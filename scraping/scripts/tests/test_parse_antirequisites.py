"""Quick test of the new parsing logic against real HTML samples."""
from bs4 import BeautifulSoup
import re
import sys
import os

# Import the scraper module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simulate the parsing logic (copied from get_all_courses.py)
def parse_course_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    course_name = ""
    h3 = soup.find("h3")
    if h3:
        course_name = h3.get_text(strip=True)

    units = ""
    unit_match = re.search(r"(\d+)\s*unit\(s\)", soup.get_text())
    if unit_match:
        units = unit_match.group(0)

    description = ""
    prerequisites = []
    recommended = ""
    restrictions = ""

    def find_label_tag(soup, label):
        for tag_name in ["strong", "b"]:
            tag = soup.find(tag_name, string=lambda t: t and label in t)
            if tag:
                return tag
            tag = soup.find(lambda t: t.name == tag_name and label in t.get_text())
            if tag:
                return tag
        return None

    def extract_text_after_tag(tag):
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

    prereq_tag = find_label_tag(soup, "Prerequisite")
    if prereq_tag:
        clean_p_text = extract_text_after_tag(prereq_tag)
        prerequisites = [x.strip().strip(".") for x in clean_p_text.split(",") if x.strip()]

    restriction_parts = []
    antireq_tag = find_label_tag(soup, "Antirequisite")
    if antireq_tag:
        antireq_text = extract_text_after_tag(antireq_tag)
        if antireq_text:
            restriction_parts.append(f"Antirequisite(s): {antireq_text}")

    hr = soup.find("hr")
    if hr:
        desc_parts = []
        curr = hr.next_sibling
        while curr:
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
        description = full_text.strip()

    return {
        "course_name": course_name,
        "units": units,
        "description": description,
        "prerequisites": prerequisites,
        "recommended": recommended,
        "restrictions": restrictions,
    }


# Test 1: COMPSCI 1DM3 with <b> tags (from user's HTML)
html_1dm3 = """
<div><h3>COMPSCI 1DM3 - Discrete Mathematics for Computer Science </h3>    3 unit(s) <br><hr>Sets, functions, relations, trees and graphs; counting principles, modular arithmetic, discrete probabilities; induction and recursion, recurrence relations.<br>Three lectures, one tutorial (two hours), second term<br><b>Prerequisite(s):</b> One of the following:<br>  • Registration in Computer Science 1 and one of MATH 1B03, 1ZC3<br>  • One of MATH 1B03, 1ZC3 with a result of at least B<br><b>Antirequisite(s):</b> COMPSCI 1FC3, 2DM3, SFWRENG 2DM3, 2E03, 2F03<br></div>
"""

# Test 2: COMPSCI 1MD3 with <b> tags
html_1md3 = """
<div><h3>COMPSCI 1MD3 - Introduction to Programming</h3>    3 unit(s) <br><hr>Introduction to fundamental programming concepts: values and types, expressions and evaluation, control flow constructs and exceptions, recursion, input/output and file processing.<br>Three lectures, one tutorial (one hour); first term<br><b>Prerequisite(s):</b> One of MATH 1K03, 1LS3, Grade 12 Advanced Functions and Introductory Calculus U, Grade 12 Calculus and Vectors, or registration or credit in ARTSSCI 1D06<br><b>Antirequisite(s):</b> ENGINEER 1D04, 1P13 A/B, IBEHS 1P10 A/B, MATH 1MP3, PHYSICS 2G03<br></div>
"""

# Test 3: Course with "Not open to students" restriction
html_not_open = """
<div><h3>ABLD 3BA3 - Topics in Black Studies</h3>    3 unit(s) <br><hr>This interdisciplinary course will explore selected topics.<br>Not open to students with credit or registration in INSPIRE 3EL3 if the topic was Topics in Black Studies.<br><b>Prerequisite(s):</b> None<br></div>
"""

# Test 4: Course with <strong> tags (AJAX preview format)
html_strong = """
<div><h3>COMPSCI 2C03 - Data Structures</h3>    3 unit(s) <br><hr>Basic data structures: stacks, queues, hash tables.<br>Three lectures, one tutorial (one hour); first term<br><strong>Prerequisite(s):</strong> COMPSCI 1DM3 or 2DM3<br><strong>Antirequisite(s):</strong> SFWRENG 2C03<br></div>
"""


def run_test(name, html, expected_restrictions):
    result = parse_course_html(html)
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"  Course: {result['course_name']}")
    print(f"  Prerequisites: {result['prerequisites']}")
    print(f"  Restrictions: {repr(result['restrictions'])}")
    print(f"  Description: {result['description'][:80]}...")

    if expected_restrictions:
        found = any(exp in result['restrictions'] for exp in expected_restrictions)
        status = "✅ PASS" if found else "❌ FAIL"
        print(f"  Expected to contain: {expected_restrictions}")
        print(f"  {status}")
        return found
    return True


all_passed = True
all_passed &= run_test("COMPSCI 1DM3 (<b> tags)", html_1dm3, ["COMPSCI 1FC3"])
all_passed &= run_test("COMPSCI 1MD3 (<b> tags)", html_1md3, ["ENGINEER 1D04"])
all_passed &= run_test("Not open to students", html_not_open, ["Not open to students"])
all_passed &= run_test("COMPSCI 2C03 (<strong> tags)", html_strong, ["SFWRENG 2C03"])

print(f"\n{'='*60}")
if all_passed:
    print("All tests passed! ✅")
else:
    print("Some tests FAILED! ❌")
    sys.exit(1)
