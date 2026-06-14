import asyncio
import json
import os
import re
from typing import Any, Dict, List, Optional
from glob import glob
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright

# Limit concurrent requests to avoid overwhelming the server
MAX_CONCURRENT_REQUESTS = 10
TOTAL_PAGES = 34
HEADLESS = True
PAGE_NAV_CONCURRENCY = 8

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def cleanup_worker_files(prefix: str) -> None:
    pattern = os.path.join(DATA_DIR, f"{prefix}.worker_*.json")
    for path in glob(pattern):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Warning: failed to remove worker file {path}: {e}")

async def fetch_and_parse_course(
    context, base_url: str, item: Dict[str, str], semaphore: asyncio.Semaphore
) -> Optional[Dict[str, Any]]:
    async with semaphore:
        coid = item['coid']
        try:
            response = await context.request.get(base_url + coid, ignore_https_errors=True)
            if response.status != 200:
                return None
                
            html_content = await response.text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Parse Name and Units
            course_name = ""
            h3 = soup.find("h3")
            if h3:
                course_name = h3.get_text(strip=True)
            else:
                course_name = item['text']

            units = ""
            unit_match = re.search(r"(\d+)\s*unit\(s\)", soup.get_text())
            if unit_match:
                units = unit_match.group(0)

            description = ""
            prerequisites = []
            recommended = ""
            restrictions = ""

            # Helper: find a tag by name list and text match
            def find_label_tag(soup, label):
                """Find a <strong> or <b> tag whose text contains the given label."""
                for tag_name in ["strong", "b"]:
                    tag = soup.find(tag_name, string=lambda t: t and label in t)
                    if tag:
                        return tag
                    # Fallback: check .text in case string matching fails
                    tag = soup.find(lambda t: t.name == tag_name and label in t.get_text())
                    if tag:
                        return tag
                return None

            def extract_text_after_tag(tag):
                """Collect text content after a label tag until the next <br>, <hr>, or label tag."""
                parts = []
                curr = tag.next_sibling
                while curr:
                    if hasattr(curr, 'name') and curr.name in ['br', 'hr']:
                        break
                    if hasattr(curr, 'name') and curr.name in ['strong', 'b']:
                        break
                    parts.append(str(curr))
                    curr = curr.next_sibling
                html = "".join(parts)
                return BeautifulSoup(f"<span>{html}</span>", "html.parser").get_text().strip().lstrip(":").strip()

            # 1. Prerequisite extraction
            prereq_tag = find_label_tag(soup, "Prerequisite")
            if prereq_tag:
                clean_p_text = extract_text_after_tag(prereq_tag)
                prerequisites = [x.strip().strip(".") for x in clean_p_text.split(",") if x.strip()]

            # 2. Antirequisite / Restriction extraction (directly from HTML tags)
            restriction_parts = []

            # Find explicit Antirequisite(s): tag
            antireq_tag = find_label_tag(soup, "Antirequisite")
            if antireq_tag:
                antireq_text = extract_text_after_tag(antireq_tag)
                if antireq_text:
                    restriction_parts.append(f"Antirequisite(s): {antireq_text}")

            # 3. Description extraction
            hr = soup.find("hr")
            if hr:
                # Collect text from <hr> until the first label tag (Prerequisite, Antirequisite, etc.)
                desc_parts = []
                curr = hr.next_sibling
                while curr:
                    # Stop at prerequisite, antirequisite, or any bold label tag
                    if curr == prereq_tag or curr == antireq_tag:
                        break
                    if hasattr(curr, 'name') and curr.name in ['strong', 'b']:
                        tag_text = curr.get_text()
                        if any(kw in tag_text for kw in ["Prerequisite", "Antirequisite", "Co-requisite"]):
                            break
                    desc_parts.append(str(curr))
                    curr = curr.next_sibling
                
                raw_desc = "".join(desc_parts).strip()
                full_text = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()
                full_text = re.sub(r'\s+', ' ', full_text)

                # Also scan the full page text for "Not open to students" restrictions
                page_text = soup.get_text(separator=" ")
                page_text = re.sub(r'\s+', ' ', page_text)
                not_open_pattern = r"(Not open to students.*?\.)"
                not_open_matches = re.findall(not_open_pattern, page_text, re.IGNORECASE)
                for match in not_open_matches:
                    clean_match = match.strip()
                    if clean_match and clean_match not in restriction_parts:
                        restriction_parts.append(clean_match)
                        full_text = full_text.replace(clean_match, "")

                restrictions = "\n".join(restriction_parts)

                # Extract Recommended
                rec_pattern = r"([^.]*?\b(?:is|are|is strongly)\s+recommended\.)"
                rec_match = re.search(rec_pattern, full_text, re.IGNORECASE)
                if rec_match:
                    recommended = rec_match.group(0).strip()
                    full_text = full_text.replace(recommended, "")

                # Filter out Lectures boilerplate
                lecture_pattern = r"Lectures\s*\(.*?\)\s*;\s*.*?(?:\.|$)"
                full_text = re.sub(lecture_pattern, "", full_text, flags=re.IGNORECASE)
                
                # Cleanup leftover Cross-list info if it's dangling
                full_text = re.sub(r"Cross-list\(s\):.*", "", full_text, flags=re.IGNORECASE).strip()

                description = full_text.strip()

            return {
                "course_name": course_name,
                "units": units,
                "description": description,
                "prerequisites": prerequisites,
                "recommended": recommended,
                "restrictions": restrictions
            }
        except Exception as e:
            print(f"\n[Error] Failed {item['text']}: {e}")
            return None

def extract_course_code(course_text: str) -> str:
    text = (course_text or "").strip()
    match = re.match(r"^[A-Za-z]{2,}\s*\d+[A-Za-z0-9]*", text)
    if match:
        return match.group(0).upper().replace("  ", " ")
    return text.split(" - ", 1)[0].upper() if text else ""


def build_page_url(catoid: str, navoid: str, page_num: int) -> str:
    return (
        "https://academiccalendars.romcmaster.ca/content.php"
        f"?catoid={catoid}"
        f"&navoid={navoid}"
        "&filter%5Bitem_type%5D=3"
        "&filter%5Bonly_active%5D=1"
        "&filter%5B3%5D=1"
        f"&filter%5Bcpage%5D={page_num}"
        "#acalog_template_course_filter"
    )


async def read_course_links(page: Page) -> List[Dict[str, str]]:
    return await page.evaluate(
        """
        () => Array.from(document.querySelectorAll("a[onclick^='showCourse']")).map(a => {
            const match = a.getAttribute('onclick').match(/showCourse\\('(\\d+)',\\s*'(\\d+)'/);
            return {
                text: a.innerText.trim(),
                coid: match ? match[2] : null
            };
        }).filter(item => item.coid !== null)
        """
    )


def parse_course_links_from_html(html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[Dict[str, str]] = []
    for a in soup.select("a[onclick^='showCourse']"):
        onclick = a.get("onclick", "")
        match = re.search(r"showCourse\('(\d+)',\s*'(\d+)'", onclick)
        if not match:
            continue
        links.append({"text": a.get_text(strip=True), "coid": match.group(2)})
    return links


async def read_course_links_via_request(context, target_url: str) -> List[Dict[str, str]]:
    response = await context.request.get(target_url, ignore_https_errors=True)
    if response.status != 200:
        return []
    html = await response.text()
    return parse_course_links_from_html(html)


async def scrape_course_page(
    browser: Browser,
    worker_id: int,
    page_num: int,
    catoid: str,
    navoid: str,
    base_preview_url: str,
    request_semaphore: asyncio.Semaphore,
    page_nav_semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    async with page_nav_semaphore:
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        partial_path = os.path.join(DATA_DIR, f"all_courses.worker_{worker_id}.json")

        try:
            target_url = build_page_url(catoid, navoid, page_num)
            print(f"[worker {worker_id}] Navigating directly to page {page_num}...")
            await page.goto(target_url, wait_until="networkidle")

            print(f"\n--- [worker {worker_id}] Processing Page {page_num} ---")
            course_links: List[Dict[str, str]] = []
            for attempt in range(1, 4):
                try:
                    await page.wait_for_selector(
                        "a[onclick^='showCourse']", timeout=12000
                    )
                    course_links = await read_course_links(page)
                except Exception:
                    course_links = []

                if course_links:
                    break

                print(
                    f"[worker {worker_id}] Page {page_num} had 0 DOM links "
                    f"(attempt {attempt}/3). Retrying..."
                )
                await asyncio.sleep(1.0)
                await page.reload(wait_until="networkidle")

            if not course_links:
                # Fallback to static HTML parse; this avoids intermittent DOM timing issues.
                course_links = await read_course_links_via_request(context, target_url)
                if course_links:
                    print(
                        f"[worker {worker_id}] Page {page_num} recovered via request fallback "
                        f"({len(course_links)} links)."
                    )
                else:
                    print(
                        f"[worker {worker_id}] Page {page_num} still has 0 course links after retries."
                    )

            page_course_codes = [extract_course_code(item.get("text", "")) for item in course_links]
            page_course_codes = [code for code in page_course_codes if code]
            first_code = page_course_codes[0] if page_course_codes else "N/A"
            last_code = page_course_codes[-1] if page_course_codes else "N/A"
            print(
                f"[worker {worker_id}] Page {page_num} course range: "
                f"first={first_code}, last={last_code}, count={len(course_links)}"
            )

            tasks = [
                fetch_and_parse_course(context, base_preview_url, item, request_semaphore)
                for item in course_links
            ]
            page_results = await asyncio.gather(*tasks)
            valid_results = [r for r in page_results if r is not None]
            with open(partial_path, "w") as f:
                json.dump(valid_results, f, indent=2)
            print(f"[worker {worker_id}] Finished page {page_num} ({len(valid_results)} courses).")
            return valid_results
        except Exception as e:
            print(f"[worker {worker_id}] Error on page {page_num}: {e}")
            with open(partial_path, "w") as f:
                json.dump([], f, indent=2)
            return []
        finally:
            await context.close()


async def scrape_courses():
    os.makedirs(DATA_DIR, exist_ok=True)

    catoid = "65"
    navoid = "14802"
    base_preview_url = (
        f"https://academiccalendars.romcmaster.ca/ajax/preview_course.php?catoid={catoid}&show&coid="
    )
    page_numbers = list(range(1, TOTAL_PAGES + 1))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        page_nav_semaphore = asyncio.Semaphore(PAGE_NAV_CONCURRENCY)
        print(
            f"Starting page workers: {len(page_numbers)} "
            f"(1 worker per page, global request concurrency={MAX_CONCURRENT_REQUESTS})"
        )

        try:
            tasks = []
            for worker_id, page_num in enumerate(page_numbers, start=1):
                tasks.append(
                    asyncio.create_task(
                        scrape_course_page(
                            browser,
                            worker_id,
                            page_num,
                            catoid,
                            navoid,
                            base_preview_url,
                            request_semaphore,
                            page_nav_semaphore,
                        )
                    )
                )
                await asyncio.sleep(0.05)

            worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            await browser.close()

    scraped_data: List[Dict[str, Any]] = []
    for worker_id, result in enumerate(worker_results, start=1):
        if isinstance(result, Exception):
            print(f"[worker {worker_id}] Failed: {result}")
            continue
        scraped_data.extend(result)

    deduped_by_name: Dict[str, Dict[str, Any]] = {}
    duplicate_count = 0
    for item in scraped_data:
        key = (item.get("course_name") or "").strip()
        if key in deduped_by_name:
            duplicate_count += 1
            continue
        deduped_by_name[key] = item

    final_results = list(deduped_by_name.values())
    output_file = os.path.join(DATA_DIR, "all_courses.json")
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)
    cleanup_worker_files("all_courses")

    print(
        f"\nSuccess! Scraped {len(final_results)} unique courses "
        f"(filtered {duplicate_count} duplicates)."
    )
    print(f"Data saved to {output_file}")
    return final_results

if __name__ == "__main__":
    asyncio.run(scrape_courses())
