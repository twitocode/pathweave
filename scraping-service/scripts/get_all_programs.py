import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Limit concurrent requests
MAX_CONCURRENT_REQUESTS = 10

async def fetch_program_requirements(context, url, name, semaphore):
    async with semaphore:
        try:
            page = await context.new_page()
            # Navigate to the program page
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Extract course codes from the page
            # Course codes are usually in links with showCourse('catoid', 'coid')
            # or just as text like 'ANTHROP 2PA3'
            
            # We'll use a locator to find all showCourse links
            course_codes = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll("a[onclick^='showCourse']"));
                    return [...new Set(links.map(a => a.innerText.trim()))];
                }
            """)
            
            # If no showCourse links, try to find text matching course code pattern
            if not course_codes:
                 content = await page.inner_text(".block_content")
                 # Pattern like 'ANTHROP 2PA3' or 'ABLD 3A03'
                 pattern = r"\b[A-Z]{2,10}\s\d[A-Z0-9]{2,4}\b"
                 course_codes = list(set(re.findall(pattern, content)))

            await page.close()
            print(f"Scraped {name}: {len(course_codes)} courses found.", end="\r")
            return {
                "program_name": name,
                "url": url,
                "requirements": sorted(course_codes)
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
