import json
import os
import re
import psycopg2
from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv
from schedule_seed_transform import (
    parse_time,
    parse_location,
    parse_section_name,
    get_instructor_names,
    get_section_instructor_set,
    get_all_instructor_names_for_section,
    detect_delivery_mode,
)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def parse_units(units_str):
    if not units_str:
        return 0
    match = re.search(r'(\d+)', units_str)
    if match:
        return int(match.group(1))
    return 0


def extract_course_code(requirement_text):
    if not requirement_text:
        return None
    match = re.search(r"\b([A-Z]{2,10}\s\d[A-Z0-9]{2,4}(?:\s+A\/B)?)\b", requirement_text)
    if match:
        return match.group(1)
    return None


def normalize_course_code(value):
    if not value:
        return None
    code = extract_course_code(value)
    if not code:
        return None
    return code.strip()


def extract_course_level_number(course_code):
    if not course_code:
        return None
    match = re.search(r"\b[A-Z]{2,10}\s(\d)", course_code)
    if not match:
        return None
    return int(match.group(1))


def normalize_program_requirement_codes(requirements):
    normalized = []
    seen = set()
    for requirement in requirements:
        code = normalize_course_code(requirement)
        if not code or code in seen:
            continue
        seen.add(code)
        normalized.append(code)
    return normalized


def split_course_name(course_name):
    """Split 'COMPSCI 1DM3 - Discrete Mathematics' into ('COMPSCI 1DM3', 'Discrete Mathematics')."""
    if not course_name:
        return "", ""
    if " - " in course_name:
        code, name = course_name.split(" - ", 1)
        return code.strip(), name.strip()
    return "", course_name.strip()


def build_course_title_code_map(courses):
    title_to_code = {}
    ambiguous_titles = set()

    for course in courses:
        if "code" in course and "name" in course:
            code = course["code"]
            name = course["name"]
        else:
            code, name = split_course_name(course.get("course_name", ""))

        if not code or not name:
            continue

        if name in title_to_code and title_to_code[name] != code:
            ambiguous_titles.add(name)
            continue

        title_to_code[name] = code

    for title in ambiguous_titles:
        title_to_code.pop(title, None)

    return title_to_code


def resolve_schedule_course_id(course, course_map, title_code_map):
    course_code = course.get("course_code")
    course_id = course_map.get(course_code)
    if course_id:
        return course_id

    course_title = course.get("course_title")
    resolved_code = title_code_map.get(course_title)
    if resolved_code:
        return course_map.get(resolved_code)

    return None


def normalize_term(term_str):
    if not term_str:
        return "Unknown"
    
    term_str = term_str.strip()
    # Check if the term starts with a 4-digit year (e.g. "2026 Spring/Summer")
    match = re.match(r'^(\d{4})\s+(.+)$', term_str)
    if match:
        year, season = match.groups()
        return f"{season.strip()} {year}"
    return term_str


def seed():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Load all possible schedules
        with open("data/all_possible_schedules.json", "r") as f:
            all_schedules = json.load(f)

        # Collect all unique teacher names from schedules
        schedule_teacher_names = set()
        for term_data in all_schedules:
            for course in term_data.get("courses", []):
                for section in course.get("sections", []):
                    for name in get_all_instructor_names_for_section(section):
                        schedule_teacher_names.add(name)

        # 1. Load Teachers
        print("Seeding teachers...")
        with open("data/rmp_data.json", "r") as f:
            rmp_data = json.load(f)
        
        teacher_values = []
        name_to_rmp_id = {}
        for prof in rmp_data.get("professors", []):
            lower_name = prof["name"].strip().lower()
            name_to_rmp_id[lower_name] = prof["id"]
            teacher_values.append((
                prof["name"],
                prof.get("avgRating", 0),
                prof.get("avgDifficulty", 0),
                prof.get("department", "Unknown"),
                prof["id"],
                prof.get("numRatings", 0)
            ))
            
        # Add non-RMP teachers from schedules with default values (including "Staff")
        for name in schedule_teacher_names:
            lower_name = name.lower()
            if lower_name not in name_to_rmp_id:
                fake_rmp_id = f"non_rmp_{name.replace(' ', '_').lower()}"
                name_to_rmp_id[lower_name] = fake_rmp_id
                teacher_values.append((
                    name,
                    0.0,
                    0.0,
                    "Unknown",
                    fake_rmp_id,
                    0
                ))
        
        execute_values(cur, """
            INSERT INTO teacher (name, avg_rating, avg_difficulty, department, rmp_id, num_ratings)
            VALUES %s
            ON CONFLICT (rmp_id) DO UPDATE SET
                avg_rating = EXCLUDED.avg_rating,
                avg_difficulty = EXCLUDED.avg_difficulty,
                num_ratings = EXCLUDED.num_ratings
        """, teacher_values)

        # 2. Load Courses
        print("Seeding courses...")
        with open("data/all_courses.json", "r") as f:
            all_courses = json.load(f)
        
        title_code_map = build_course_title_code_map(all_courses)
        course_values_dict = {}
        for course in all_courses:
            if "code" in course and "name" in course:
                code = course["code"]
                name = course["name"]
            else:
                code, name = split_course_name(course.get("course_name", ""))

            if not code:
                continue

            level_number = extract_course_level_number(code)
            course_values_dict[code] = (
                code,
                name,
                course.get("description", ""),
                course.get("restrictions", ""),
                course.get("prerequisites", []),
                parse_units(course.get("units", "")),
                level_number,
            )
        
        course_values = list(course_values_dict.values())
        
        execute_values(cur, """
            INSERT INTO course (code, name, description, restrictions, prerequisites, units, level_number)
            VALUES %s
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                restrictions = EXCLUDED.restrictions,
                prerequisites = EXCLUDED.prerequisites,
                units = EXCLUDED.units,
                level_number = EXCLUDED.level_number
        """, course_values)

        scraped_course_codes = [v[0] for v in course_values]
        if scraped_course_codes:
            cur.execute(
                "DELETE FROM course WHERE code <> ALL(%s)",
                (scraped_course_codes,)
            )

        # Get mappings
        cur.execute("SELECT code, id FROM course")
        course_map = dict(cur.fetchall())
        
        cur.execute("SELECT rmp_id, id FROM teacher")
        teacher_rmp_map = dict(cur.fetchall())
        
        cur.execute("SELECT name, id FROM teacher")
        teacher_name_map = dict(cur.fetchall())

        # 3. Seed Sections, Section Meetings, Section Teachers, and Section References
        print("Seeding sections...")
        cur.execute("DELETE FROM section_references")
        cur.execute("DELETE FROM section_teachers")
        cur.execute("DELETE FROM section_meeting")
        cur.execute("DELETE FROM section")

        total_sections = 0
        total_meetings = 0
        total_section_teachers = 0
        total_references = 0

        for term_data in all_schedules:
            term = normalize_term(term_data.get("term", ""))
            for course in term_data.get("courses", []):
                course_code = course.get("course_code")
                course_id = resolve_schedule_course_id(course, course_map, title_code_map)
                if not course_id:
                    continue

                sections = course.get("sections", [])
                
                # Track section IDs by type for reference linking
                lec_sem_sections = []  # (section_db_id, instructor_set)
                lab_tut_sections = []  # (section_db_id, instructor_set)

                for section in sections:
                    section_name, section_type = parse_section_name(section.get("section_name", ""))
                    if not section_name:
                        continue

                    mode, is_in_person = detect_delivery_mode(section)

                    # Insert section
                    cur.execute(
                        """
                        INSERT INTO section (course_id, name, type, term, mode, is_in_person)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (course_id, section_name, section_type, term, mode, is_in_person)
                    )
                    section_id = cur.fetchone()[0]
                    total_sections += 1

                    # Insert section meetings
                    for detail in section.get("details", []):
                        days = detail.get("days", "")
                        start_time = parse_time(detail.get("start_time"))
                        end_time = parse_time(detail.get("end_time"))
                        building, room = parse_location(detail.get("room", ""))

                        cur.execute(
                            """
                            INSERT INTO section_meeting (section_id, days, start_time, end_time, building, room)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (section_id, days, start_time, end_time, building, room)
                        )
                        total_meetings += 1

                    # Insert section teachers
                    all_names = get_all_instructor_names_for_section(section)
                    linked_teacher_ids = set()
                    for name in all_names:
                        teacher_id = teacher_name_map.get(name)
                        if teacher_id and teacher_id not in linked_teacher_ids:
                            linked_teacher_ids.add(teacher_id)
                            cur.execute(
                                """
                                INSERT INTO section_teachers (section_id, teacher_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (section_id, teacher_id)
                            )
                            total_section_teachers += 1

                    # Track for reference linking
                    instructor_set = get_section_instructor_set(section)
                    if section_type in ("LEC", "SEM"):
                        lec_sem_sections.append((section_id, instructor_set))
                    elif section_type in ("LAB", "TUT"):
                        lab_tut_sections.append((section_id, instructor_set))

                # Create section references: link LEC/SEM -> LAB/TUT by matching professors
                for parent_id, parent_insts in lec_sem_sections:
                    for child_id, child_insts in lab_tut_sections:
                        # If the child has no non-Staff instructors, link to all parents
                        # If there's instructor overlap, link them
                        if not child_insts or not parent_insts or child_insts.intersection(parent_insts):
                            cur.execute(
                                """
                                INSERT INTO section_references (parent_section_id, child_section_id)
                                VALUES (%s, %s)
                                ON CONFLICT DO NOTHING
                                """,
                                (parent_id, child_id)
                            )
                            total_references += 1

        print(f"  Inserted {total_sections} sections")
        print(f"  Inserted {total_meetings} section meetings")
        print(f"  Inserted {total_section_teachers} section-teacher links")
        print(f"  Inserted {total_references} section references")

        # 4. Load Programs
        print("Seeding programs...")
        with open("data/all_programs_with_requirements.json", "r") as f:
            all_programs = json.load(f)
        
        program_courses = []
        scraped_program_names = []

        for prog in all_programs:
            scraped_program_names.append(prog["program_name"])
            requirement_codes = normalize_program_requirement_codes(prog.get("requirements", []))
            grouped_requirements = prog.get("requirements_by_level", [])

            cur.execute("SELECT id FROM program WHERE name = %s LIMIT 1", (prog["program_name"],))
            row = cur.fetchone()
            if row:
                program_id = row[0]
                cur.execute(
                    """
                    UPDATE program
                    SET source_url = %s,
                        requirement_codes = %s,
                        requirements_by_level = %s
                    WHERE id = %s
                    """,
                    (
                        prog.get("url"),
                        requirement_codes,
                        Json(grouped_requirements),
                        program_id,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO program (name, source_url, requirement_codes, requirements_by_level)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        prog["program_name"],
                        prog.get("url"),
                        requirement_codes,
                        Json(grouped_requirements),
                    ),
                )
                program_id = cur.fetchone()[0]

            cur.execute("DELETE FROM program_courses WHERE program_id = %s", (program_id,))

            for course_code in requirement_codes:
                course_id = course_map.get(course_code)
                if course_id is None:
                    continue
                program_courses.append((program_id, course_id))

        # Remove stale programs not present in latest scrape output.
        if scraped_program_names:
            cur.execute(
                "DELETE FROM program WHERE name <> ALL(%s)",
                (scraped_program_names,),
            )

        execute_values(cur, """
            INSERT INTO program_courses (program_id, course_id)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, program_courses)

        # 5. Course-Teacher Relationships
        print("Seeding course-teacher relationships...")
        course_teacher_values = []
        teacher_program_values = []

        # Build a reverse lookup: course_id -> set of program_ids
        cur.execute("SELECT course_id, program_id FROM program_courses")
        course_to_programs = {}
        for course_id, program_id in cur.fetchall():
            course_to_programs.setdefault(course_id, set()).add(program_id)

        seen_teacher_programs = set()

        for prof in rmp_data.get("professors", []):
            teacher_id = teacher_rmp_map.get(prof["id"])
            if not teacher_id:
                continue
            for course_code in prof.get("courses", []):
                course_id = course_map.get(course_code)
                if not course_id:
                    continue
                course_teacher_values.append((course_id, teacher_id))

                for program_id in course_to_programs.get(course_id, []):
                    key = (teacher_id, program_id)
                    if key not in seen_teacher_programs:
                        seen_teacher_programs.add(key)
                        teacher_program_values.append(key)

        # Also add course-teacher links from schedule data
        for term_data in all_schedules:
            for course in term_data.get("courses", []):
                course_code = course.get("course_code")
                course_id = resolve_schedule_course_id(course, course_map, title_code_map)
                if not course_id:
                    continue
                for section in course.get("sections", []):
                    for name in get_all_instructor_names_for_section(section):
                        teacher_id = teacher_name_map.get(name)
                        if not teacher_id:
                            continue
                        course_teacher_values.append((course_id, teacher_id))
                        for program_id in course_to_programs.get(course_id, []):
                            key = (teacher_id, program_id)
                            if key not in seen_teacher_programs:
                                seen_teacher_programs.add(key)
                                teacher_program_values.append(key)
                    
        execute_values(cur, """
            INSERT INTO course_teachers (course_id, teacher_id)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, course_teacher_values)

        if teacher_program_values:
            execute_values(cur, """
                INSERT INTO teacher_programs (teacher_id, program_id)
                VALUES %s
                ON CONFLICT DO NOTHING
            """, teacher_program_values)

        conn.commit()
        print("Database seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed()
