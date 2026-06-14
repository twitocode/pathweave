import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://academiccalendars.romcmaster.ca/content.php?catoid=65&navoid=14802&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=28#acalog_template_course_filter"
        await page.goto(url)
        
        course_links = await page.evaluate("""
            () => Array.from(document.querySelectorAll("a[onclick^='showCourse']")).map(a => {
                const match = a.getAttribute('onclick').match(/showCourse\('(\d+)',\s*'(\d+)'/);
                return { text: a.innerText.trim(), coid: match ? match[2] : null };
            }).filter(item => item.coid !== null)
        """)
        
        print(f"Found {len(course_links)} courses")
        if course_links:
            first = course_links[0]
            print(f"First course: {first}")
            
            preview_url = f"https://academiccalendars.romcmaster.ca/ajax/preview_course.php?catoid=65&show&coid={first['coid']}"
            resp = await context.request.get(preview_url)
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text[:200]}")
        
        await browser.close()

asyncio.run(main())
