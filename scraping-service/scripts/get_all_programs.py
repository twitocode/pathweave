import asyncio
import json
import re
from playwright.async_api import async_playwright

# Limit concurrent requests
MAX_CONCURRENT_REQUESTS = 10
LEVEL_HEADER_PATTERN = re.compile(r"^Level\s+([IVXLC]+)\s*:\s*(\d+)\s+Units?$", re.IGNORECASE)
UNITS_HEADER_PATTERN = re.compile(r"^(\d+)\s+units?$", re.IGNORECASE)
COURSE_LINE_PATTERN = re.compile(r"\b([A-Z]{2,10}\s\d[A-Z0-9]{3})\b")
LEVEL_ONLY_PATTERN = re.compile(r"^Level\s+[IVXLC]+\b", re.IGNORECASE)
STRUCTURAL_LINE_PATTERN = re.compile(
    r"^(from|or|electives|course list|as outlined below:?|fall and winter term|spring/summer term)$",
    re.IGNORECASE,
)


def _clean_line(line):
    line = re.sub(r"\s+", " ", line).strip()
    return line


def _extract_requirements_section(raw_text):
    if not raw_text:
        return ""

    start = raw_text.find("Requirements")
    if start == -1:
        return raw_text

    section = raw_text[start:]

    # Catalog pages typically include navigation text after this marker.
    end_markers = ["Return to", "Program Academic Calendar"]
    end_positions = [section.find(marker) for marker in end_markers if section.find(marker) != -1]
    if end_positions:
        section = section[: min(end_positions)]

    return section


def parse_requirements_by_level(raw_text):
    section = _extract_requirements_section(raw_text)
    lines = [_clean_line(line) for line in section.splitlines()]
    lines = [line for line in lines if line and line.lower() != "requirements"]

    grouped = []
    flat_course_requirements = []
    flat_seen = set()
    current_level = None
    current_group = None

    for line in lines:
        level_match = LEVEL_HEADER_PATTERN.match(line)
        if level_match:
            current_level = {
                "level": level_match.group(1),
                "total_units": int(level_match.group(2)),
                "unit_groups": [],
            }
            grouped.append(current_level)
            current_group = None
            continue

        units_match = UNITS_HEADER_PATTERN.match(line)
        if units_match and current_level:
            current_group = {
                "units": int(units_match.group(1)),
                "requirements": [],
                "_text_hints": [],
            }
            current_level["unit_groups"].append(current_group)
            continue

        if not current_level:
            continue

        if LEVEL_ONLY_PATTERN.match(line):
            continue

        if current_group is None:
            current_group = {
                "units": None,
                "requirements": [],
                "_text_hints": [],
            }
            current_level["unit_groups"].append(current_group)

        if STRUCTURAL_LINE_PATTERN.match(line):
            current_group["_text_hints"].append(line)
            continue

        course_match = COURSE_LINE_PATTERN.search(line)
        if not course_match:
            current_group["_text_hints"].append(line)
            continue

        course_code = course_match.group(1)
        current_group["requirements"].append(
            {"type": "course", "text": line, "course_code": course_code}
        )

        if line not in flat_seen:
            flat_seen.add(line)
            flat_course_requirements.append(line)

    for level_data in grouped:
        for unit_group in level_data.get("unit_groups", []):
            requirements = unit_group.get("requirements", [])
            if not requirements:
                text_hints = " ".join(unit_group.get("_text_hints", [])).lower()
                if "admission" in text_hints:
                    unit_group["requirements"] = [
                        {
                            "type": "text",
                            "text": "See Admission Requirements",
                            "course_code": None,
                        }
                    ]
                continue

            has_course = any(item.get("course_code") for item in requirements)
            if has_course:
                continue

            combined_text = " ".join(item.get("text", "") for item in requirements).lower()
            if "admission" in combined_text:
                unit_group["requirements"] = [
                    {
                        "type": "text",
                        "text": "See Admission Requirements",
                        "course_code": None,
                    }
                ]

            unit_group.pop("_text_hints", None)

    for level_data in grouped:
        for unit_group in level_data.get("unit_groups", []):
            unit_group.pop("_text_hints", None)

    return grouped, flat_course_requirements

async def fetch_program_requirements(context, url, name, semaphore):
    async with semaphore:
        try:
            page = await context.new_page()
            # Navigate to the program page
            await page.goto(url, wait_until="networkidle", timeout=30000)

            requirements_text = await page.evaluate("""
                () => {
                    const container = document.querySelector("td.block_content") || document.body;
                    return container ? container.innerText : "";
                }
            """)
            requirements_by_level, parsed_courses = parse_requirements_by_level(requirements_text)

            # Fallback for pages where the requirements section does not use level/unit formatting.
            fallback_courses = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll("a[onclick^='showCourse']"));
                    return [...new Set(links.map(a => a.innerText.trim()))];
                }
            """)

            if parsed_courses:
                course_requirements = parsed_courses
            else:
                course_requirements = fallback_courses

            if not course_requirements:
                content = await page.inner_text(".block_content")
                # Pattern like 'ANTHROP 2PA3' or 'ABLD 3A03'
                pattern = r"\b[A-Z]{2,10}\s\d[A-Z0-9]{2,4}\b"
                course_requirements = sorted(set(re.findall(pattern, content)))

            await page.close()
            print(f"Scraped {name}: {len(course_requirements)} courses found.", end="\r")
            return {
                "program_name": name,
                "url": url,
                "requirements": course_requirements,
                "requirements_by_level": requirements_by_level,
            }
        except Exception as e:
            print(f"\n[Error] Failed to scrape {name}: {e}")
            return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        
        main_page = await context.new_page()
        url = "https://academiccalendars.romcmaster.ca/content.php?catoid=58&navoid=12628"
        print(f"Navigating to programs list: {url}")
        await main_page.goto(url, wait_until="networkidle")

        # Extract all program links
        programs = await main_page.evaluate("""
            () => {
                const container = document.querySelector('td.block_content') || document.body;
                return Array.from(container.querySelectorAll("a[href*='preview_program.php']")).map(a => ({
                    name: a.innerText.trim(),
                    url: a.href
                })).filter(p => p.name.length > 5);
            }
        """)
        print(f"Found {len(programs)} programs.")

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        tasks = [fetch_program_requirements(context, p_info['url'], p_info['name'], semaphore) for p_info in programs]
        
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r is not None]

        with open("data/all_programs_with_requirements.json", "w") as f:
            json.dump(valid_results, f, indent=2)

        print(f"\nSuccess! Scraped {len(valid_results)} programs.")
        print("Data saved to all_programs_with_requirements.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
