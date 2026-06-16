import argparse
import asyncio
import os
import re
import string
import itertools
import json
import time
import random
from typing import Optional, List, Dict, Any, Set
from utils import (
    cleanup_worker_files,
    split_catalog_course_name,
    build_course_title_code_map,
    resolve_scraped_course_code,
    COURSE_CODE_RE,
)
from dotenv import load_dotenv
import psycopg2
from playwright.async_api import async_playwright, Page, Frame, Browser
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

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

def log_error(worker_id: int, message: str):
    error_log_path = os.path.join(DATA_DIR, "scraper_errors.log")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(error_log_path, "a") as f:
            f.write(f"[{timestamp}] [Worker {worker_id}] {message}\n")
    except Exception:
        pass

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MOSAIC_USERNAME = os.getenv("MOSAIC_USERNAME")
MOSAIC_PASSWORD = os.getenv("MOSAIC_PASSWORD")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL")

TARGET_TERMS = ["2269", "2271"]

TERM_LABELS = {
    "2259": "Fall 2025",
    "2261": "Winter 2026",
    "2265": "Spring/Summer 2026",
    "2269": "Fall 2026",
    "2271": "Winter 2027",
    "2275": "Spring/Summer 2027",
}


def group_existing_section_codes_by_term(rows) -> Dict[str, Set[str]]:
    grouped: Dict[str, Set[str]] = {}
    for code, term in rows:
        if not code or not term:
            continue
        grouped.setdefault(term, set()).add(code)
    return grouped


def get_existing_section_codes_by_term(term_labels: List[str]) -> Dict[str, Set[str]]:
    """Query the database for course codes that already have sections by term."""
    if not DATABASE_URL:
        console.print("[yellow]Warning: DATABASE_URL not set, cannot check existing course sections.[/yellow]")
        return {}
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT c.code, s.term
            FROM course c
            JOIN section s ON s.course_id = c.id
            WHERE s.term = ANY(%s)
            """,
            (term_labels,),
        )
        grouped = group_existing_section_codes_by_term(cur.fetchall())
        cur.close()
        conn.close()
        total_codes = sum(len(codes) for codes in grouped.values())
        console.print(f"Found {total_codes} course/term pairs with sections in DB.")
        return grouped
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to query existing course sections: {e}[/yellow]")
        return {}


def load_existing_schedule_output(output_path: str) -> List[Dict[str, Any]]:
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


def merge_term_results(all_terms_data: List[Dict[str, Any]], term_label: str, term_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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





def load_course_title_code_map() -> Dict[str, str]:
    catalog_path = os.path.join(DATA_DIR, "all_courses.json")
    try:
        with open(catalog_path, "r") as f:
            courses = json.load(f)
    except Exception as e:
        console.print(f"[yellow]Warning: failed to load course catalog for title lookup: {e}[/yellow]")
        return {}
    if not isinstance(courses, list):
        return {}
    return build_course_title_code_map(courses)




def parse_selected_letters(value: Optional[str]) -> List[str]:
    if not value:
        return list(string.ascii_uppercase)

    compact = value.replace(",", "").replace(" ", "").upper()
    if not compact or any(letter not in string.ascii_uppercase for letter in compact):
        raise ValueError("--letters must contain only letters A-Z, for example C,D or CD")

    selected_letters: List[str] = []
    seen: Set[str] = set()
    for letter in compact:
        if letter in seen:
            continue
        selected_letters.append(letter)
        seen.add(letter)

    return selected_letters


def build_letter_chunks(letters: List[str], headless: bool, one_worker_per_letter: bool = False) -> tuple[List[List[str]], int]:
    if one_worker_per_letter:
        chunks = [[letter] for letter in letters]
        return chunks, len(chunks)

    if headless:
        chunk_size = 2
        chunks = [letters[i:i+chunk_size] for i in range(0, len(letters), chunk_size)]
        return chunks, len(chunks)

    return [letters], 1


def validate_courses_per_worker(value) -> int:
    try:
        courses_per_worker = int(value)
    except (TypeError, ValueError):
        raise ValueError("--courses-per-worker must be a positive integer")

    if courses_per_worker < 1:
        raise ValueError("--courses-per-worker must be at least 1")

    return courses_per_worker


def build_worker_assignments(
    letters: List[str],
    letter_counts: Dict[str, int],
    courses_per_worker: int,
) -> List[List[Dict[str, int | str]]]:
    threshold = validate_courses_per_worker(courses_per_worker)
    assignments: List[List[Dict[str, int | str]]] = []
    packed_worker: List[Dict[str, int | str]] = []
    packed_count = 0

    def flush_packed_worker():
        nonlocal packed_worker, packed_count
        if packed_worker:
            assignments.append(packed_worker)
            packed_worker = []
            packed_count = 0

    for letter in letters:
        count = int(letter_counts.get(letter, 0))
        if count <= 0:
            continue

        if count > threshold:
            flush_packed_worker()
            for start in range(0, count, threshold):
                end = min(start + threshold, count)
                assignments.append([{
                    "letter": letter,
                    "start": start,
                    "end": end,
                    "total": count,
                }])
            continue

        if packed_worker and packed_count + count > threshold:
            flush_packed_worker()

        packed_worker.append({
            "letter": letter,
            "start": 0,
            "end": count,
            "total": count,
        })
        packed_count += count

    flush_packed_worker()
    return assignments


def format_assignment_label(assignment: Dict[str, int | str]) -> str:
    letter = assignment["letter"]
    start = int(assignment["start"])
    end = int(assignment["end"])
    total = int(assignment["total"])
    if start == 0 and end == total:
        return str(letter)
    return f"{letter} {start + 1}-{end}"



async def get_peoplesoft_frame(page: Page) -> Frame | Page:
    iframe = page.frame(name="TargetContent")
    if iframe:
        return iframe
    return page

def _fmt_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(round(seconds)), 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


async def navigate_to_term_catalog(page: Page, worker_id: int, term_code: str) -> Frame | Page:
    update_worker(worker_id, status="Logging In", current=f"Navigating to Mosaic login...")
    try:
        await page.goto("https://mosaic.mcmaster.ca/psp/prcsprd/?cmd=login", wait_until="domcontentloaded", timeout=20000)
    except Exception:
        pass # The page might infinitely load, but the form could still be usable
    
    for attempt in range(3):
        await page.locator("#userid").wait_for(state="visible", timeout=30000)

        update_worker(worker_id, status="Logging In", current=f"Logging in (Attempt {attempt + 1})...")
        await page.fill("#userid", MOSAIC_USERNAME or "")
        await page.fill("#pwd", MOSAIC_PASSWORD or "")
        # Increase timeout dramatically for the login step
        await page.click("input[name='Submit']", timeout=90000)

        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass # sometimes networkidle never fires on Peoplesoft, we rely on the next visible locator anyway

        # Check if we hit the "Session Expired" page right after login
        expired_link = page.locator("a:has-text('Sign in to PeopleSoft')")
        if await expired_link.count() > 0 and await expired_link.first.is_visible():
            update_worker(worker_id, status="Logging In", current=f"Session expired detected, retrying...")
            await expired_link.first.click()
            await asyncio.sleep(2)
            continue

        break

    update_worker(worker_id, status="Navigating", current=f"Waiting for Student Center...")
    student_center_div = page.locator("div[id^='win0divPTNUI_LAND_REC_GROUPLET']").filter(has_text=re.compile("Student Center", re.IGNORECASE)).first
    if await student_center_div.count() == 0:
        student_center_div = page.locator("text='Student Center'").first
    await student_center_div.wait_for(state="visible", timeout=90000)
    await student_center_div.click()
    await page.wait_for_load_state("networkidle")

    await asyncio.sleep(2.3)
    frame = await get_peoplesoft_frame(page)

    update_worker(worker_id, status="Navigating", current=f"Clicking Course Search...")
    search_link = frame.locator("#DERIVED_SSS_SCR_SSS_LINK_ANCHOR1")
    await search_link.wait_for(state="visible", timeout=90000)
    await search_link.click()
    await page.wait_for_load_state("networkidle")

    await asyncio.sleep(2.3)
    frame = await get_peoplesoft_frame(page)

    update_worker(worker_id, status="Navigating", current=f"Clicking Browse Course Catalog...")
    browse_link = frame.locator("text=Browse Course Catalog")
    await browse_link.wait_for(state="visible", timeout=15000)
    await browse_link.click()
    await page.wait_for_load_state("networkidle")

    await asyncio.sleep(2.3)
    frame = await get_peoplesoft_frame(page)

    update_worker(worker_id, status="Filtering", current=f"Selecting Career and Term...")
    career_select = frame.locator("#MCM_SSS_BCC_WRK_ACAD_CAREER")
    await career_select.wait_for(state="visible", timeout=15000)
    await career_select.select_option("UGRD")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2.3)
    frame = await get_peoplesoft_frame(page)

    term_select = frame.locator("#MCM_SSS_BCC_WRK_STRM")
    await term_select.wait_for(state="visible", timeout=15000)
    await term_select.select_option(term_code)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2.3)
    frame = await get_peoplesoft_frame(page)

    update_worker(worker_id, status="Searching", current=f"Executing Search...")
    search_btn = frame.locator("#MCM_SSS_BCC_WRK_SSS_PB_CHANGE")
    await search_btn.wait_for(state="visible", timeout=15000)
    await search_btn.click()
    await page.wait_for_load_state("networkidle")

    await asyncio.sleep(2.7)
    return await get_peoplesoft_frame(page)


async def count_courses_for_letters(browser: Browser, term_code: str, letters: List[str]) -> Dict[str, int]:
    context = await browser.new_context()
    page = await context.new_page()
    update_worker(0, status="Counting", current=f"Counting letters for {TERM_LABELS.get(term_code, term_code)}", started=True, reset=True)
    counts: Dict[str, int] = {}

    try:
        frame = await navigate_to_term_catalog(page, 0, term_code)
        for letter in letters:
            update_worker(0, status="Counting", active=letter, current=f"Counting letter {letter}...")
            letter_btn = frame.locator(f"#DERIVED_SSS_BCC_SSR_ALPHANUM_{letter}")

            if await letter_btn.count() == 0 or not await letter_btn.first.is_visible():
                counts[letter] = 0
                continue

            await letter_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2.7)
            frame = await get_peoplesoft_frame(page)

            expand_btn = frame.locator("#DERIVED_SSS_BCC_SSS_EXPAND_ALL\\$97\\$")
            if await expand_btn.count() > 0 and await expand_btn.first.is_visible():
                await expand_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2.7)
                frame = await get_peoplesoft_frame(page)

            prev_count = -1
            stable_loops = 0
            for _ in range(15):
                curr_count = await frame.locator("a[id^='CRSE_TITLE$']").count()
                if curr_count == prev_count:
                    stable_loops += 1
                    if stable_loops >= 2:
                        break
                else:
                    stable_loops = 0
                prev_count = curr_count
                await asyncio.sleep(0.9)

            counts[letter] = await frame.locator("a[id^='CRSE_TITLE$']").count()

        update_worker(0, status="Finished", active="", current=f"Counted {len(letters)} letters.", finished=True)
        return counts
    finally:
        try:
            await asyncio.wait_for(context.close(), timeout=3.0)
        except Exception:
            pass


async def scrape_letters(browser: Browser, worker_id: int, assignments: List[Dict[str, int | str]], term_code: str, existing_codes: Set[str] = None, title_code_map: Dict[str, str] = None) -> List[Dict[str, Any]]:
    worker_start = time.time()
    assignment_labels = [format_assignment_label(assignment) for assignment in assignments]
    update_worker(worker_id, status="Starting", current=f"Starting assignments: {assignment_labels}", started=True, reset=True)
    context = await browser.new_context()
    page = await context.new_page()
    all_scraped_data = []
    term_label = TERM_LABELS.get(term_code, term_code)
    if title_code_map is None:
        title_code_map = {}
    partial_path = os.path.join(DATA_DIR, f"mosaic_schedules.worker_{worker_id}_{term_code}.json")

    # Load existing progress if available
    if os.path.exists(partial_path):
        try:
            with open(partial_path, "r") as f:
                all_scraped_data = json.load(f)
            update_worker(worker_id, courses=len(all_scraped_data))
        except Exception:
            pass

    try:
        frame = await navigate_to_term_catalog(page, worker_id, term_code)

        for assignment in assignments:
            letter = str(assignment["letter"])
            range_start = int(assignment["start"])
            range_end = int(assignment["end"])
            active_label = format_assignment_label(assignment)
            letter_start = time.time()
            update_worker(worker_id, status="Filtering", active=active_label, current=f"Filtering by letter {letter}...")
            letter_btn = frame.locator(f"#DERIVED_SSS_BCC_SSR_ALPHANUM_{letter}")
            
            if await letter_btn.count() == 0 or not await letter_btn.first.is_visible():
                update_worker(worker_id, status="Running", current=f"Letter {letter} not available.")
                continue

            await letter_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2.7)
            frame = await get_peoplesoft_frame(page)

            update_worker(worker_id, status="Filtering", current=f"Expanding all courses for {letter}...")
            expand_btn = frame.locator("#DERIVED_SSS_BCC_SSS_EXPAND_ALL\\$97\\$")
            if await expand_btn.count() > 0 and await expand_btn.first.is_visible():
                await expand_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2.7)
                frame = await get_peoplesoft_frame(page)

            # Build a mapping of course_index -> {subject, course_nbr} from the expanded page.
            # The subject comes from group headers like "CHEM - Chemistry" (DERIVED_SSS_BCC_GROUP_BOX_1$*)
            # and the course number comes from the CRSE_NBR$N cell in each row.
            course_code_map = await frame.evaluate('''
            () => {
                const map = {};
                // Find all group header links (subject headers like "CHEM - Chemistry")
                const groupHeaders = document.querySelectorAll("a[id^='DERIVED_SSS_BCC_GROUP_BOX_1$']");
                // Find all course number cells
                const courseNbrLinks = document.querySelectorAll("a[id^='CRSE_NBR$']");
                // Find all course title links to get total count
                const courseTitleLinks = document.querySelectorAll("a[id^='CRSE_TITLE$']");

                // Build an ordered list of group header positions and their subjects
                const groups = [];
                for (const header of groupHeaders) {
                    const text = header.innerText.trim();
                    // Extract subject code: "CHEM - Chemistry" -> "CHEM"
                    const subject = text.split(" - ")[0].trim();
                    // Get the vertical position to determine which courses fall under this group
                    const rect = header.getBoundingClientRect();
                    groups.push({ subject, top: rect.top });
                }

                // For each course title link, find its subject and course number
                for (const titleLink of courseTitleLinks) {
                    const match = titleLink.id.match(/\\$(\\d+)$/);
                    if (!match) continue;
                    const idx = match[1];

                    // Get course number from CRSE_NBR$idx
                    const nbrLink = document.querySelector(`a[id='CRSE_NBR$${idx}']`);
                    const courseNbr = nbrLink ? nbrLink.innerText.trim() : "";

                    // Determine the subject by finding the closest group header above this course
                    const titleRect = titleLink.getBoundingClientRect();
                    let subject = "";
                    for (let i = groups.length - 1; i >= 0; i--) {
                        if (groups[i].top <= titleRect.top) {
                            subject = groups[i].subject;
                            break;
                        }
                    }

                    map[idx] = { subject, courseNbr };
                }
                return map;
            }
            ''')
            update_worker(worker_id, status="Parsing", current=f"Built course code map with {len(course_code_map)} entries for letter {letter}.")

            # Wait for course links to fully render and stabilize
            prev_count = -1
            stable_loops = 0
            for _ in range(15):
                curr_count = await frame.locator("a[id^='CRSE_TITLE$']").count()
                if curr_count == prev_count:
                    stable_loops += 1
                    if stable_loops >= 2: # Stable for 4 seconds
                        break
                else:
                    stable_loops = 0
                prev_count = curr_count
                await asyncio.sleep(0.9)

            course_links = frame.locator("a[id^='CRSE_TITLE$']")
            course_count = await course_links.count()
            assignment_end = min(range_end, course_count)
            assignment_count = max(0, assignment_end - range_start)
            update_worker(worker_id, total_courses=assignment_count)
            if assignment_count == 0:
                update_worker(worker_id, status="Running", current=f"No courses in assigned range for {active_label}.")
                continue
            
            for i in range(range_start, assignment_end):
                # Wait for the DOM to recover in case PeopleSoft did a postback after the modal closed
                recovered = False
                for _ in range(10):
                    course_links = frame.locator("a[id^='CRSE_TITLE$']")
                    if await course_links.count() >= course_count:
                        recovered = True
                        break
                    await asyncio.sleep(0.9)
                
                if not recovered:
                    log_error(worker_id, f"DOM never recovered full course count after course index {i-1}. Breaking early.")
                    break
                
                course_link = course_links.nth(i)
                if not await course_link.is_visible():
                    continue

                course_id = await course_link.get_attribute("id")
                idx_str = course_id.split("$")[-1] if course_id else ""
                
                course_title = await course_link.inner_text()
                # Look up the proper course code from our map
                code_info = course_code_map.get(idx_str, {})
                subject = code_info.get("subject", "")
                course_nbr = code_info.get("courseNbr", "")
                scraped_course_code = f"{subject} {course_nbr}".strip() if subject and course_nbr else course_title.strip()
                course_code = resolve_scraped_course_code(scraped_course_code, course_title.strip(), title_code_map)
                
                # Skip if already scraped in a previous run
                if any(c.get("course_code") == course_code for c in all_scraped_data):
                    # We still count it towards total courses processed, but don't re-scrape
                    update_worker(worker_id, status="Running", current=f"Skipping already scraped: {course_code}")
                    continue

                # Skip if the course already exists in the database (--skip-existing flag)
                if existing_codes and course_code in existing_codes:
                    update_worker(worker_id, status="Running", current=f"Skipping (in DB): {course_code}", total_courses=-1)
                    continue

                course_start = time.time()
                # Reset modal container display in case they were nuked by JS override in a previous iteration
                await page.evaluate('''() => {
                    const stuckMask = document.getElementById("pt_modalMask");
                    if (stuckMask) stuckMask.style.display = "";
                    const stuckModal = document.getElementById("pt_modals");
                    if (stuckModal) stuckModal.style.display = "";
                }''')
                update_worker(worker_id, status="Navigating", current=f"Clicking course: {course_code} ({course_title.strip()})")
                await course_link.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2.3)

                modal_frame = None
                is_not_scheduled = False

                # Step 1: Find the modal frame — look for "View Class Sections" button or "not scheduled" text
                for f in page.frames:
                    btn = f.locator("input[id^='DERIVED_SAA_CRS_SSR_PB_GO']")
                    if await btn.count() > 0 and await btn.first.is_visible():
                        modal_frame = f
                        break

                    not_scheduled = f.locator("text=This course has not been scheduled.")
                    if await not_scheduled.count() > 0 and await not_scheduled.first.is_visible():
                        is_not_scheduled = True
                        modal_frame = f
                        break

                schedules = []

                if not modal_frame:
                    update_worker(worker_id, status="Running", current=f"Could not locate modal frame.")
                elif is_not_scheduled:
                    update_worker(worker_id, status="Running", current=f"Course not scheduled.")
                else:
                    # Step 2: Click "View Class Sections" button to reveal the term dropdown
                    view_btn = modal_frame.locator("input[id^='DERIVED_SAA_CRS_SSR_PB_GO']")
                    try:
                        await view_btn.first.click()
                        try:
                            await page.wait_for_load_state("networkidle", timeout=8000)
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        log_error(worker_id, f"Error clicking View Class Sections for {course_code}: {e}")
                        update_worker(worker_id, status="Error", current=f"Error clicking View Class Sections: {e}", errors=1)

                    # Re-find the modal frame after postback
                    modal_frame = None
                    for f in page.frames:
                        term_dropdown = f.locator("#DERIVED_SAA_CRS_TERM_ALT")
                        if await term_dropdown.count() > 0 and await term_dropdown.first.is_visible():
                            modal_frame = f
                            break
                        # Also check if sections already loaded (single-term courses skip the dropdown)
                        if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                            modal_frame = f
                            break
                        not_scheduled = f.locator("text=This course has not been scheduled.")
                        if await not_scheduled.count() > 0 and await not_scheduled.first.is_visible():
                            is_not_scheduled = True
                            modal_frame = f
                            break

                    if not modal_frame:
                        update_worker(worker_id, status="Running", current=f"No dropdown or sections after clicking View Class Sections.")
                    elif is_not_scheduled:
                        update_worker(worker_id, status="Running", current=f"Course not scheduled for any term.")
                    else:
                        # Step 3: Check for the term dropdown and select the correct term
                        term_dropdown = modal_frame.locator("#DERIVED_SAA_CRS_TERM_ALT")
                        if await term_dropdown.count() > 0 and await term_dropdown.first.is_visible():
                            options = await term_dropdown.first.locator(f"option[value='{term_code}']").count()
                            if options == 0:
                                # Term not in dropdown — skip
                                update_worker(worker_id, status="Running", current=f"Term not available for {course_code}.")
                                is_not_scheduled = True
                            else:
                                selected_value = await term_dropdown.first.input_value()
                                if selected_value != term_code:
                                    await term_dropdown.first.select_option(value=term_code)
                                    await asyncio.sleep(0.3)

                                # Step 4: Click "Show Sections" to load sections for selected term
                                show_btn = modal_frame.locator("input[id^='DERIVED_SAA_CRS_SSR_PB_GO']")
                                if await show_btn.count() > 0 and await show_btn.first.is_visible():
                                    try:
                                        await show_btn.first.click()
                                        try:
                                            await page.wait_for_load_state("networkidle", timeout=8000)
                                        except Exception:
                                            pass
                                        await asyncio.sleep(0.5)
                                    except Exception as e:
                                        log_error(worker_id, f"Error clicking Show Sections for {course_code}: {e}")
                                        update_worker(worker_id, status="Error", current=f"Error clicking Show Sections: {e}", errors=1)
                    
                    parsed_frame = None
                    for f in page.frames:
                        try:
                            if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                                parsed_frame = f
                                break
                        except Exception:
                            pass
                            
                    if not parsed_frame:
                        await asyncio.sleep(2.7)
                        for f in page.frames:
                            try:
                                if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                                    parsed_frame = f
                                    break
                            except Exception:
                                pass
                                
                    if not parsed_frame:
                        update_worker(worker_id, status="Running", current=f"Could not find class section rows.")
                    else:
                        schedules = await parsed_frame.evaluate('''
                        () => {
                            const results = [];
                            const nameNodes = document.querySelectorAll("span[id^='CLASS_SECTION$span'] a");
                            
                            for (let node of nameNodes) {
                                const match = node.id.match(/\\$(\\d+)$/);
                                const idx = match ? match[1] : null;
                                if (!idx) continue;
                                
                                const section_name = node.innerText.trim();
                                const sessionNode = document.querySelector(`span[id='CLASS_SESSION$${idx}']`);
                                const session = sessionNode ? sessionNode.innerText.trim() : "";
                                const statusImg = document.querySelector(`div[id='win0divCLASS_STATUS$${idx}'] img`);
                                const status = statusImg ? statusImg.getAttribute("alt") : "";
                                
                                const details = [];
                                const detailRows = document.querySelectorAll(`tr[id^='trCLASS_MTGPAT$${idx}_row']`);
                                for (let dr of detailRows) {
                                    const getText = (prefix) => {
                                        const el = dr.querySelector(`span[id^='${prefix}']`);
                                        return el ? el.innerText.trim() : "";
                                    };
                                    details.push({
                                        days: getText("MTGPAT_DAYS$"),
                                        start_time: getText("MTGPAT_START$"),
                                        end_time: getText("MTGPAT_END$"),
                                        room: getText("MTGPAT_ROOM$"),
                                        instructor: getText("MTGPAT_INSTR$"),
                                        dates: getText("MTGPAT_DATES$")
                                    });
                                }
                                
                                results.push({
                                    section_name: section_name,
                                    session: session,
                                    status: status,
                                    details: details
                                });
                            }
                            return results;
                        }
                        ''')

                    
# if not # disabled section

                course_data = {
                    "course_code": course_code,
                    "course_title": course_title.strip(),
                    "term": term_label,
                    "sections": schedules
                }
                all_scraped_data.append(course_data)
                update_worker(worker_id, courses=1)

                # Save partial results
                with open(partial_path, "w") as f:
                    json.dump(all_scraped_data, f, indent=2)

                # Close the modal aggressively
                closed_modal = False
                
                # 1. Try to click the close anchor by class name anywhere on the page
                close_anchors = page.locator(".PSMODALCLOSEANCHOR")
                if await close_anchors.count() > 0:
                    try:
                        await close_anchors.last.click(force=True, timeout=5000)
                        closed_modal = True
                    except Exception:
                        pass
                
                # 2. Try falling back to looking in all frames
                if not closed_modal:
                    for f in page.frames:
                        close_btn = f.locator("a[id^='ptModCloseLnk']")
                        if await close_btn.count() > 0:
                            try:
                                await close_btn.last.click(force=True, timeout=5000)
                                closed_modal = True
                                break
                            except Exception:
                                pass

                # Wait for the modal close action to process / postback
                await asyncio.sleep(1.3)
                
                # 3. UNCONDITIONALLY run JS force-close and DOM cleanup to guarantee no leftover frames/masks intercept subsequent clicks
                await page.evaluate('''() => {
                    // Click close button if somehow still present
                    const closeBtns = document.querySelectorAll(".PSMODALCLOSEANCHOR");
                    if (closeBtns.length > 0) {
                        try { closeBtns[closeBtns.length - 1].click(); } catch(e) {}
                    }
                    
                    // Nuke the mask and modal container
                    const stuckMask = document.getElementById("pt_modalMask");
                    if (stuckMask) stuckMask.style.display = 'none';
                    
                    const stuckModal = document.getElementById("pt_modals");
                    if (stuckModal) {
                        stuckModal.style.display = 'none';
                        stuckModal.innerHTML = ''; // Delete any nested iframes completely
                    }
                }''')
                await asyncio.sleep(1.3)

                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                    
                frame = await get_peoplesoft_frame(page)

                elapsed_course = time.time() - course_start
                update_worker(worker_id, current=f"Course done in {_fmt_time(elapsed_course)}.")

                await asyncio.sleep(1.3)

            elapsed_letter = time.time() - letter_start
            update_worker(worker_id, current=f"Letter {letter} done in {_fmt_time(elapsed_letter)}.")

        elapsed_worker = time.time() - worker_start
        update_worker(worker_id, status="Finished", active="", current=f"Finished assignments {assignment_labels}. Scraped {len(all_scraped_data)} courses in {_fmt_time(elapsed_worker)}.")
        return all_scraped_data

    except Exception as e:
        log_error(worker_id, f"Fatal error during assignments {assignment_labels}: {e}")
        update_worker(worker_id, status="Error", current=f"Error occurred: {e}", errors=1)
        raise e
    finally:
        elapsed_worker = time.time() - worker_start
        update_worker(worker_id, current=f"Closing context...")
        try:
            await asyncio.wait_for(context.close(), timeout=3.0)
        except Exception:
            pass


async def scrape_term(browser: Browser, term_code: str, worker_assignments: List[List[Dict[str, int | str]]], existing_codes: Set[str] = None, title_code_map: Dict[str, str] = None, browser_visible: Browser = None, visible_letter: str = "") -> List[Dict[str, Any]]:
    """Run workers for a single term, return all course data for that term."""
    term_label = TERM_LABELS.get(term_code, term_code)
    console.print(f"\n{'='*60}")
    console.print(f"Starting scrape for term: {term_label} ({term_code})")
    console.print(f"{'='*60}")
    term_start = time.time()

    if existing_codes is None:
        existing_codes = set()
    if title_code_map is None:
        title_code_map = {}

    tasks = []
    for worker_id, assignments in enumerate(worker_assignments, start=1):
        worker_browser = browser
        if browser_visible and visible_letter:
            if any(str(a.get("letter", "")).upper() == visible_letter for a in assignments):
                worker_browser = browser_visible

        async def worker_task(browser_inst, w_id, assignment_group, t_code, exist_c, title_lookup):
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    res = await scrape_letters(browser_inst, w_id, assignment_group, t_code, exist_c, title_lookup)
                    update_worker(w_id, current=f"Done.", finished=True)
                    return res
                except Exception as e:
                    if attempt == max_retries - 1:
                        update_worker(w_id, status="Failed", current=f"Gave up after {max_retries} attempts.", finished=True)
                        partial_path = os.path.join(DATA_DIR, f"mosaic_schedules.worker_{w_id}_{t_code}.json")
                        try:
                            with open(partial_path, "r") as f:
                                return json.load(f)
                        except Exception:
                            return []
                    update_worker(w_id, status="Retrying", current=f"Crashed. Retrying in 5s... ({attempt+2}/{max_retries})", errors=1)
                    await asyncio.sleep(5)
                    
        tasks.append(
            asyncio.create_task(
                worker_task(worker_browser, worker_id, assignments, term_code, existing_codes, title_code_map)
            )
        )
        if len(worker_assignments) > 1:
            stagger = random.uniform(1.3, 6.7)
            console.print(f"Staggering worker {worker_id} launch by {stagger:.1f} seconds...")
            await asyncio.sleep(stagger)

    worker_results = await asyncio.gather(*tasks, return_exceptions=True)
    term_results = []
    for worker_id, chunk_results in enumerate(worker_results, start=1):
        if isinstance(chunk_results, Exception):
            log_error(worker_id, f"Worker task failed completely: {chunk_results}")
            update_worker(worker_id, status="Error", current=f"Failed: {chunk_results}", errors=1)
            continue
        if isinstance(chunk_results, list):
            term_results.extend(chunk_results)

    elapsed_term = time.time() - term_start
    console.print(f"Term {term_label} done. Scraped {len(term_results)} courses in {_fmt_time(elapsed_term)}.")
    return term_results


async def run(skip_existing: bool = False, letters: Optional[str] = None, courses_per_worker: int = 100):
    console.print("Starting Parallel Mosaic Scraper...")
    if skip_existing:
        console.print("[cyan]--skip-existing enabled: only courses without DB sections for each term will be scraped and appended.[/cyan]")
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "all_possible_schedules.json")
    
    selected_letters = parse_selected_letters(letters)
    title_code_map = load_course_title_code_map()
    worker_threshold = validate_courses_per_worker(courses_per_worker)
    append_output = True  # Always merge into existing files instead of overwriting
    if letters is not None:
        console.print(f"[cyan]Scraping selected letters only: {', '.join(selected_letters)}[/cyan]")
    
    # Fetch section coverage once, then use the term-specific set for each scrape.
    existing_codes_by_term: Dict[str, Set[str]] = {}
    if skip_existing:
        term_labels = [TERM_LABELS.get(term_code, term_code) for term_code in TARGET_TERMS]
        existing_codes_by_term = get_existing_section_codes_by_term(term_labels)

    console.print(f"Worker sizing: up to {worker_threshold} courses per worker.")
    console.print(f"Terms to scrape: {[TERM_LABELS.get(t, t) for t in TARGET_TERMS]}")

    run_start = time.time()
    with Live(get_renderable=generate_table, refresh_per_second=4, console=console) as live:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            visible_letter = os.getenv("VISIBLE_WORKER_LETTER", "").strip().upper()
            browser_visible = await p.chromium.launch(headless=False) if visible_letter else None
            try:
                all_terms_data = load_existing_schedule_output(output_path) if append_output else []

                for term_code in TARGET_TERMS:
                    term_label = TERM_LABELS.get(term_code, term_code)
                    existing_codes = existing_codes_by_term.get(term_label, set()) if skip_existing else set()
                    letter_counts = await count_courses_for_letters(browser, term_code, selected_letters)
                    worker_assignments = build_worker_assignments(selected_letters, letter_counts, worker_threshold)

                    worker_states.clear()
                    for i in range(1, len(worker_assignments) + 1):
                        update_worker(i)

                    console.print(f"{term_label}: counted {sum(letter_counts.values())} courses across {len(selected_letters)} letters; using {len(worker_assignments)} worker(s).")
                    if not worker_assignments:
                        term_results = []
                    else:
                        term_results = await scrape_term(browser, term_code, worker_assignments, existing_codes, title_code_map, browser_visible, visible_letter)

                    if append_output:
                        all_terms_data = merge_term_results(all_terms_data, term_label, term_results)
                    else:
                        all_terms_data.append({
                            "term": term_label,
                            "courses": term_results
                        })

                    # Save incremental progress after each term
                    with open(output_path, "w") as f:
                        json.dump(all_terms_data, f, indent=2)
                    console.print(f"Saved progress after {term_label}.")

                with open(output_path, "w") as f:
                    json.dump(all_terms_data, f, indent=2)
                
                cleanup_worker_files("mosaic_schedules")
                elapsed_total = time.time() - run_start
                total_courses = sum(len(t["courses"]) for t in all_terms_data)
                console.print(f"\nDone. Saved {total_courses} courses across {len(all_terms_data)} terms to {output_path}")
                console.print(f"Total time: {_fmt_time(elapsed_total)}")

            finally:
                console.print("Closing browser...")
                await browser.close()
                if browser_visible:
                    await browser_visible.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Mosaic course schedules")
    parser.add_argument(
        "--skip-existing",
        "--missing-sections-only",
        action="store_true",
        dest="skip_existing",
        help="Skip courses whose code already has sections in the database for the target term",
    )
    parser.add_argument(
        "--letters",
        help="Only scrape course-code prefixes matching these letters, e.g. C,D or CD. Selected-letter runs append/merge into the existing output.",
    )
    parser.add_argument(
        "--courses-per-worker",
        default=100,
        help="Maximum course count assigned to each worker after the per-letter count pass. Defaults to 100.",
    )
    parser.add_argument(
        "--terms",
        help="Comma-separated list of term codes to scrape, e.g. 2269,2271. Overrides the default TARGET_TERMS.",
    )
    args = parser.parse_args()
    try:
        parse_selected_letters(args.letters)
        courses_per_worker = validate_courses_per_worker(args.courses_per_worker)
        if args.terms:
            TARGET_TERMS = [t.strip() for t in args.terms.split(",") if t.strip()]
    except ValueError as e:
        parser.error(str(e))
    asyncio.run(run(skip_existing=args.skip_existing, letters=args.letters, courses_per_worker=courses_per_worker))
