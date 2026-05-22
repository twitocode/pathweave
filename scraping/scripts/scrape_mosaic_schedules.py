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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

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
            print(f"Warning: failed to remove worker file {path}: {e}")

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
    print(f"[Worker {worker_id}] Starting for letters: {letters}")
    context = await browser.new_context()
    page = await context.new_page()
    all_scraped_data = []
    term_label = TERM_LABELS.get(term_code, term_code)
    partial_path = os.path.join(DATA_DIR, f"mosaic_schedules.worker_{worker_id}_{term_code}.json")

    try:
        print(f"[Worker {worker_id}] Navigating to Mosaic login...")
        await page.goto("https://mosaic.mcmaster.ca/psp/prcsprd/?cmd=login")

        print(f"[Worker {worker_id}] Logging in...")
        await page.fill("#userid", MOSAIC_USERNAME or "")
        await page.fill("#pwd", MOSAIC_PASSWORD or "")
        # Increase timeout dramatically for the login step
        await page.click("input[name='Submit']", timeout=90000)
        
        try:
            await page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass # sometimes networkidle never fires on Peoplesoft, we rely on the next visible locator anyway

        print(f"[Worker {worker_id}] Waiting for Student Center...")
        student_center_div = page.locator("#win0divPTNUI_LAND_REC_GROUPLET\\$8")
        await student_center_div.wait_for(state="visible", timeout=90000)
        await student_center_div.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(3)
        frame = await get_peoplesoft_frame(page)

        print(f"[Worker {worker_id}] Clicking Course Search...")
        search_link = frame.locator("#DERIVED_SSS_SCR_SSS_LINK_ANCHOR1")
        await search_link.wait_for(state="visible", timeout=15000)
        await search_link.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(2)
        frame = await get_peoplesoft_frame(page)

        print(f"[Worker {worker_id}] Clicking Browse Course Catalog...")
        browse_link = frame.locator("text=Browse Course Catalog")
        await browse_link.wait_for(state="visible", timeout=15000)
        await browse_link.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(2)
        frame = await get_peoplesoft_frame(page)

        print(f"[Worker {worker_id}] Selecting Career and Term...")
        career_select = frame.locator("#MCM_SSS_BCC_WRK_ACAD_CAREER")
        await career_select.wait_for(state="visible", timeout=15000)
        await career_select.select_option("UGRD")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        frame = await get_peoplesoft_frame(page)

        term_select = frame.locator("#MCM_SSS_BCC_WRK_STRM")
        await term_select.wait_for(state="visible", timeout=15000)
        await term_select.select_option(term_code)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        frame = await get_peoplesoft_frame(page)

        print(f"[Worker {worker_id}] Executing Search...")
        search_btn = frame.locator("#MCM_SSS_BCC_WRK_SSS_PB_CHANGE")
        await search_btn.wait_for(state="visible", timeout=15000)
        await search_btn.click()
        await page.wait_for_load_state("networkidle")

        await asyncio.sleep(3)
        frame = await get_peoplesoft_frame(page)

        for letter in letters:
            letter_start = time.time()
            print(f"[Worker {worker_id}] Filtering by letter {letter}...")
            letter_btn = frame.locator(f"#DERIVED_SSS_BCC_SSR_ALPHANUM_{letter}")
            
            if await letter_btn.count() == 0 or not await letter_btn.first.is_visible():
                print(f"[Worker {worker_id}] Letter {letter} not available.")
                continue

            await letter_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            frame = await get_peoplesoft_frame(page)

            print(f"[Worker {worker_id}] Expanding all courses for {letter}...")
            expand_btn = frame.locator("#DERIVED_SSS_BCC_SSS_EXPAND_ALL\\$97\\$")
            if await expand_btn.count() > 0 and await expand_btn.first.is_visible():
                await expand_btn.first.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                frame = await get_peoplesoft_frame(page)
            
            course_index = 0
            while True:
                course_link = frame.locator(f"#CRSE_TITLE\\${course_index}")
                if not await course_link.is_visible():
                    break

                course_title = await course_link.inner_text()
                course_start = time.time()
                print(f"[Worker {worker_id}] Clicking course: {course_title.strip()}")
                await course_link.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

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
                    print(f"[Worker {worker_id}] Could not locate modal buttons.")
                elif is_not_scheduled:
                    print(f"[Worker {worker_id}] Course not scheduled.")
                else:
                    try:
                        await view_sections_btn.click()
                    except Exception as e:
                        print(f"[Worker {worker_id}] Error clicking view sections: {e}")
                    
                    await asyncio.sleep(4)
                    
                    parsed_frame = None
                    for f in page.frames:
                        try:
                            if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                                parsed_frame = f
                                break
                        except Exception:
                            pass
                            
                    if not parsed_frame:
                        await asyncio.sleep(3)
                        for f in page.frames:
                            try:
                                if await f.locator("tr[id^='trCLASS\\$']").count() > 0:
                                    parsed_frame = f
                                    break
                            except Exception:
                                pass
                                
                    if not parsed_frame:
                        print(f"[Worker {worker_id}] Could not find class section rows.")
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

                    course_title_clean = course_title.split(" - ")[0].strip()
                    
                    if not HEADLESS:
                        print(f"\n[Worker {worker_id}] Scraped Sections for {course_title_clean}:")
                        print(f"{'Section':<15} | {'Days':<10} | {'Start':<8} | {'End':<8} | {'Room':<25} | {'Instructor':<20}")
                        print("-" * 95)
                        for sec in schedules:
                            sec_name = sec["section_name"].split(" ")[0]
                            if not sec["details"]:
                                print(f"{sec_name:<15} | {'N/A':<10} | {'N/A':<8} | {'N/A':<8} | {'N/A':<25} | {'N/A':<20}")
                            else:
                                for i, d in enumerate(sec["details"]):
                                    s_name = sec_name if i == 0 else ""
                                    days = d.get("days", "")
                                    start = d.get("start_time", "")
                                    end = d.get("end_time", "")
                                    room = d.get("room", "")[:24]
                                    instr = d.get("instructor", "")[:19]
                                    print(f"{s_name:<15} | {days:<10} | {start:<8} | {end:<8} | {room:<25} | {instr:<20}")
                        print("\n")

                    course_data = {
                        "course_code": course_title_clean,
                        "term": term_label,
                        "sections": schedules
                    }
                    all_scraped_data.append(course_data)

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

                # Wait for the modal to visually disappear
                await asyncio.sleep(2)
                
                # 3. If mask is still intercepting, try Escape key or JS force-close
                mask = page.locator("#pt_modalMask")
                if await mask.count() > 0 and await mask.first.is_visible():
                    print(f"[Worker {worker_id}] Modal mask still visible, attempting Escape key...")
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(2)
                    
                    if await mask.first.is_visible():
                        print(f"[Worker {worker_id}] Modal mask STILL visible, using JS override...")
                        await page.evaluate('''() => {
                            const closeBtns = document.querySelectorAll(".PSMODALCLOSEANCHOR");
                            if (closeBtns.length > 0) closeBtns[closeBtns.length - 1].click();
                            
                            // Nuke the mask if it's completely stuck
                            const stuckMask = document.getElementById("pt_modalMask");
                            if (stuckMask) stuckMask.style.display = 'none';
                            
                            const stuckModal = document.getElementById("pt_modals");
                            if (stuckModal) stuckModal.style.display = 'none';
                        }''')
                        await asyncio.sleep(1)

                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                    
                frame = await get_peoplesoft_frame(page)

                elapsed_course = time.time() - course_start
                print(f"[Worker {worker_id}] Course done in {_fmt_time(elapsed_course)}.")

                await asyncio.sleep(1)
                course_index += 1

            elapsed_letter = time.time() - letter_start
            print(f"[Worker {worker_id}] Letter {letter} done in {_fmt_time(elapsed_letter)}.")

        elapsed_worker = time.time() - worker_start
        print(f"[Worker {worker_id}] Finished letters {letters}. Scraped {len(all_scraped_data)} courses in {_fmt_time(elapsed_worker)}.")
        return all_scraped_data

    except Exception as e:
        print(f"[Worker {worker_id}] Error occurred: {e}")
        return all_scraped_data
    finally:
        print(f"[Worker {worker_id}] Closing context...")
        await context.close()


async def scrape_term(browser: Browser, term_code: str, chunks: List[List[str]]) -> List[Dict[str, Any]]:
    """Run 13 workers for a single term, return all course data for that term."""
    term_label = TERM_LABELS.get(term_code, term_code)
    print(f"\n{'='*60}")
    print(f"Starting scrape for term: {term_label} ({term_code})")
    print(f"{'='*60}")
    term_start = time.time()

    tasks = []
    for worker_id, chunk in enumerate(chunks, start=1):
        tasks.append(
            asyncio.create_task(
                scrape_letters(browser, worker_id, chunk, term_code)
            )
        )
        stagger = random.uniform(3, 15)
        print(f"Staggering worker {worker_id} launch by {stagger:.1f} seconds...")
        await asyncio.sleep(stagger)

    worker_results = await asyncio.gather(*tasks, return_exceptions=True)
    term_results = []
    for worker_id, chunk_results in enumerate(worker_results, start=1):
        if isinstance(chunk_results, Exception):
            print(f"[Worker {worker_id}] Failed: {chunk_results}")
            continue
        if isinstance(chunk_results, list):
            term_results.extend(chunk_results)

    elapsed_term = time.time() - term_start
    print(f"Term {term_label} done. Scraped {len(term_results)} courses in {_fmt_time(elapsed_term)}.")
    return term_results


async def run():
    print("Starting Parallel Mosaic Scraper...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Chunk alphabet into 13 workers, 2 letters each
    alphabet = list(string.ascii_uppercase)
    chunk_size = 2
    chunks = [alphabet[i:i+chunk_size] for i in range(0, len(alphabet), chunk_size)]
    
    print(f"Divided alphabet into {len(chunks)} chunks for 13 workers.")
    print(f"Terms to scrape: {[TERM_LABELS.get(t, t) for t in TARGET_TERMS]}")

    run_start = time.time()
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
                print(f"Saved progress after {term_label}.")

            output_path = os.path.join(DATA_DIR, "all_possible_schedules.json")
            with open(output_path, "w") as f:
                json.dump(all_terms_data, f, indent=2)
            
            cleanup_worker_files("mosaic_schedules")
            elapsed_total = time.time() - run_start
            total_courses = sum(len(t["courses"]) for t in all_terms_data)
            print(f"\nDone. Saved {total_courses} courses across {len(all_terms_data)} terms to {output_path}")
            print(f"Total time: {_fmt_time(elapsed_total)}")

        finally:
            print("Closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())