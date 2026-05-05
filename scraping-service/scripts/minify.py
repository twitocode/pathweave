import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def minify_courses():
    with open(os.path.join(DATA_DIR, "all_courses.json"), "r") as file:
        courses = json.load(file)

    for i in range(len(courses)):
        course = courses[i]

        new_course = {"c": course["code"], "n": course["name"]}
        courses[i] = new_course

    with open(os.path.join(DATA_DIR, "minify/all_courses_minify.json"), "w") as file:
        json.dump(courses, file, indent=2)


def minify_programs():
    with open(os.path.join(DATA_DIR, "all_programs_with_requirements.json"), "r") as file:
        programs = json.load(file)

    for i in range(len(programs)):
        program = programs[i]

        new_program = {"n": program["program_name"]}
        programs[i] = new_program

    with open(os.path.join(DATA_DIR, "minify/all_programs_minify.json"), "w") as file:
        json.dump(programs, file, indent=2)

if __name__ == "__main__":
    minify_courses()
    minify_programs()
