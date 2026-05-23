import asyncio
import json
import re
from playwright.async_api import async_playwright

# Limit concurrent requests
MAX_CONCURRENT_REQUESTS = 10
LEVEL_HEADER_PATTERN = re.compile(r"^Level\s+([IVXLC]+)\s*:\s*(\d+)\s+Units?$", re.IGNORECASE)
PROGRAM_TOTAL_PATTERN = re.compile(
    r"^(\d+)\s+units?\s+total\b.*\bLevels?\s+([IVXLC]+)\s+to\s+([IVXLC]+)\b",
    re.IGNORECASE,
)
UNITS_HEADER_PATTERN = re.compile(
    r"^(?:component\s+[a-z0-9]+\s*-\s*)?(\d+(?:\s*-\s*\d+)?)\s+units?\b(.*)$",
    re.IGNORECASE,
)
COURSE_LINE_PATTERN = re.compile(r"\b([A-Z]{2,10}\s\d[A-Z0-9]{3})\b")
LEVEL_ONLY_PATTERN = re.compile(r"^Level\s+[IVXLC]+\b", re.IGNORECASE)
STRUCTURAL_LINE_PATTERN = re.compile(
    r"^(from|or|electives|course list|as outlined below:?|fall and winter term|spring/summer term)$",
    re.IGNORECASE,
)


def roman_to_int(roman):
    if not roman:
        return None
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
    total = 0
    prev = 0
    for char in reversed(roman.upper()):
        value = values.get(char)
        if value is None:
            return None
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total


def extract_course_code(text):
    if not text:
        return None
    match = COURSE_LINE_PATTERN.search(text)
    if not match:
        return None
    return match.group(1)


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

    def add_text_hint_requirement(unit_group):
        hints = [
            hint
            for hint in unit_group.get("_text_hints", [])
            if not STRUCTURAL_LINE_PATTERN.match(hint)
        ]
        if not hints:
            return

        text = " ".join(hints).strip()
        if text:
            unit_group["requirements"].append(
                {"type": "text", "text": text, "course_code": None}
            )

    for line in lines:
        level_match = LEVEL_HEADER_PATTERN.match(line)
        if level_match:
            level_roman = level_match.group(1).upper()
            current_level = {
                "level": level_roman,
                "level_roman": level_roman,
                "level_number": roman_to_int(level_roman),
                "total_units": int(level_match.group(2)),
                "unit_groups": [],
            }
            grouped.append(current_level)
            current_group = None
            continue

        program_total_match = PROGRAM_TOTAL_PATTERN.match(line)
        if program_total_match and current_level is None:
            start_roman = program_total_match.group(2).upper()
            end_roman = program_total_match.group(3).upper()
            level_roman = f"{start_roman}-{end_roman}"
            current_level = {
                "level": level_roman,
                "level_roman": level_roman,
                "level_number": None,
                "total_units": int(program_total_match.group(1)),
                "unit_groups": [],
            }
            grouped.append(current_level)
            current_group = None
            continue

        units_match = UNITS_HEADER_PATTERN.match(line)
        if units_match and current_level:
            units_value = re.sub(r"\s+", "", units_match.group(1))
            suffix = (units_match.group(2) or "").strip().lower()
            current_group = {
                "units": units_value,
                "choose_one": "from" in suffix,
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
                "choose_one": False,
                "requirements": [],
                "_text_hints": [],
            }
            current_level["unit_groups"].append(current_group)

        if STRUCTURAL_LINE_PATTERN.match(line):
            if line.lower() == "from":
                current_group["choose_one"] = True
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

        if course_code not in flat_seen:
            flat_seen.add(course_code)
            flat_course_requirements.append(course_code)

    for level_data in grouped:
        for unit_group in level_data.get("unit_groups", []):
            requirements = unit_group.get("requirements", [])
            if not requirements:
                add_text_hint_requirement(unit_group)
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
                fallback_codes = []
                seen = set()
                for line in fallback_courses:
                    course_code = extract_course_code(line)
                    if not course_code or course_code in seen:
                        continue
                    seen.add(course_code)
                    fallback_codes.append(course_code)
                course_requirements = fallback_codes

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
        url = (
            "https://academiccalendars.romcmaster.ca/content.php?catoid=65&navoid=14803"
        )
        print(f"Navigating to programs list: {url}")
        await main_page.goto(url, wait_until="networkidle")

        # Extract all program links
        programs = await main_page.evaluate("""
            () => {
                const container = document.querySelector("td.block_content") || document.body;
                const results = [];
                const seen = new Set();
                let currentSection = "";

                for (const child of Array.from(container.children)) {
                    const heading = child.querySelector("strong");
                    if (heading && heading.innerText) {
                        currentSection = heading.innerText.trim();
                    }

                    if (!child.matches("ul.program-list")) {
                        continue;
                    }

                    if (!/bachelor/i.test(currentSection)) {
                        continue;
                    }

                    for (const a of Array.from(child.querySelectorAll("a[href*='preview_program.php']"))) {
                        const name = (a.innerText || "").trim();
                        const url = a.href;
                        if (!name || !url || seen.has(url)) {
                            continue;
                        }
                        seen.add(url);
                        results.push({ name, url });
                    }
                }

                return results;
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
