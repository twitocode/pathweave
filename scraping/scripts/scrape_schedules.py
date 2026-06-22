import argparse
import asyncio
import json
import os
import random
import re
import time
from glob import glob
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

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
            pass

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

# MyTimetable term cards identified by their data-term attribute.
# Map data-term ID -> human-readable label.
TERM_MAP = {
    # "3202620": "Spring/Summer 2026",
    "3202630": "Fall 2026",
    "3202710": "Winter 2027",
}

# Default terms to scrape (all of them). Can be overridden via --terms.
TARGET_TERM_IDS: List[str] = list(TERM_MAP.keys())


console = Console()
worker_states = {}

def update_worker(worker_id: int, status: str = None, current: str = None, active: str = None, courses: int = None, total_courses: int = None, errors: int = None, started: bool = False, finished: bool = False, reset: bool = False):
    if worker_id not in worker_states or reset:
        worker_states[worker_id] = {"status": "Waiting...", "current": "", "active": "", "courses": 0, "total_courses": 0, "errors": 0, "start_time": None, "end_time": None}
    
    state = worker_states[worker_id]
    if status is not None: state["status"] = status
    if current is not None: state["current"] = current
    if active is not None: state["active"] = active
    if courses is not None: state["courses"] += courses
    if total_courses is not None: state["total_courses"] += total_courses
    if errors is not None: state["errors"] += errors
    if started: state["start_time"] = time.time()
    if finished: state["end_time"] = time.time()

def _worker_elapsed(state: dict) -> float:
    if state["start_time"] is None:
        return 0.0
    end = state["end_time"] if state["end_time"] else time.time()
    return end - state["start_time"]

def generate_table() -> Table:
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Worker", style="dim", width=10)
    table.add_column("Status", width=20)
    table.add_column("Active", width=14)
    table.add_column("Current Task", width=50)
    table.add_column("Courses", justify="right")
    table.add_column("Errors", justify="right", style="red")
    table.add_column("Time", justify="right", style="cyan")

    for w_id in sorted(worker_states.keys()):
        state = worker_states[w_id]
        t = _fmt_time(_worker_elapsed(state))
        active = state.get("active", "")
        if len(active) > 12: active = active[:9] + "..."
        cur = state["current"]
        if len(cur) > 48: cur = cur[:45] + "..."
        
        # Color the status based on state
        status = state["status"]
        if status == "Finished":
            status = f"[green]{status}[/green]"
        elif status == "Error":
            status = f"[red]{status}[/red]"
        elif status == "Waiting...":
            status = f"[dim]{status}[/dim]"
        else:
            status = f"[yellow]{status}[/yellow]"
        
        table.add_row(
            f"Worker {w_id}", 
            status, 
            active,
            cur, 
            f"{state['courses']} / {state['total_courses']}", 
            str(state["errors"]), 
            t
        )
    return table


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_existing_schedule_output(output_path: str) -> List[Dict[str, Any]]:
    """Load existing term-grouped schedule output for incremental merging."""
    if not os.path.exists(output_path):
        return []
    try:
        with open(output_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning: failed to load existing schedule output: {e}[/yellow]")
        return []
    if not isinstance(data, list):
        console.print("[yellow]Warning: existing schedule output is not a term list; starting fresh.[/yellow]")
        return []
    return data


def merge_term_results(
    all_terms_data: List[Dict[str, Any]],
    term_label: str,
    term_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge newly scraped course results into the existing term-grouped structure."""
    merged_terms: List[Dict[str, Any]] = []
    found_term = False

    for term_data in all_terms_data:
        if term_data.get("term") != term_label:
            merged_terms.append(term_data)
            continue

        found_term = True
        merged_term = dict(term_data)
        courses = list(merged_term.get("courses", []))
        course_index = {
            course.get("course_code"): index
            for index, course in enumerate(courses)
            if course.get("course_code")
        }

        for course in term_results:
            course_code = course.get("course_code")
            if course_code and course_code in course_index:
                courses[course_index[course_code]] = course
            else:
                courses.append(course)
                if course_code:
                    course_index[course_code] = len(courses) - 1

        merged_term["courses"] = courses
        merged_terms.append(merged_term)

    if not found_term:
        merged_terms.append({
            "term": term_label,
            "courses": list(term_results),
        })

    return merged_terms

def log_error(worker_id: int, message: str):
    error_log_path = os.path.join(DATA_DIR, "scraper_errors.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(error_log_path, "a") as f:
            f.write(f"[{timestamp}] [Worker {worker_id}] {message}\n")
    except Exception:
        pass

def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(round(seconds)), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


UI_SETTLE_SECONDS = 1.0 - 0.65
COURSE_COOLDOWN_SECONDS = 3.0 - 2
RESULT_NAV_COOLDOWN_SECONDS = 1.0 - 0.65

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_PATTERN = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
TIME_RANGE_PATTERN = r"(\d{1,2}:\d{2}\s+[AP]M)\s+to\s+(\d{1,2}:\d{2}\s+[AP]M)"

# Mapping from MyTimetable 3-letter day names to Mosaic 2-letter abbreviations
DAY_ABBREV_MAP = {
    "Mon": "Mo", "Tue": "Tu", "Wed": "We", "Thu": "Th",
    "Fri": "Fr", "Sat": "Sa", "Sun": "Su",
}


def _day_to_mosaic(day: str) -> str:
    """Convert 3-letter day name (Mon) to 2-letter mosaic format (Mo)."""
    return DAY_ABBREV_MAP.get(day, day)


def _time_to_mosaic(t: str) -> str:
    """Convert '3:30 PM' to '3:30PM' (remove space before AM/PM)."""
    return re.sub(r"\s+([AP]M)", r"\1", t.strip()) if t else t


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
        course_code: str = (course.get("code") or "").strip()
        if not course_code:
            continue

        course_codes.append(course_code)

        if limit is not None and len(course_codes) >= limit:
            break

    return course_codes


def load_course_title_map(
    path: Optional[str] = None,
) -> Dict[str, str]:
    """Build a mapping from course code -> course title from all_courses.json."""
    path = path or os.path.join(DATA_DIR, "all_courses.json")
    with open(path) as f:
        courses = json.load(f)
    return {
        (c.get("code") or "").strip(): (c.get("name") or "").strip()
        for c in courses
        if (c.get("code") or "").strip()
    }


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


async def rewind_to_first_result(page: Page, max_steps: int = 200, worker_id: Optional[int] = None) -> bool:
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
            if worker_id is not None: update_worker(worker_id, current="Result index reset to 1")
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

                if worker_id is not None: update_worker(worker_id, current="Warning: could not fully rewind to result 1")
    return False


async def remove_selected_course(page: Page, course_code: Optional[str] = None, worker_id: int = None) -> None:
    if worker_id is not None: update_worker(worker_id, current="Attempting course cleanup...")

    try:
        await rewind_to_first_result(page)
    except Exception:
        pass

    trash_button = page.locator(".cnf_trash_button:visible").first

    if await trash_button.count() == 0:
        if worker_id is not None: update_worker(worker_id, current="No course button found to remove (already clean)")
        return
    await trash_button.scroll_into_view_if_needed()
    await trash_button.dispatch_event("click", {"bubbles": True})

    if worker_id is not None: update_worker(worker_id, current=f"Removed Course: {course_code} from Results")

    await asyncio.sleep(0.5)
    if worker_id is not None: update_worker(worker_id, current="Cleanup complete")

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
        raw_bldg = bldg_match.group(1).strip()
        if " - " in raw_bldg:
            raw_bldg = raw_bldg.split(" - ", 1)[-1]
        raw_bldg = raw_bldg.replace("_", " ")
        if raw_bldg.endswith("LAB") and not raw_bldg.endswith(" LAB"):
            raw_bldg = raw_bldg[:-3] + " LAB"
        building = raw_bldg.strip()

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
    hours_text: str, section_blocks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Expand parsed time segments into per-day blocks with LEC/LAB/TUT labels."""
    legend_segments = parse_schedule_segments(hours_text)
    
    assigned_segments = []
    unassigned_sections = []
    
    for sec in section_blocks:
        row_txt = sec.get("row_txt", "")
        sec_segments = parse_schedule_segments(row_txt)
        if sec_segments:
            assigned_segments.append((sec, sec_segments))
            for s in sec_segments:
                for ls in list(legend_segments):
                    if s["days"] == ls["days"] and s["start"] == ls["start"] and s["end"] == ls["end"]:
                        legend_segments.remove(ls)
                        break
        else:
            unassigned_sections.append(sec)
            
    unique_comps = []
    for sec in unassigned_sections:
        comp = sec.get("section", "Unknown").split()[0]
        if comp not in unique_comps:
            unique_comps.append(comp)

    comp_to_segs = {c: [] for c in unique_comps}
    if len(legend_segments) == len(unique_comps):
        for c, s in zip(unique_comps, legend_segments):
            comp_to_segs[c].append(s)
    elif len(unique_comps) > 0:
        for i, s in enumerate(legend_segments):
            c = unique_comps[min(i, len(unique_comps)-1)]
            comp_to_segs[c].append(s)

    for sec in unassigned_sections:
        comp = sec.get("section", "Unknown").split()[0]
        assigned_segments.append((sec, comp_to_segs[comp]))
        
    expanded: List[Dict[str, Any]] = []
    for sec, segs in assigned_segments:
        section_label = sec.get("section", "Unknown")
        component = (
            section_label.split()[0] if section_label != "Unknown" else "Unknown"
        )
        for seg in segs:
            for day in seg["days"]:
                expanded.append(
                    {
                        "day": day,
                        "start": seg["start"],
                        "end": seg["end"],
                        "type": component,
                        "section": section_label,
                    }
                )

    return expanded


def combinations_to_sections(
    combinations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Flatten combination-based data into mosaic-style sections.

    Each unique section label (e.g. 'LEC C01') across all combinations becomes
    a single section entry.  Its ``details`` list contains one item per
    distinct day/time block observed for that section.
    """
    # Keyed by section label -> {meta, details_set, details_list}
    section_map: Dict[str, Dict[str, Any]] = {}

    for combo in combinations:
        section_meta: Dict[str, Dict[str, str]] = {}
        for sec in combo.get("sections", []):
            label = sec.get("section", "Unknown")
            section_meta[label] = sec

            if label not in section_map:
                section_map[label] = {
                    "section_name": label,
                    "session": "1",
                    "status": "Open",
                    "instructor": sec.get("instructor", "Staff"),
                    "room": sec.get("location", "TBD"),
                    "mode": sec.get("mode", "Unknown"),
                    "parents": [],
                    "class_number": sec.get("class_number", -1),
                    "details_seen": set(),
                    "details": [],
                }
            
            # Aggregate parents from all combos
            for p in sec.get("parents", []):
                if p not in section_map[label]["parents"]:
                    section_map[label]["parents"].append(p)

        for block in combo.get("schedule_blocks", []):
            label = block.get("section", "Unknown")
            if label not in section_map:
                meta = section_meta.get(label, {})
                section_map[label] = {
                    "section_name": label,
                    "session": "1",
                    "status": "Open",
                    "instructor": meta.get("instructor", "Staff"),
                    "room": meta.get("location", "TBD"),
                    "mode": meta.get("mode", "Unknown"),
                    "parents": [],
                    "class_number": meta.get("class_number", -1),
                    "details_seen": set(),
                    "details": [],
                }

            day_mosaic = _day_to_mosaic(block.get("day", ""))
            start_mosaic = _time_to_mosaic(block.get("start", ""))
            end_mosaic = _time_to_mosaic(block.get("end", ""))
            detail_key = (day_mosaic, start_mosaic, end_mosaic)

            if detail_key not in section_map[label]["details_seen"]:
                section_map[label]["details_seen"].add(detail_key)
                section_map[label]["details"].append({
                    "days": day_mosaic,
                    "start_time": start_mosaic,
                    "end_time": end_mosaic,
                    "room": section_map[label]["room"],
                    "instructor": section_map[label]["instructor"]
                })

        # Remove the TBA fallback loop from here
        pass

    # Build final list, stripping internal tracking fields
    result: List[Dict[str, Any]] = []
    for entry in section_map.values():
        if not entry["details"]:
            entry["details"].append({
                "days": "TBA",
                "start_time": "TBA",
                "end_time": "",
                "room": entry["mode"] if entry["mode"] in ("Online", "Blended") else entry["room"],
                "instructor": entry["instructor"]
            })
        result.append({
            "section_name": entry["section_name"],
            "session": entry["session"],
            "status": entry["status"],
            "parents": entry.get("parents", []),
            "class_number": entry.get("class_number", -1),
            "details": entry["details"],
        })
    return result


async def scrape_course_combinations(
    page: Page, course_code: str, worker_id: int,
    term_label: str = "", course_title_map: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    update_worker(worker_id, current=f"--- Processing Course: {course_code} ---")
    course_selected = False

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
            update_worker(worker_id, current=f"No suggestion found for {course_code}; skipping.")
            return None

        await target.click()
        course_selected = True
        update_worker(worker_id, current="Selected suggestion")
        await asyncio.sleep(COURSE_COOLDOWN_SECONDS)

        other_term = await get_other_term_availability(page, course_code)
        if other_term:
            update_worker(worker_id, current=f"{course_code} is only available in {other_term}; recording term.")
            course_selected = False
            return {
                "course_code": course_code,
                "course_title": (course_title_map or {}).get(course_code, ""),
                "term": term_label,
                "available_term": other_term,
                "sections": [],
            }

        selected_labels = await wait_for_selected_course_labels(page, course_code)
        if not any(
            normalize_course_code(label).startswith(normalized_target_code)
            for label in selected_labels
        ):
            update_worker(worker_id, current=f"Selected course mismatch for {course_code}. Selected: {selected_labels}")
            await remove_selected_course(page)
            course_selected = False
            return None

        # 2. View Schedules (if prompt appears)
        view_btn = page.locator(".welcome-search-continue")
        try:
            if await view_btn.is_visible():
                await view_btn.click()
                update_worker(worker_id, current="Clicked 'View Schedules'")
                await asyncio.sleep(COURSE_COOLDOWN_SECONDS)
        except Exception:
            pass

        other_term = await get_other_term_availability(page, course_code)
        if other_term:
            update_worker(worker_id, current=f"{course_code} is only available in {other_term}; recording term.")
            course_selected = False
            return {
                "course_code": course_code,
                "course_title": (course_title_map or {}).get(course_code, ""),
                "term": term_label,
                "available_term": other_term,
                "sections": [],
            }

        # 3. Wait for Results and determining total combinations
        total_span = page.locator(".results-nav .results-total-schedules").first
        try:
            await total_span.wait_for(state="visible", timeout=15000)
            total_text = await total_span.inner_text()
            total_combos = int(total_text.strip())
            update_worker(worker_id, current=f"Found {total_combos} combinations")
        except Exception as e:
            update_worker(worker_id, current=f"Could not determine total combinations: {e}")
            return None

        course_title = (course_title_map or {}).get(course_code, "")
        combinations: List[Dict[str, Any]] = []

        # 4. Cycle and Extract
        next_btn = page.locator(".results-action-next").first

        for i in range(1, total_combos + 1):
            await asyncio.sleep(UI_SETTLE_SECONDS)
            legend_block = page.locator(".course_cell_legend").filter(
                has_text=course_code
            )

            try:
                # Sections details (Instructor, Room, etc.)
                # Parse by vsbselectionnew groups to capture parent-child relationships.
                # Each vsbselectionnew label groups a parent (first type_block, e.g. LEC)
                # with its children (subsequent type_blocks, e.g. LAB/TUT).
                section_blocks: List[Dict[str, Any]] = []
                selection_groups = legend_block.locator("label.vsbselectionnew")
                group_count = await selection_groups.count()

                if group_count > 0:
                    for g in range(group_count):
                        group = selection_groups.nth(g)
                        type_blocks = group.locator(".selection_table .type_block")
                        row_count = await type_blocks.count()

                        parent_label = ""
                        for j in range(row_count):
                            type_block = type_blocks.nth(j)
                            section_label = (await type_block.inner_text()).strip()
                            section_row = type_block.locator("xpath=ancestor::tr[1]")
                            row_txt = await section_row.inner_text()
                            parsed = parse_section_details(" ".join(row_txt.split()))

                            type_match = re.search(r"(LEC|LAB|TUT|SEM)\s+[A-Z0-9]+", section_label)
                            section_label = (
                                type_match.group(0)
                                if type_match
                                else section_label or f"Section {j+1}"
                            )

                            crn_value = -1
                            try:
                                crn_el = section_row.locator(".crn_value")
                                if await crn_el.count() > 0:
                                    crn_text = (await crn_el.first.inner_text()).strip()
                                    if crn_text.isdigit():
                                        crn_value = int(crn_text)
                            except Exception:
                                pass

                            if j == 0:
                                # First type_block in the group is the parent
                                parent_label = section_label
                                section_blocks.append({"section": section_label, "parents": [], "class_number": crn_value, "row_txt": row_txt, **parsed})
                            else:
                                # Subsequent type_blocks are children of the parent
                                section_blocks.append({"section": section_label, "parents": [parent_label], "class_number": crn_value, "row_txt": row_txt, **parsed})
                else:
                    # Fallback: no vsbselectionnew groups found, use flat iteration
                    type_blocks = legend_block.locator(".selection_table .type_block")
                    row_count = await type_blocks.count()
                    for j in range(row_count):
                        type_block = type_blocks.nth(j)
                        section_label = (await type_block.inner_text()).strip()
                        section_row = type_block.locator("xpath=ancestor::tr[1]")
                        row_txt = await section_row.inner_text()
                        parsed = parse_section_details(" ".join(row_txt.split()))

                        type_match = re.search(r"(LEC|LAB|TUT|SEM)\s+[A-Z0-9]+", section_label)
                        section_label = (
                            type_match.group(0)
                            if type_match
                            else section_label or f"Section {j+1}"
                        )

                        crn_value = -1
                        try:
                            crn_el = section_row.locator(".crn_value")
                            if await crn_el.count() > 0:
                                crn_text = (await crn_el.first.inner_text()).strip()
                                if crn_text.isdigit():
                                    crn_value = int(crn_text)
                        except Exception:
                            pass

                        section_blocks.append({"section": section_label, "parents": [], "class_number": crn_value, "row_txt": row_txt, **parsed})

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

                day_blocks = expand_schedule_blocks(hours_text, section_blocks)

                combinations.append(
                    {
                        "index": i,
                        "schedule_blocks": day_blocks,
                        "sections": section_blocks,
                    }
                )
                if SCRAPE_SCHEDULE_DEBUG:
                    update_worker(worker_id, current=f"  Captured combo {i}/{total_combos}", end="\r")
            except Exception as e:
                if SCRAPE_SCHEDULE_DEBUG:
                    update_worker(worker_id, current=f"\n  Failed combo {i}: {e}")
                else:
                    update_worker(worker_id, current=f"[course {course_code}] combo {i}/{total_combos}: {e}")

            if i < total_combos:
                await next_btn.click()
                await asyncio.sleep(RESULT_NAV_COOLDOWN_SECONDS)

        if SCRAPE_SCHEDULE_DEBUG:
            print(
                f"\nCaptured {len(combinations)} combinations for {course_code}."
            )

        # Convert combinations into mosaic-compatible flat sections
        sections = combinations_to_sections(combinations)
        return {
            "course_code": course_code,
            "course_title": course_title,
            "term": term_label,
            "sections": sections,
        }
    finally:
        if course_selected:
            await remove_selected_course(page, course_code=course_code, worker_id=worker_id)
            await asyncio.sleep(COURSE_COOLDOWN_SECONDS)


async def setup_timetable_page(
    browser: Browser, worker_id: int, term_data_id: str
) -> Tuple[BrowserContext, Page]:
    term_label = TERM_MAP.get(term_data_id, term_data_id)
    context = await browser.new_context()
    page = await context.new_page()

    try:
        update_worker(worker_id, current=f"[worker {worker_id}] Logging in...")
        await page.goto("https://mytimetable.mcmaster.ca/login.jsp")
        await page.fill("#word1", MOSAIC_USERNAME or "")
        await page.fill("#word2", MOSAIC_PASSWORD or "")
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        update_worker(worker_id, current=f"[worker {worker_id}] Selecting term: {term_label}...")
        
        # Wait for the term cards container to load (give it up to 30 seconds)
        try:
            await page.wait_for_selector("a.term-card-title", timeout=30000)
        except Exception:
            pass  # We will let the explicit checks below handle the failure

        # Select term by its data-term attribute on the card container
        term_card = page.locator(f"div.term-card[data-term='{term_data_id}'] a.term-card-title")
        
        if await term_card.count() > 0:
            await term_card.first.click()
        else:
            # Fallback: try matching by text label
            term_link = page.locator("a.term-card-title").filter(has_text=term_label)
            if await term_link.count() > 0:
                await term_link.first.click()
            else:
                raise RuntimeError(f"Could not find term card for {term_label} (data-term={term_data_id})")

        await page.wait_for_selector("#code_number", timeout=30000)
        update_worker(worker_id, current=f"[worker {worker_id}] Ready ({term_label})")
        return context, page
    except Exception:
        await context.close()
        raise


async def scrape_course_chunk(
    browser: Browser, worker_id: int, course_codes: List[str], term_data_id: str,
    course_title_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    term_label = TERM_MAP.get(term_data_id, term_data_id)
    context: Optional[BrowserContext] = None
    partial_path = os.path.join(
        DATA_DIR, f"all_possible_schedules.worker_{worker_id}_{term_data_id}.json"
    )
    results: List[Dict[str, Any]] = []
    update_worker(worker_id, status="Running", active="Init", total_courses=len(course_codes), started=True)

    try:
        setup_success = False
        for attempt in range(5):
            try:
                context, page = await setup_timetable_page(browser, worker_id, term_data_id)
                setup_success = True
                break
            except Exception as e:
                if attempt == 4:
                    update_worker(worker_id, current=f"[worker {worker_id}] Failed during setup: {e}")
                    return []
                update_worker(worker_id, current=f"[worker {worker_id}] Setup failed (attempt {attempt+1}/5), retrying...")
                await asyncio.sleep(2)
        
        if not setup_success:
            return []

        for idx, code in enumerate(course_codes, start=1):
            update_worker(worker_id, current=f"[worker {worker_id}] Course {idx}/{len(course_codes)}: {code}")
            for attempt in range(5):
                try:
                    result = await scrape_course_combinations(
                        page, code, worker_id,
                        term_label=term_label,
                        course_title_map=course_title_map,
                    )
                    if result:
                        results.append(result)
                        update_worker(worker_id, courses=1, active=code)
                        with open(partial_path, "w") as f:
                            json.dump(results, f, indent=2)
                        if not SCRAPE_SCHEDULE_DEBUG:
                            update_worker(worker_id, current=f"[worker {worker_id}] {code}")
                    break
                except Exception as e:
                    if attempt == 4:
                        update_worker(worker_id, current=f"[worker {worker_id}] Error scraping {code}: {e}")
                    else:
                        update_worker(worker_id, current=f"[worker {worker_id}] Retry {attempt+1}/5 for {code}")
                        await asyncio.sleep(1)
            # finally block logic moved outside the retry loop to apply per-course cooldown
            await asyncio.sleep(COURSE_COOLDOWN_SECONDS)

        with open(partial_path, "w") as f:
            json.dump(results, f, indent=2)

        update_worker(worker_id, current=f"[worker {worker_id}] Finished {len(results)} scraped courses.")
        return results
    finally:
        update_worker(worker_id, status="Finished", finished=True)
        if context:
            await context.close()


async def scrape_term(
    browser: Browser,
    term_data_id: str,
    course_codes: List[str],
    course_title_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Run all workers for a single term, return scraped course data."""
    term_label = TERM_MAP.get(term_data_id, term_data_id)
    console.print(f"\n{'='*60}")
    console.print(f"Starting scrape for term: {term_label} ({term_data_id})")
    console.print(f"{'='*60}")
    term_start = time.time()

    chunks = [chunk for chunk in chunk_list(course_codes, WORKER_COUNT) if chunk]
    console.print(
        f"[bold green]{term_label}: {len(course_codes)} courses, {len(chunks)} workers.[/bold green]"
    )

    # Reset worker states for the new term
    worker_states.clear()
    for i in range(1, len(chunks) + 1):
        update_worker(i)

    tasks = []
    for worker_id, chunk in enumerate(chunks, start=1):
        tasks.append(
            asyncio.create_task(
                scrape_course_chunk(browser, worker_id, chunk, term_data_id, course_title_map)
            )
        )
        # Stagger avoids hammering login at the exact same millisecond.
        stagger = random.uniform(3.0, 10.0)
        await asyncio.sleep(stagger)

    worker_results = await asyncio.gather(*tasks, return_exceptions=True)
    term_results: List[Dict[str, Any]] = []
    for worker_id, chunk_results in enumerate(worker_results, start=1):
        if isinstance(chunk_results, Exception):
            update_worker(
                worker_id,
                current=f"[worker {worker_id}] Failed: {chunk_results}",
            )
            continue
        if not isinstance(chunk_results, list):
            update_worker(
                worker_id,
                current=f"[worker {worker_id}] Unexpected result type: {type(chunk_results)}",
            )
            continue
        term_results.extend(chunk_results)

    elapsed_term = time.time() - term_start
    console.print(
        f"Term {term_label} done. Scraped {len(term_results)} courses in {format_wall_time(elapsed_term)}."
    )
    return term_results


async def run(term_ids: Optional[List[str]] = None) -> None:
    run_started = time.time()
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "all_possible_schedules.json")

    terms_to_scrape = term_ids or TARGET_TERM_IDS
    console.print(f"Terms to scrape: {[TERM_MAP.get(t, t) for t in terms_to_scrape]}")
    if not SCRAPE_SCHEDULE_DEBUG:
        console.print(
            "[dim](set SCRAPE_SCHEDULE_DEBUG=1 or DEBUG=1 for full logs)[/dim]"
        )

    course_codes = load_course_codes(limit=COURSE_LIMIT)
    course_title_map = load_course_title_map()
    console.print(f"Loaded {len(course_codes)} courses from catalog.")

    all_terms_data = load_existing_schedule_output(output_path)

    with Live(
        get_renderable=generate_table, console=console, refresh_per_second=4
    ) as live:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            try:
                for term_data_id in terms_to_scrape:
                    term_label = TERM_MAP.get(term_data_id, term_data_id)

                    term_results = await scrape_term(
                        browser, term_data_id, course_codes, course_title_map
                    )

                    all_terms_data = merge_term_results(
                        all_terms_data, term_label, term_results
                    )

                    # Save incremental progress after each term
                    with open(output_path, "w") as f:
                        json.dump(all_terms_data, f, indent=2)
                    console.print(f"Saved progress after {term_label}.")

                    cleanup_worker_files("all_possible_schedules")

                # Final write
                with open(output_path, "w") as f:
                    json.dump(all_terms_data, f, indent=2)

                total_courses = sum(
                    len(t.get("courses", [])) for t in all_terms_data
                )
                elapsed_total = time.time() - run_started
                console.print(
                    f"\nDone. Saved {total_courses} courses across "
                    f"{len(all_terms_data)} terms to {output_path}"
                )
                console.print(f"Total time: {format_wall_time(elapsed_total)}")
            finally:
                await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape MyTimetable course schedule combinations"
    )
    parser.add_argument(
        "--terms",
        help=(
            "Comma-separated list of term data-term IDs to scrape, "
            "e.g. 3202620,3202630. Defaults to all known terms."
        ),
    )
    args = parser.parse_args()

    selected_term_ids = None
    if args.terms:
        selected_term_ids = [t.strip() for t in args.terms.split(",") if t.strip()]
        unknown = [t for t in selected_term_ids if t not in TERM_MAP]
        if unknown:
            parser.error(
                f"Unknown term ID(s): {unknown}. Known: {list(TERM_MAP.keys())}"
            )

    asyncio.run(run(term_ids=selected_term_ids))
