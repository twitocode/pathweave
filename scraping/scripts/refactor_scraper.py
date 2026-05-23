import re
import os

SCRIPT_PATH = "/Users/twito/Documents/Code/projects/PathWeave/scraping/scripts/scrape_mosaic_schedules.py"

with open(SCRIPT_PATH, "r") as f:
    code = f.read()

# Add rich imports
imports = """from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

console = Console()
worker_states = {}

def update_worker(worker_id: int, status: str = None, current: str = None, courses: int = None, errors: int = None, time_elapsed: float = None):
    if worker_id not in worker_states:
        worker_states[worker_id] = {"status": "Waiting...", "current": "", "courses": 0, "errors": 0, "time": 0.0}
    
    state = worker_states[worker_id]
    if status is not None: state["status"] = status
    if current is not None: state["current"] = current
    if courses is not None: state["courses"] += courses
    if errors is not None: state["errors"] += errors
    if time_elapsed is not None: state["time"] = time_elapsed

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
        t = _fmt_time(state["time"])
        cur = state["current"]
        if len(cur) > 48: cur = cur[:45] + "..."
        table.add_row(
            f"Worker {w_id}", 
            state["status"], 
            cur, 
            str(state["courses"]), 
            str(state["errors"]), 
            t
        )
    return table
"""

code = code.replace("from playwright.async_api import async_playwright, Page, Frame, Browser", 
                    "from playwright.async_api import async_playwright, Page, Frame, Browser\n" + imports)

# Replace [Worker {worker_id}] prints
def repl_worker_print(m):
    content = m.group(1)
    status = '"Running"'
    if 'Starting' in content: status = '"Starting"'
    elif 'login' in content or 'Logging' in content: status = '"Logging In"'
    elif 'Student Center' in content: status = '"Navigating"'
    elif 'Clicking' in content: status = '"Navigating"'
    elif 'Selecting' in content: status = '"Filtering"'
    elif 'Search' in content: status = '"Searching"'
    elif 'Filtering' in content or 'Expanding' in content: status = '"Filtering"'
    elif 'Built course map' in content or 'Built course code map' in content: status = '"Parsing"'
    elif 'courses in' in content and 'Finished' in content: status = '"Finished"'
    elif 'Error' in content or 'Failed' in content: status = '"Error"'
    
    if status == '"Finished"':
        return f'update_worker(worker_id, status={status}, current=f"{content}", time_elapsed=elapsed_worker)'
    elif status == '"Error"':
        return f'update_worker(worker_id, status={status}, current=f"{content}", errors=1)'
    elif 'done in' in content and 'Letter' not in content and 'Finished' not in content:
        # course done
        return f'update_worker(worker_id, current=f"{content}")'
    elif 'Letter' in content and 'done' in content:
        return f'update_worker(worker_id, current=f"{content}")'
    
    return f'update_worker(worker_id, status={status}, current=f"{content}")'

code = re.sub(r'print\(f"\[Worker \{worker_id\}\] (.*?)"\)', repl_worker_print, code)

# Track courses
code = code.replace('all_scraped_data.append(course_data)', 'all_scraped_data.append(course_data)\n                    update_worker(worker_id, courses=1)')

# Mute the HEADLESS section printing which breaks table
code = re.sub(r'(if not HEADLESS:\n(\s+)print\(f"\\n\[Worker \{worker_id\}\] Scraped.*?print\("\\n"\))', r'\n# \1 (disabled to preserve live table)', code, flags=re.DOTALL)

# Handle run()
run_old = '''    run_start = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        try:
            all_terms_data = []

            for term_code in TARGET_TERMS:'''

run_new = '''    run_start = time.time()
    for i in range(1, 14): update_worker(i) # init workers
    with Live(get_renderable=generate_table, refresh_per_second=4, console=console) as live:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            try:
                all_terms_data = []

                for term_code in TARGET_TERMS:'''
code = code.replace(run_old, run_new)

# Handle other prints by replacing with console.print or leaving as is? 
# Wait, print() inside the Live context might glitch it.
# We shouldn't use regular print while Live is running.
code = re.sub(r'print\((.*?)\)', r'console.print(\1)', code)

with open(SCRIPT_PATH, "w") as f:
    f.write(code)

print("Refactored script successfully.")
