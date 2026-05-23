import asyncio
import os
import string
import itertools
import json
import time
import random
from glob import glob
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Frame, Browser
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

console = Console()
worker_states = {}

def update_worker(worker_id: int, status: str = None, current: str = None, courses: int = None, total_courses: int = None, errors: int = None, started: bool = False, finished: bool = False, reset: bool = False):
    if worker_id not in worker_states or reset:
        worker_states[worker_id] = {"status": "Waiting...", "current": "", "courses": 0, "total_courses": 0, "errors": 0, "start_time": None, "end_time": None}
    
    state = worker_states[worker_id]
    if status is not None: state["status"] = status
    if current is not None: state["current"] = current
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
    table.add_column("Current Task", width=50)
    table.add_column("Courses", justify="right")
    table.add_column("Errors", justify="right", style="red")
    table.add_column("Time", justify="right", style="cyan")

    for w_id in sorted(worker_states.keys()):
        state = worker_states[w_id]
        t = _fmt_time(_worker_elapsed(state))
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

TARGET_TERMS = ["2269", "2271", "2275"]

TERM_LABELS = {
    "2259": "Fall 2025",
    "2261": "Winter 2026",
    "2265": "Spring/Summer 2026",
    "2269": "Fall 2026",
    "2271": "Winter 2027",
    "2275": "Spring/Summer 2027",
}

def cleanup_worker_files(prefix: str) -> None:
    pattern = os.path.join(DATA_DIR, f"{prefix}.worker_*.json")
    for path in glob(pattern):
        try:
            os.remove(path)
        except Exception as e:
            console.print(f"Warning: failed to remove worker file {path}: {e}")

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


async def scrape_letters(browser: Browser, worker_id: int, letters: List[str], term_code: str) -> List[Dict[str, Any]]:
    worker_start = time.time()
    update_worker(worker_id, status="Starting", current=f"Starting for letters: {letters}", started=True, reset=True)
    context = await browser.new_context()
    page = await context.new_page()
    all_scraped_data = []
    term_label = TERM_LABELS.get(term_code, term_code)
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
        update_worker(worker_id, status="Logging In", current=f"Navigating to Mosaic login...")
        await page.goto("https://mosaic.mcmaster.ca/psp/prcsprd/?cmd=login")

        update_worker(worker_id, status="Logging In", current=f"Logging in...")
        await page.fill("#userid", MOSAIC_USERNAME or "")
        await page.fill("#pwd", MOSAIC_PASSWORD or "")
        # Increase timeout dramatically for the login step
        await page.click("input[name='Submit']", timeout=90000)
        
        try:
            await page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass # sometimes networkidle never fires on Peoplesoft, we rely on the next visible locator anyway

        update_worker(worker_id, status="Navigating", current=f"Waiting for Student Center...")
        student_center_div = page.locator("#win0divPTNUI_LAND_REC_GROUPLET\\$8")
        await student_center_div.wait_for(state="visible", timeout=90000)
        await student_center_div.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(5)
        frame = await get_peoplesoft_frame(page)

        update_worker(worker_id, status="Navigating", current=f"Clicking Course Search...")
        search_link = frame.locator("#DERIVED_SSS_SCR_SSS_LINK_ANCHOR1")
        await search_link.wait_for(state="visible", timeout=15000)
        await search_link.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(5)
        frame = await get_peoplesoft_frame(page)

        update_worker(worker_id, status="Navigating", current=f"Clicking Browse Course Catalog...")
        browse_link = frame.locator("text=Browse Course Catalog")
        await browse_link.wait_for(state="visible", timeout=15000)
        await browse_link.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(5)
        frame = await get_peoplesoft_frame(page)

        update_worker(worker_id, status="Filtering", current=f"Selecting Career and Term...")
        career_select = frame.locator("#MCM_SSS_BCC_WRK_ACAD_CAREER")
        await career_select.wait_for(state="visible", timeout=15000)
        await career_select.select_option("UGRD")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        frame = await get_peoplesoft_frame(page)

        term_select = frame.locator("#MCM_SSS_BCC_WRK_STRM")
        await term_select.wait_for(state="visible", timeout=15000)
        await term_select.select_option(term_code)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        frame = await get_peoplesoft_frame(page)

        update_worker(worker_id, status="Searching", current=f"Executing Search...")
        search_btn = frame.locator("#MCM_SSS_BCC_WRK_SSS_PB_CHANGE")
        await search_btn.wait_for(state="visible", timeout=15000)
        await search_btn.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(6)
        frame = await get_peoplesoft_frame(page)

        for letter in letters:
            letter_start = time.time()
            update_worker(worker_id, status="Filtering", current=f"Filtering by letter {letter}...")
            letter_btn = frame.locator(f"#DERIVED_SSS_BCC_SSR_ALPHANUM_{letter}")
            
            if await letter_btn.count() == 0 or not await letter_btn.first.is_visible():
                update_worker(worker_id, status="Running", current=f"Letter {letter} not available.")
                continue

            await letter_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(6)
            frame = await get_peoplesoft_frame(page)

            update_worker(worker_id, status="Filtering", current=f"Expanding all courses for {letter}...")
            expand_btn = frame.locator("#DERIVED_SSS_BCC_SSS_EXPAND_ALL\\$97\\$")
            if await expand_btn.count() > 0 and await expand_btn.first.is_visible():
                await expand_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(6)
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
                await asyncio.sleep(2)

            course_links = frame.locator("a[id^='CRSE_TITLE$']")
            course_count = await course_links.count()
            update_worker(worker_id, total_courses=course_count)
            
            for i in range(course_count):
                # Wait for the DOM to recover in case PeopleSoft did a postback after the modal closed
                recovered = False
                for _ in range(10):
                    course_links = frame.locator("a[id^='CRSE_TITLE$']")
                    if await course_links.count() >= course_count:
                        recovered = True
                        break
                    await asyncio.sleep(2)
                
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
                course_code = f"{subject} {course_nbr}".strip() if subject and course_nbr else course_title.strip()
                
                # Skip if already scraped in a previous run
                if any(c.get("course_code") == course_code for c in all_scraped_data):
                    # We still count it towards total courses processed, but don't re-scrape
                    update_worker(worker_id, status="Running", current=f"Skipping already scraped: {course_code}")
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
                await asyncio.sleep(5)

                modal_frame = None
                view_sections_btn = None
                is_not_scheduled = False

                for f in page.frames:
                    btn = f.locator("#DERIVED_SAA_CRS_SSR_PB_GO")
                    if await btn.count() > 0 and await btn.first.is_visible():
                        view_sections_btn = btn.first
                        modal_frame = f
                        break

                    not_scheduled = f.locator("text=This course has not been scheduled.")
                    if await not_scheduled.count() > 0 and await not_scheduled.first.is_visible():
                        is_not_scheduled = True
                        modal_frame = f
                        break

                schedules = []

                if not modal_frame:
                    update_worker(worker_id, status="Running", current=f"Could not locate modal buttons.")
                elif is_not_scheduled:
                    update_worker(worker_id, status="Running", current=f"Course not scheduled.")
                else:
                    try:
                        await view_sections_btn.click()
                    except Exception as e:
                        log_error(worker_id, f"Error clicking view sections for course {course_code}: {e}")
                        update_worker(worker_id, status="Error", current=f"Error clicking view sections: {e}", errors=1)
                    
                    await asyncio.sleep(8)
                    
                    parsed_frame = None
                    for f in page.frames:
                        try:
                            if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                                parsed_frame = f
                                break
                        except Exception:
                            pass
                            
                    if not parsed_frame:
                        await asyncio.sleep(6)
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
                await asyncio.sleep(3)
                
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
                await asyncio.sleep(3)

                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                    
                frame = await get_peoplesoft_frame(page)

                elapsed_course = time.time() - course_start
                update_worker(worker_id, current=f"Course done in {_fmt_time(elapsed_course)}.")

                await asyncio.sleep(3)

            elapsed_letter = time.time() - letter_start
            update_worker(worker_id, current=f"Letter {letter} done in {_fmt_time(elapsed_letter)}.")

        elapsed_worker = time.time() - worker_start
        update_worker(worker_id, status="Finished", current=f"Finished letters {letters}. Scraped {len(all_scraped_data)} courses in {_fmt_time(elapsed_worker)}.")
        return all_scraped_data

    except Exception as e:
        log_error(worker_id, f"Fatal error during letter chunk {letters}: {e}")
        update_worker(worker_id, status="Error", current=f"Error occurred: {e}", errors=1)
        return all_scraped_data
    finally:
        elapsed_worker = time.time() - worker_start
        update_worker(worker_id, current=f"Closing context...")
        try:
            await asyncio.wait_for(context.close(), timeout=3.0)
        except Exception:
            pass
        update_worker(worker_id, current=f"Done.", finished=True)


async def scrape_term(browser: Browser, term_code: str, chunks: List[List[str]]) -> List[Dict[str, Any]]:
    """Run 13 workers for a single term, return all course data for that term."""
    term_label = TERM_LABELS.get(term_code, term_code)
    console.print(f"\n{'='*60}")
    console.print(f"Starting scrape for term: {term_label} ({term_code})")
    console.print(f"{'='*60}")
    term_start = time.time()

    tasks = []
    for worker_id, chunk in enumerate(chunks, start=1):
        tasks.append(
            asyncio.create_task(
                scrape_letters(browser, worker_id, chunk, term_code)
            )
        )
        stagger = random.uniform(3, 15)
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


async def run():
    console.print("Starting Parallel Mosaic Scraper...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Chunk alphabet into 13 workers, 2 letters each
    alphabet = list(string.ascii_uppercase)
    chunk_size = 2
    chunks = [alphabet[i:i+chunk_size] for i in range(0, len(alphabet), chunk_size)]
    
    console.print(f"Divided alphabet into {len(chunks)} chunks for 13 workers.")
    console.print(f"Terms to scrape: {[TERM_LABELS.get(t, t) for t in TARGET_TERMS]}")

    run_start = time.time()
    for i in range(1, 14): update_worker(i) # init workers
    with Live(get_renderable=generate_table, refresh_per_second=4, console=console) as live:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            try:
                all_terms_data = []

                for term_code in TARGET_TERMS:
                    term_label = TERM_LABELS.get(term_code, term_code)
                    term_results = await scrape_term(browser, term_code, chunks)

                    all_terms_data.append({
                        "term": term_label,
                        "courses": term_results
                    })

                    # Save incremental progress after each term
                    progress_path = os.path.join(DATA_DIR, "all_possible_schedules.json")
                    with open(progress_path, "w") as f:
                        json.dump(all_terms_data, f, indent=2)
                    console.print(f"Saved progress after {term_label}.")

                output_path = os.path.join(DATA_DIR, "all_possible_schedules.json")
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

if __name__ == "__main__":
    asyncio.run(run())