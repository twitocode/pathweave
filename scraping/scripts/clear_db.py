import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from the root .env file
# Based on scrape_schedules.py, the .env is in the project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

def clear_db():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in environment.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Order matters if not using CASCADE, but TRUNCATE ... CASCADE is easiest.
        # We list all tables for clarity.
        tables = [
            "user_detail_avoided_courses",
            "user_detail_completed_courses",
            "user_details",
            "users",
            "course_teachers",
            "teacher_programs",
            "program_courses",
            "program_requirement_item",
            "program_requirement_group",
            "schedule_combo",
            "teacher",
            "course",
            "program"
        ]
        
        print("Clearing database tables...")
        # TRUNCATE is faster and more thorough for clearing all data.
        # CASCADE handles foreign key dependencies automatically.
        # RESTART IDENTITY resets any auto-incrementing sequences.
        query = f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;"
        cur.execute(query)
        
        conn.commit()
        print("All database entries deleted successfully.")
        
    except Exception as e:
        print(f"Error clearing database: {e}")
    finally:
        if 'conn' in locals() and conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL entries in the database? (y/N): ")
    if confirm.lower() == 'y':
        clear_db()
    else:
        print("Operation cancelled.")
