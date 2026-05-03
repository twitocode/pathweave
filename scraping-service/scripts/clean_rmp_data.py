import json
import re
import os

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
                
                # --- NEW Logic: Resolve Prefix ---
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
                
                # 4. Final verification: Check if this combination exists in canonical list
                # (Optional but good for quality)
                
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

def main():
    rmp_path = 'data/rmp_data.json'
    courses_path = 'data/all_courses.json'
    progs_path = 'data/all_programs_with_requirements.json'

    # 1. Gather all unique subject codes from all available sources
    all_subjects = set()
    code_to_dept = {}

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

    if not os.path.exists(rmp_path):
        print("Error: data/rmp_data.json not found.")
        return

    with open(rmp_path, 'r') as f:
        rmp_data = json.load(f)

    # Update Professor list
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
    with open(rmp_path, 'w') as f:
        json.dump(rmp_data, f, indent=2)

    print(f"Smart cleaning of {rmp_path} complete. Subjects detected: {len(all_subjects)}")

if __name__ == "__main__":
    main()
