import asyncio
import json
import os
import re
import httpx

# School ID for McMaster University
SCHOOL_ID_B64 = "U2Nob29sLTE0NDA="
GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
}

# Semaphore to limit concurrency
MAX_CONCURRENT_TEACHERS = 10

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Known common McMaster RMP aliases
SUBJECT_ALIASES = {
    "COMM": "COMMERCE",
    "KIN": "KINESIOL",
    "BIO": "BIOLOGY",
    "CHEM": "CHEM",
    "PSYCH": "PSYCH",
    "ENG": "ENGINEER",
    "ECON": "ECON",
    "MATH": "MATH",
    "COMP": "COMPSCI",
    "CS": "COMPSCI",
    "SFWRENG": "SFWRENG",
    "SOFTENG": "SFWRENG",
    "SOCIOL": "SOCIOL",
    "SOC": "SOCIOL",
    "ANTRHO": "ANTHROP",
    "ANTH": "ANTHROP",
}


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

async def get_all_teachers():
    teachers = []
    has_next_page = True
    cursor = ""

    query = """
    query TeacherSearchPaginationQuery(
      $count: Int!
      $cursor: String
      $query: TeacherSearchQuery!
    ) {
      newSearch {
        teachers(query: $query, first: $count, after: $cursor) {
          edges {
            node {
              id
              firstName
              lastName
              avgRating
              avgDifficulty
              numRatings
              department
            }
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        while has_next_page:
            variables = {
                "count": 100,
                "cursor": cursor,
                "query": {"text": "", "schoolID": SCHOOL_ID_B64},
            }

            try:
                response = await client.post(
                    GRAPHQL_URL, json={"query": query, "variables": variables}
                )
                data = response.json()

                edges = data["data"]["newSearch"]["teachers"]["edges"]
                for edge in edges:
                    teachers.append(edge["node"])

                page_info = data["data"]["newSearch"]["teachers"]["pageInfo"]
                has_next_page = page_info["hasNextPage"]
                cursor = page_info["endCursor"]

                print(f"Fetched {len(teachers)} teachers...", end="\r")
            except Exception as e:
                print(f"\n[Error] Failed to fetch teachers: {e}")
                break

    print(f"\nTotal teachers found: {len(teachers)}")
    return teachers


async def get_teacher_courses(client, teacher, semaphore):
    async with semaphore:
        query = """
        query TeacherRatingsPageQuery($id: ID!) {
          node(id: $id) {
            ... on Teacher {
              ratings(first: 100) {
                edges {
                  node {
                    class
                  }
                }
              }
            }
          }
        }
        """

        try:
            response = await client.post(
                GRAPHQL_URL, json={"query": query, "variables": {"id": teacher["id"]}}
            )
            data = response.json()

            ratings = data["data"]["node"]["ratings"]["edges"]
            # Extract unique course codes
            courses = set()
            for r in ratings:
                c = r["node"]["class"]
                if c:
                    courses.add(
                        c.upper().replace(" ", "")
                    )  # Normalize to compact uppercase

            return {
                "id": teacher["id"],
                "name": f"{teacher['firstName']} {teacher['lastName']}",
                "avgRating": teacher["avgRating"],
                "avgDifficulty": teacher["avgDifficulty"],
                "numRatings": teacher["numRatings"],
                "department": teacher["department"],
                "courses": list(courses),
            }
        except Exception as e:
            # print(f"\n[Error] Failed for {teacher['firstName']} {teacher['lastName']}: {e}")
            return None


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def _build_subject_index():
    """Build the set of all known subjects and a code-to-department mapping
    from local data files (programs + courses)."""
    all_subjects = set()
    code_to_dept = {}

    courses_path = os.path.join(DATA_DIR, "all_courses.json")
    progs_path = os.path.join(DATA_DIR, "all_programs_with_requirements.json")

    # Load from programs (very reliable for diverse codes)
    if os.path.exists(progs_path):
        with open(progs_path, 'r') as f:
            progs = json.load(f)
            for p in progs:
                for req in p['requirements']:
                    match = re.match(r'^([A-Z]+)\s([0-9][A-Z0-9]+)', req)
                    if match:
                        d, n = match.group(1), match.group(2)
                        all_subjects.add(d)
                        if n not in code_to_dept: code_to_dept[n] = []
                        if d not in code_to_dept[n]: code_to_dept[n].append(d)

    # Load from courses
    if os.path.exists(courses_path):
        with open(courses_path, 'r') as f:
            courses = json.load(f)
            for c in courses:
                match = re.match(r'^([A-Z]+)\s([0-9][A-Z0-9]+)', c['course_name'])
                if match:
                    d, n = match.group(1), match.group(2)
                    all_subjects.add(d)
                    if n not in code_to_dept: code_to_dept[n] = []
                    if d not in code_to_dept[n]: code_to_dept[n].append(d)

    return all_subjects, code_to_dept


def split_and_clean_codes(raw_list, dept_hint, code_to_dept, all_subjects):
    cleaned_set = set()
    
    for item in raw_list:
        if not item: continue
        item = item.upper().replace(" ", "")
        
        # Split concatenated codes and extract chunks
        chunks = re.findall(r"([A-Z]*[0-9][A-Z0-9]{3,4})", item)
        if not chunks:
            chunks = [item]
            
        for chunk in chunks:
            match = re.match(r"([A-Z]+)?([0-9][A-Z0-9]+)", chunk)
            if match:
                prefix = match.group(1) or ""
                num = match.group(2)
                
                # --- Resolve Prefix ---
                resolved_prefix = prefix
                
                # 1. Try manual alias
                if prefix in SUBJECT_ALIASES:
                    resolved_prefix = SUBJECT_ALIASES[prefix]
                
                # 2. Try prefix matching against all subjects
                elif prefix and prefix not in all_subjects:
                    # e.g. "COM" might match "COMMERCE"
                    matches = [s for s in all_subjects if s.startswith(prefix)]
                    if len(matches) == 1:
                        resolved_prefix = matches[0]
                
                # 3. Handle missing prefix using dept hint and canonical list
                if not resolved_prefix:
                    if num in code_to_dept:
                        possible = code_to_dept[num]
                        # Try to match hint
                        for d in possible:
                            if d in dept_hint or dept_hint in d or d[:3] in dept_hint:
                                resolved_prefix = d
                                break
                        if not resolved_prefix:
                            resolved_prefix = possible[0]
                
                final_code = f"{resolved_prefix} {num}".strip()
                cleaned_set.add(final_code)
            else:
                cleaned_set.add(chunk)
    
    # Remove subsets/suffixes
    final_list = list(cleaned_set)
    unique_courses = []
    for c1 in final_list:
        is_redundant = False
        c1_no_space = c1.replace(" ", "")
        for c2 in final_list:
            if c1 == c2: continue
            c2_no_space = c2.replace(" ", "")
            if c2_no_space.endswith(c1_no_space) and len(c2_no_space) > len(c1_no_space):
                is_redundant = True
                break
            if c1_no_space in c2_no_space and len(c1_no_space) < 4:
                is_redundant = True
                break
        if not is_redundant:
            unique_courses.append(c1)
                
    return sorted(unique_courses)


def clean_rmp_data(rmp_data):
    """Clean course codes on professors and rebuild the course_mapping in-place."""
    all_subjects, code_to_dept = _build_subject_index()

    for prof in rmp_data['professors']:
        dept_hint = prof['department'].upper()
        old_courses = prof.get('courses', [])
        prof['courses'] = split_and_clean_codes(old_courses, dept_hint, code_to_dept, all_subjects)

    # Rebuild Mapping
    new_mapping = {}
    for prof in rmp_data['professors']:
        for course in prof['courses']:
            if course not in new_mapping:
                new_mapping[course] = []
            new_mapping[course].append({
                "name": prof['name'],
                "avgRating": prof['avgRating'],
                "avgDifficulty": prof['avgDifficulty'],
                "numRatings": prof['numRatings'],
                "department": prof['department'],
                "rmpId": prof['id']
            })

    rmp_data['course_mapping'] = new_mapping
    print(f"Cleaned course codes. Subjects detected: {len(all_subjects)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    teachers_basic = await get_all_teachers()

    active_teachers = [t for t in teachers_basic if t["numRatings"] > 0]
    print(f"Active teachers (with ratings): {len(active_teachers)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TEACHERS)

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        tasks = [get_teacher_courses(client, t, semaphore) for t in active_teachers]

        print("Fetching course details for each teacher...")
        detailed_teachers = await asyncio.gather(*tasks)

    valid_results = [t for t in detailed_teachers if t is not None]

    # Build initial (uncleaned) mapping
    course_to_profs = {}
    for t in valid_results:
        for c in t["courses"]:
            if c not in course_to_profs:
                course_to_profs[c] = []
            course_to_profs[c].append(
                {
                    "name": t["name"],
                    "avgRating": t["avgRating"],
                    "avgDifficulty": t["avgDifficulty"],
                    "numRatings": t["numRatings"],
                    "department": t["department"],
                    "rmpId": t["id"],
                }
            )

    rmp_data = {"professors": valid_results, "course_mapping": course_to_profs}

    # Clean course codes in-place and rebuild the mapping
    clean_rmp_data(rmp_data)

    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "rmp_data.json")
    with open(output_path, "w") as f:
        json.dump(rmp_data, f, indent=2)

    print(f"\nSuccess! Scraped {len(valid_results)} professors.")
    print(f"Data saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
