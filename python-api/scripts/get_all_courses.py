import asyncio
import json
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Limit concurrent requests to avoid overwhelming the server
MAX_CONCURRENT_REQUESTS = 10

async def fetch_and_parse_course(context, base_url, item, semaphore):
    async with semaphore:
        coid = item['coid']
        try:
            response = await context.request.get(base_url + coid)
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
            
            # 1. Prerequisite extraction
            prereq_tag = soup.find("strong", string=lambda t: t and "Prerequisite" in t)
            if not prereq_tag:
                prereq_tag = soup.find(lambda tag: tag.name == "strong" and "Prerequisite" in tag.text)

            if prereq_tag:
                p_html_parts = []
                curr = prereq_tag.next_sibling
                while curr:
                    if hasattr(curr, 'name') and curr.name in ['br', 'hr']:
                        break
                    p_html_parts.append(str(curr))
                    curr = curr.next_sibling
                
                full_p_html = "".join(p_html_parts)
                p_soup = BeautifulSoup(f"<span>{full_p_html}</span>", "html.parser")
                clean_p_text = p_soup.get_text().strip().lstrip(":").strip()
                prerequisites = [x.strip().strip(".") for x in clean_p_text.split(",") if x.strip()]

            # 2. Description and New Fields Extraction
            hr = soup.find("hr")
            if hr:
                desc_parts = []
                curr = hr.next_sibling
                while curr:
                    if curr == prereq_tag:
                        break
                    desc_parts.append(str(curr))
                    curr = curr.next_sibling
                
                raw_desc = "".join(desc_parts).strip()
                # Get text with space separator to keep it readable for regex
                full_text = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()
                # Clean up multiple spaces and weird characters
                full_text = re.sub(r'\s+', ' ', full_text)

                # Extraction Patterns
                rec_pattern = r"([^.]*?\b(?:is|are|is strongly)\s+recommended\.)"
                # Restrictions: Not open to... or Antirequisite...
                rest_pattern = r"((?:Not open to students|Antirequisite\(s\):).*?(\.|$))"
                # Lectures boilerplate
                lecture_pattern = r"Lectures\s*\(.*?\)\s*;\s*.*?(?:\.|$)"

                # Extract Recommended
                rec_match = re.search(rec_pattern, full_text, re.IGNORECASE)
                if rec_match:
                    recommended = rec_match.group(0).strip()
                    full_text = full_text.replace(recommended, "")

                # Extract Restrictions
                rest_match = re.search(rest_pattern, full_text, re.IGNORECASE)
                if rest_match:
                    restrictions = rest_match.group(0).strip()
                    full_text = full_text.replace(restrictions, "")

                # Filter out Lectures boilerplate
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

async def scrape_courses():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        catoid = "58"
        base_preview_url = f"https://academiccalendars.romcmaster.ca/ajax/preview_course.php?catoid={catoid}&show&coid="
        url = f"https://academiccalendars.romcmaster.ca/content.php?catoid={catoid}&navoid=12627"
        
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="networkidle")

        scraped_data = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        # Limited to 2 pages for testing as requested
        for page_num in range(1, 34):
            print(f"\n--- Processing Page {page_num} ---")
            
            try:
                await page.wait_for_selector("a[onclick^='showCourse']", timeout=15000)
            except Exception:
                print("No course links found.")
                break
            
            course_links = await page.evaluate("""
                () => Array.from(document.querySelectorAll("a[onclick^='showCourse']")).map(a => {
                    const match = a.getAttribute('onclick').match(/showCourse\\('(\\d+)',\\s*'(\\d+)'/);
                    return {
                        text: a.innerText.trim(),
                        coid: match ? match[2] : null
                    };
                }).filter(item => item.coid !== null)
            """)

            print(f"Found {len(course_links)} courses. Fetching in parallel...")

            tasks = [fetch_and_parse_course(context, base_preview_url, item, semaphore) for item in course_links]
            page_results = await asyncio.gather(*tasks)
            valid_results = [r for r in page_results if r is not None]
            scraped_data.extend(valid_results)

            print(f"Page {page_num} finished. Scraped {len(valid_results)} courses. Total so far: {len(scraped_data)}")

            if page_num < 2:
                next_page = page_num + 1
                print(f"Moving to page {next_page}...")
                next_btn = page.locator(f"a:text-is('{next_page}')").first
                if await next_btn.count() == 0:
                    next_btn = page.locator(f"a[aria-label='Page {next_page}']").first
                
                if await next_btn.count() > 0:
                    first_text = (await page.locator("a[onclick^='showCourse']").first.inner_text()).strip()
                    await next_btn.click()
                    
                    for _ in range(50):
                        await asyncio.sleep(0.2)
                        try:
                            new_text = (await page.locator("a[onclick^='showCourse']").first.inner_text()).strip()
                            if new_text != first_text:
                                break
                        except:
                            pass
                else:
                    break

        await browser.close()
        
        output_file = "data/all_courses.json"
        with open(output_file, "w") as f:
            json.dump(scraped_data, f, indent=2)
            
        print(f"\nSuccess! Scraped {len(scraped_data)} courses across 2 pages.")
        print(f"Data saved to {output_file}")
        return scraped_data

if __name__ == "__main__":
    asyncio.run(scrape_courses())
