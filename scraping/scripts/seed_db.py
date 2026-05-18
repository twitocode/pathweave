import json
import os
import re
import psycopg2
from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv
from schedule_seed_transform import build_schedule_values

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
        # 1. Load Teachers
        print("Seeding teachers...")
        with open("data/rmp_data.json", "r") as f:
            rmp_data = json.load(f)
        
        teacher_values = []
        for prof in rmp_data.get("professors", []):
            teacher_values.append((
                prof["name"],
                prof.get("avgRating", 0),
                prof.get("avgDifficulty", 0),
                prof.get("department", "Unknown"),
                prof["id"],
                prof.get("numRatings", 0)
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
        
        # Terms come from all_possible_schedules.json
        with open("data/all_possible_schedules.json", "r") as f:
            all_schedules = json.load(f)
        
        course_terms = {}
        for item in all_schedules:
            course_terms[item["course_code"]] = normalize_term(item.get("term", ""))

        course_values = []
        for course in all_courses:
            # Handle both raw (course_name) and cleaned (code/name) formats
            if "code" in course and "name" in course:
                code = course["code"]
                name = course["name"]
            else:
                code, name = split_course_name(course.get("course_name", ""))

            if not code:
                continue

            level_number = extract_course_level_number(code)
            course_values.append((
                code,
                name,
                course.get("description", ""),
                course.get("restrictions", ""),
                course.get("prerequisites", []),
                parse_units(course.get("units", "")),
                course_terms.get(code, "Unknown"),
                level_number,
            ))
        
        execute_values(cur, """
            INSERT INTO course (code, name, description, restrictions, prerequisites, units, term, level_number)
            VALUES %s
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                restrictions = EXCLUDED.restrictions,
                prerequisites = EXCLUDED.prerequisites,
                units = EXCLUDED.units,
                term = EXCLUDED.term,
                level_number = EXCLUDED.level_number
        """, course_values)

        # Get course code to ID mapping for relationships
        cur.execute("SELECT code, id FROM course")
        course_map = dict(cur.fetchall())
        
        # Get teacher rmp_id to ID mapping
        cur.execute("SELECT rmp_id, id FROM teacher")
        teacher_map = dict(cur.fetchall())

        # 3. Load Schedule Combos
        print("Seeding schedule combos...")
        schedule_values = build_schedule_values(all_schedules, course_map)
        
        # Clear existing schedules to avoid duplicates if re-running
        cur.execute("DELETE FROM schedule_combo")
        execute_values(cur, """
            INSERT INTO schedule_combo (
                course_id,
                combo_index,
                day,
                start_time,
                end_time,
                type,
                section,
                instructor_name,
                building,
                room_number,
                mode,
                is_in_person
            )
            VALUES %s
        """, schedule_values)

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

        # Build a reverse lookup: course_code -> set of program_ids
        cur.execute("SELECT course_id, program_id FROM program_courses")
        course_to_programs = {}
        for course_id, program_id in cur.fetchall():
            course_to_programs.setdefault(course_id, set()).add(program_id)

        seen_teacher_programs = set()

        for prof in rmp_data.get("professors", []):
            teacher_id = teacher_map.get(prof["id"])
            if not teacher_id:
                continue
            for course_code in prof.get("courses", []):
                course_id = course_map.get(course_code)
                if not course_id:
                    continue
                course_teacher_values.append((course_id, teacher_id))

                # Also link teacher to every program that includes this course
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
