import asyncio
import os
import json
import re
import time
from glob import glob
from typing import List, Optional, Dict, Any, Tuple, Union
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def cleanup_worker_files(prefix: str) -> None:
    pattern = os.path.join(DATA_DIR, f"{prefix}.worker_*.json")
    for path in glob(pattern):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Warning: failed to remove worker file {path}: {e}")

MOSAIC_USERNAME = os.getenv("MOSAIC_USERNAME")
MOSAIC_PASSWORD = os.getenv("MOSAIC_PASSWORD")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"


def _env_truthy(value: Optional[str]) -> bool:
    if value is None or not value.strip():
        return False
    return value.strip().lower() in ("1", "true", "yes", "debug", "on")


def format_wall_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(round(seconds)), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


# Verbose timestamps + cleanup/combo traces (matches previous console behavior).
SCRAPE_SCHEDULE_DEBUG = _env_truthy(os.getenv("SCRAPE_SCHEDULE_DEBUG")) or _env_truthy(
    os.getenv("DEBUG")
)

COURSE_LIMIT: Optional[int] = None  # None => scrape all courses
WORKER_COUNT = 30
TERM_NAME = "2026 Spring/Summer"


class ActionTimer:
    def __init__(self) -> None:
        self.start = time.time()

    def log(self, message: str) -> None:
        if not SCRAPE_SCHEDULE_DEBUG:
            return
        elapsed = time.time() - self.start
        print(f"[{elapsed:6.2f}s  ] {message}")
        self.start = time.time()


timer = ActionTimer()

UI_SETTLE_SECONDS = 1.0 - 0.65
COURSE_COOLDOWN_SECONDS = 3.0 - 2
RESULT_NAV_COOLDOWN_SECONDS = 1.0 - 0.65

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_PATTERN = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
TIME_RANGE_PATTERN = r"(\d{1,2}:\d{2}\s+[AP]M)\s+to\s+(\d{1,2}:\d{2}\s+[AP]M)"


def normalize_course_code(value: Optional[str]) -> str :
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def load_course_codes(
    path: Optional[str] = None, limit: Optional[int] = COURSE_LIMIT
) -> List[str]:
    path = path or os.path.join(DATA_DIR, "all_courses.json")
    with open(path) as f:
        courses = json.load(f)

    course_codes: List[str] = []
    for course in courses:
        course_name: str = course.get("course_name", "")
        course_code = course_name.split(" - ", 1)[0].strip()
        if not course_code:
            continue

        course_codes.append(course_code)

        if limit is not None and len(course_codes) >= limit:
            break

    return course_codes


def chunk_list(items: List[Any], chunk_count: int) -> List[List[Any]]:
    return [items[i::chunk_count] for i in range(chunk_count)]


async def selected_course_labels(page: Page) -> List[str]:
    return await page.evaluate(
        """() => Array.from(
            document.querySelectorAll("input.ignore_check[id^='cnf_toggle']:checked")
        ).map((box) => box.getAttribute("aria-label") || "")"""
    )


async def wait_for_selected_course_labels(
    page: Page, course_code: str, timeout_ms: int = 15000
) -> List[str]:
    """
    Wait until the course checkbox for `course_code` is actually checked.
    Returns the checked aria-labels list (may be empty if timed out).
    """
    normalized_target = normalize_course_code(course_code)
    if not normalized_target:
        return []

    # Wait until *any* cnf_toggle checkbox becomes checked, then verify it matches.
    try:
        await page.wait_for_function(
            """(targetNorm) => {
                const boxes = Array.from(
                    document.querySelectorAll("input.ignore_check[id^='cnf_toggle']:checked")
                );
                if (boxes.length === 0) return false;
                const norm = (v) => (v || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
                return boxes.some((b) => norm(b.getAttribute('aria-label')).startsWith(targetNorm));
            }""",
            normalized_target,
            timeout=timeout_ms,
        )
    except Exception:
        # Timed out: fall through to read whatever is currently checked.
        pass

    return await selected_course_labels(page)


def normalize_term_label(term_text: str) -> str:
    """
    Convert labels like "2025 Fall" or "Fall 2025" into "Fall 2025".
    """
    cleaned = re.sub(r"\s+", " ", (term_text or "").strip())
    match_year_first = re.match(r"^(\d{4})\s+([A-Za-z/]+)$", cleaned)
    if match_year_first:
        return f"{match_year_first.group(2)} {match_year_first.group(1)}"
    return cleaned


async def get_other_term_availability(page: Page, course_code: str) -> Optional[str]:
    """
    Detect MyTimetable message like:
      "<COURSE> is only available in the term 2025 Fall."
    Returns the normalized term label (e.g. "Fall 2025") when found.
    """
    normalized_target = normalize_course_code(course_code)
    if not normalized_target:
        return None

    body_text: str = await page.evaluate("() => document.body.innerText || ''")
    if not body_text:
        return None

    # Look for explicit "only available ... term X" lines and ensure they refer to this course.
    for raw_line in body_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if "is only available" not in line.lower():
            continue
        if normalized_target not in normalize_course_code(line):
            continue

        term_match = re.search(r"\bterm\s+([A-Za-z0-9/ ]+?)(?:[.!]|$)", line, flags=re.IGNORECASE)
        if term_match:
            return normalize_term_label(term_match.group(1))

        # Fallback when "term" isn't present but an academic term label is.
        fallback_match = re.search(
            r"\b((?:20\d{2}\s+[A-Za-z/]+)|(?:[A-Za-z/]+\s+20\d{2}))\b",
            line,
            flags=re.IGNORECASE,
        )
        if fallback_match:
            return normalize_term_label(fallback_match.group(1))

        return "Unknown"

    return None


async def _read_result_index(page: Page) -> Optional[int]:
    """Return current result index from the pagination UI, or None if unavailable."""
    current_span = page.locator(".results-current-schedule").first
    try:
        await current_span.wait_for(state="visible", timeout=2000)
        txt = (await current_span.inner_text()).strip()
        match = re.search(r"\d+", txt)
        return int(match.group(0)) if match else None
    except Exception:
        return None


async def rewind_to_first_result(page: Page, max_steps: int = 200) -> bool:
    """
    Click "previous" until the current result index reaches 1.
    Returns True when already at / successfully reached 1.
    """
    # If we aren't on a results view, rewinding can't work.
    current_span = page.locator(".results-current-schedule").first
    try:
        if await current_span.count() == 0:
            return False
        if not await current_span.is_visible():
            return False
    except Exception:
        return False

    prev_btn = page.locator(".results-action-previous").first
    try:
        if await prev_btn.count() == 0:
            return False
    except Exception:
        return False

    for _ in range(max_steps):
        current_idx = await _read_result_index(page)
        if current_idx is None:
            return False
        if current_idx <= 1:
            timer.log("Result index reset to 1")
            return True

        try:
            await prev_btn.click()
        except Exception:
            return False
        await asyncio.sleep(RESULT_NAV_COOLDOWN_SECONDS)

        # Wait until result index updates after the click.
        for _ in range(20):
            await asyncio.sleep(0.1)
            next_idx = await _read_result_index(page)
            if next_idx is not None and next_idx < current_idx:
                break

    timer.log("Warning: could not fully rewind to result 1")
    return False


async def remove_selected_course(page: Page, course_code: Optional[str] = None) -> None:
    timer.log("Attempting course cleanup...")

    try:
        await rewind_to_first_result(page)
    except Exception:
        pass

    trash_button = page.locator(".cnf_trash_button:visible").first

    if await trash_button.count() == 0:
        timer.log("No course button found to remove (already clean)")
        return
    await trash_button.scroll_into_view_if_needed()
    await trash_button.dispatch_event("click", {"bubbles": True})

    timer.log(f"Removed Course: {course_code} from Results")

    await asyncio.sleep(0.5)
    timer.log("Cleanup complete")

def parse_section_details(raw_text: str) -> Dict[str, str]:
    # Instruction Mode
    mode = "Unknown"
    if "In Person" in raw_text:
        mode = "In Person"
    elif "Online" in raw_text:
        mode = "Online"
    elif "Blended" in raw_text:
        mode = "Blended"

    # Professor
    prof = "Staff"
    prof_match = re.search(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\s+\d\.\d/\d\.\d\sUnits", raw_text
    )
    if prof_match:
        prof = prof_match.group(1)
    elif "Linda Davis" in raw_text:
        prof = "Linda Davis"
    elif "Staff" in raw_text:
        prof = "Staff"

    # Building/Room
    building = "TBD"
    bldg_match = re.search(
        r"([A-Z][a-z\s]+-\s[A-Z0-9_]+LAB|[A-Z][a-z\s]+-\s[A-Z0-9_]+)", raw_text
    )
    if bldg_match:
        building = bldg_match.group(1).strip()

    return {"instructor": prof, "location": building, "mode": mode}


def parse_schedule_segments(raw_text: str) -> List[Dict[str, Any]]:
    """Parse MyTimetable time text into day/time segments before expanding by day."""
    segments: List[Dict[str, Any]] = []
    clean_text = re.sub(r"<br\s*/?>", "\n", raw_text or "", flags=re.IGNORECASE)

    for line in [
        re.sub(r"\s+", " ", part).strip()
        for part in clean_text.splitlines()
        if part.strip()
    ]:
        previous_end = 0
        for match in re.finditer(TIME_RANGE_PATTERN, line):
            prefix = line[previous_end : match.start()]
            days = re.findall(DAY_PATTERN, prefix)
            if not days and previous_end == 0:
                days = re.findall(DAY_PATTERN, line[: match.start()])
            if not days:
                previous_end = match.end()
                continue

            segments.append(
                {
                    "days": days,
                    "start": match.group(1),
                    "end": match.group(2),
                }
            )
            previous_end = match.end()

    return segments


def expand_schedule_blocks(
    segments: List[Dict[str, Any]], section_blocks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Expand parsed time segments into per-day blocks with LEC/LAB/TUT labels."""
    expanded: List[Dict[str, Any]] = []

    for segment_idx, segment in enumerate(segments):
        section = (
            section_blocks[min(segment_idx, len(section_blocks) - 1)]
            if section_blocks
            else {}
        )
        section_label: str = section.get("section", "Unknown")
        component = (
            section_label.split()[0] if section_label != "Unknown" else "Unknown"
        )

        for day in segment["days"]:
            expanded.append(
                {
                    "day": day,
                    "start": segment["start"],
                    "end": segment["end"],
                    "type": component,
                    "section": section_label,
                }
            )

    return expanded


async def scrape_course_combinations(
    page: Page, course_code: str
) -> Optional[Dict[str, Any]]:
    timer.log(f"--- Processing Course: {course_code} ---")
    course_selected = False
    course_data: Optional[Dict[str, Any]] = None

    # Defensive cleanup: if a previous course is still selected, remove it first.
    await remove_selected_course(page)
    await asyncio.sleep(UI_SETTLE_SECONDS)

    try:
        # 1. Search and Select
        normalized_target_code = normalize_course_code(course_code)
        search_box = page.locator("#code_number")
        await search_box.click()
        await search_box.fill("")
        await search_box.type(course_code, delay=20)

        suggestion_items = page.locator("#suggestion_box a, #suggestion_container a")
        target = None
        for _ in range(20):
            try:
                await suggestion_items.first.wait_for(state="visible", timeout=1000)
            except Exception:
                await asyncio.sleep(0.25)
                continue

            count = await suggestion_items.count()
            exact_match = None
            prefix_match = None
            for i in range(count):
                s = suggestion_items.nth(i)
                if not await s.is_visible():
                    continue
                txt = (await s.inner_text()).upper().replace("\n", " ")
                norm = normalize_course_code(txt)
                if norm == normalized_target_code:
                    exact_match = s
                    break
                if prefix_match is None and norm.startswith(normalized_target_code):
                    prefix_match = s

            target = exact_match or prefix_match
            if target:
                break
            await asyncio.sleep(0.25)

        if not target:
            timer.log(
                f"No exact suggestion found for {course_code}; skipping to avoid wrong course selection."
            )
            return None

        await target.click()
        course_selected = True
        timer.log("Selected suggestion")
        await asyncio.sleep(COURSE_COOLDOWN_SECONDS)

        other_term = await get_other_term_availability(page, course_code)
        if other_term:
            timer.log(f"{course_code} is only available in {other_term}; recording term.")
            course_selected = False
            return {
                "course_code": course_code,
                "term": other_term,
                "combinations": [],
            }

        selected_labels = await wait_for_selected_course_labels(page, course_code)
        if not any(
            normalize_course_code(label).startswith(normalized_target_code)
            for label in selected_labels
        ):
            timer.log(
                f"Selected course mismatch for {course_code}. Selected: {selected_labels}"
            )
            await remove_selected_course(page)
            course_selected = False
            return None

        # 2. View Schedules (if prompt appears)
        view_btn = page.locator(".welcome-search-continue")
        try:
            if await view_btn.is_visible():
                await view_btn.click()
                timer.log("Clicked 'View Schedules'")
                await asyncio.sleep(COURSE_COOLDOWN_SECONDS)
        except Exception:
            pass

        other_term = await get_other_term_availability(page, course_code)
        if other_term:
            timer.log(f"{course_code} is only available in {other_term}; recording term.")
            course_selected = False
            return {
                "course_code": course_code,
                "term": other_term,
                "combinations": [],
            }

        # 3. Wait for Results and determining total combinations
        total_span = page.locator(".results-nav .results-total-schedules").first
        try:
            await total_span.wait_for(state="visible", timeout=15000)
            total_text = await total_span.inner_text()
            total_combos = int(total_text.strip())
            timer.log(f"Found {total_combos} combinations")
        except Exception as e:
            timer.log(f"Could not determine total combinations: {e}")
            return None

        course_data = {"course_code": course_code, "term": TERM_NAME, "combinations": []}

        # 4. Cycle and Extract
        next_btn = page.locator(".results-action-next").first

        for i in range(1, total_combos + 1):
            await asyncio.sleep(UI_SETTLE_SECONDS)
            legend_block = page.locator(".course_cell_legend").filter(
                has_text=course_code
            )

            try:
                # Sections details (Instructor, Room, etc.)
                section_blocks: List[Dict[str, Any]] = []
                type_blocks = legend_block.locator(".selection_table .type_block")
                row_count = await type_blocks.count()
                for j in range(row_count):
                    type_block = type_blocks.nth(j)
                    section_label = (await type_block.inner_text()).strip()
                    section_row = type_block.locator("xpath=ancestor::tr[1]")
                    row_txt = await section_row.inner_text()
                    parsed = parse_section_details(" ".join(row_txt.split()))

                    type_match = re.search(r"(LEC|LAB|TUT)\s+[A-Z0-9]+", section_label)
                    section_label = (
                        type_match.group(0)
                        if type_match
                        else section_label or f"Section {j+1}"
                    )

                    section_blocks.append({"section": section_label, **parsed})

                # Prefer the visible hours text; it preserves multi-day blocks better than the h4 aria-label.
                hours_text = ""
                try:
                    hours_text = await legend_block.locator(
                        "#hoursInLegend"
                    ).inner_text()
                except Exception:
                    pass

                if not hours_text:
                    header_aria = await legend_block.locator(
                        "h4.course_title"
                    ).get_attribute("aria-label")
                    hours_text = header_aria or ""

                schedule_segments = parse_schedule_segments(hours_text)
                day_blocks = expand_schedule_blocks(schedule_segments, section_blocks)

                course_data["combinations"].append(
                    {
                        "index": i,
                        "schedule_blocks": day_blocks,
                        "sections": section_blocks,
                    }
                )
                if SCRAPE_SCHEDULE_DEBUG:
                    print(f"  Captured combo {i}/{total_combos}", end="\r")
            except Exception as e:
                if SCRAPE_SCHEDULE_DEBUG:
                    print(f"\n  Failed combo {i}: {e}")
                else:
                    print(f"[course {course_code}] combo {i}/{total_combos}: {e}")

            if i < total_combos:
                await next_btn.click()
                await asyncio.sleep(RESULT_NAV_COOLDOWN_SECONDS)

        if SCRAPE_SCHEDULE_DEBUG:
            print(
                f"\nCaptured {len(course_data['combinations'])} combinations for {course_code}."
            )
        return course_data
    finally:
        if course_selected:
            await remove_selected_course(page, course_code=course_code)
            await asyncio.sleep(COURSE_COOLDOWN_SECONDS)


async def setup_timetable_page(
    browser: Browser, worker_id: int
) -> Tuple[BrowserContext, Page]:
    context = await browser.new_context()
    page = await context.new_page()

    timer.log(f"[worker {worker_id}] Logging in...")
    await page.goto("https://mytimetable.mcmaster.ca/login.jsp")
    await page.fill("#word1", MOSAIC_USERNAME or "")
    await page.fill("#word2", MOSAIC_PASSWORD or "")
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")

    timer.log(f"[worker {worker_id}] Opening MyTimetable...")

    timer.log(f"[worker {worker_id}] Selecting Term...")
    term = page.locator(f".term-card-title:has-text('{TERM_NAME}')")
    if await term.count() > 0:
        await term.click()
    else:
        await page.click(f"a:has-text('{TERM_NAME}')")

    await page.wait_for_selector("#code_number", timeout=30000)
    timer.log(f"[worker {worker_id}] Ready")
    return context, page


async def scrape_course_chunk(
    browser: Browser, worker_id: int, course_codes: List[str]
) -> List[Dict[str, Any]]:
    context: Optional[BrowserContext] = None
    partial_path = os.path.join(
        DATA_DIR, f"all_possible_schedules.worker_{worker_id}.json"
    )
    results: List[Dict[str, Any]] = []

    try:
        context, page = await setup_timetable_page(browser, worker_id)

        for idx, code in enumerate(course_codes, start=1):
            timer.log(f"[worker {worker_id}] Course {idx}/{len(course_codes)}: {code}")
            try:
                result = await scrape_course_combinations(page, code)
                if result:
                    results.append(result)
                    with open(partial_path, "w") as f:
                        json.dump(results, f, indent=2)
                    if not SCRAPE_SCHEDULE_DEBUG:
                        print(f"[worker {worker_id}] {code}")
            except Exception as e:
                if SCRAPE_SCHEDULE_DEBUG:
                    timer.log(f"[worker {worker_id}] Error scraping {code}: {e}")
                else:
                    print(f"[worker {worker_id}] Error scraping {code}: {e}")
            finally:
                timer.log(
                    f"[worker {worker_id}] Cooling down before next course ({COURSE_COOLDOWN_SECONDS}s)..."
                )
                await asyncio.sleep(COURSE_COOLDOWN_SECONDS)

        with open(partial_path, "w") as f:
            json.dump(results, f, indent=2)

        timer.log(f"[worker {worker_id}] Finished {len(results)} scraped courses.")
        return results
    finally:
        if context:
            await context.close()


async def run() -> None:
    run_started = time.time()
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        course_codes = load_course_codes(limit=COURSE_LIMIT)
        # course_codes = ["CHEM 1AA3"]
        chunks = [chunk for chunk in chunk_list(course_codes, WORKER_COUNT) if chunk]
        timer.log(f"Loaded {len(course_codes)} courses; starting {len(chunks)} workers.")
        if not SCRAPE_SCHEDULE_DEBUG:
            print(
                f"Scrape schedules: {len(course_codes)} courses, {len(chunks)} workers "
                f"(set SCRAPE_SCHEDULE_DEBUG=1 or DEBUG=1 for full logs)"
            )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            try:
                tasks = []
                for worker_id, chunk in enumerate(chunks, start=1):
                    tasks.append(
                        asyncio.create_task(
                            scrape_course_chunk(browser, worker_id, chunk)
                        )
                    )
                    # Small stagger avoids hammering Mosaic login at the exact same millisecond.
                    await asyncio.sleep(1)

                worker_results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results: List[Dict[str, Any]] = []
                for worker_id, chunk_results in enumerate(worker_results, start=1):
                    if isinstance(chunk_results, Exception):
                        if SCRAPE_SCHEDULE_DEBUG:
                            timer.log(f"[worker {worker_id}] Failed: {chunk_results}")
                        else:
                            print(f"[worker {worker_id}] Failed: {chunk_results}")
                        continue
                    if not isinstance(chunk_results, list):
                        if SCRAPE_SCHEDULE_DEBUG:
                            timer.log(
                                f"[worker {worker_id}] Unexpected worker result type: {type(chunk_results)}"
                            )
                        else:
                            print(
                                f"[worker {worker_id}] Unexpected worker result type: {type(chunk_results)}"
                            )
                        continue
                    all_results.extend(chunk_results)

                output_path = os.path.join(DATA_DIR, "all_possible_schedules.json")
                with open(output_path, "w") as f:
                    json.dump(all_results, f, indent=2)
                cleanup_worker_files("all_possible_schedules")

                timer.log(f"All tasks done. Saved {len(all_results)} courses.")
                if not SCRAPE_SCHEDULE_DEBUG:
                    print(f"Done. Saved {len(all_results)} courses to {output_path}")
            finally:
                await browser.close()
    finally:
        elapsed = time.time() - run_started
        total_msg = f"Total time: {format_wall_time(elapsed)}"
        if SCRAPE_SCHEDULE_DEBUG:
            timer.log(total_msg)
        else:
            print(total_msg)


if __name__ == "__main__":
    asyncio.run(run())
