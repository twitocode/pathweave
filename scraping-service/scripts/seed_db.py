import json
import os
import re
import psycopg2
from psycopg2.extras import execute_values
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
        
        # We also need terms from all_possible_schedules.json
        with open("data/all_possible_schedules.json", "r") as f:
            all_schedules = json.load(f)
        
        course_terms = {}
        for item in all_schedules:
            course_terms[item["course_code"]] = item["term"]

        course_values = []
        for course in all_courses:
            code = course["code"]
            course_values.append((
                code,
                course["name"],
                course["description"],
                course.get("restrictions", ""),
                course.get("prerequisites", []),
                parse_units(course["units"]),
                course_terms.get(code, "Unknown")
            ))
        
        execute_values(cur, """
            INSERT INTO course (code, name, description, restrictions, prerequisites, units, term)
            VALUES %s
            ON CONFLICT (code) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                restrictions = EXCLUDED.restrictions,
                prerequisites = EXCLUDED.prerequisites,
                units = EXCLUDED.units,
                term = EXCLUDED.term
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
        for prog in all_programs:
            cur.execute("INSERT INTO program (name) VALUES (%s) RETURNING id", (prog["program_name"],))
            program_id = cur.fetchone()[0]
            
            for req in prog.get("requirements", []):
                # Requirement format: "CODE - NAME"
                match = re.match(r'^([A-Z]+ \d+[A-Z\d]*)\s*-\s*(.*)$', req)
                if match:
                    req_code = match.group(1).strip()
                    if req_code in course_map:
                        program_courses.append((program_id, course_map[req_code]))

        execute_values(cur, """
            INSERT INTO program_courses (program_id, course_id)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, program_courses)

        # 5. Course-Teacher Relationships
        print("Seeding course-teacher relationships...")
        course_teacher_values = []
        for prof in rmp_data.get("professors", []):
            teacher_id = teacher_map.get(prof["id"])
            if not teacher_id:
                continue
            for course_code in prof.get("courses", []):
                if course_code in course_map:
                    course_teacher_values.append((course_map[course_code], teacher_id))
        
        execute_values(cur, """
            INSERT INTO course_teachers (course_id, teacher_id)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, course_teacher_values)

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
