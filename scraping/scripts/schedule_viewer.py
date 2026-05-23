import json
import os
from typing import TypedDict

class Detail(TypedDict):
    days: str
    start_time: str
    end_time: str
    room: str
    instructor: str
    dates: str


class Section(TypedDict):
    section_name: str
    session: str
    status: str
    details: Detail


class Course(TypedDict):
    course_code: str
    course_title: str
    term: str
    sections: list[Section]


class Term(TypedDict):
    term: str
    courses: list[Course]


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def run():
    terms: list[Term] = []
    with open(DATA_DIR + "/all_possible_schedules.json", "r") as f:
        terms = json.load(f)

    course_map = {}
    rooms = {}
    
    for i in range(len(terms)):
        for j in range(len(terms[i]["courses"])):
            course = terms[i]["courses"][j]
            term = course["term"]
            sections_length = len(course["sections"])
            code = course["course_code"]
            sections = course['sections']

            if sections_length > 0:
                if code in course_map:
                    course_map[code].append(term)
                else:
                    course_map[code] = [term]
            
            for section in sections:
              for detail in section['details']:
                  room = detail['room']
                  if room not in rooms:
                      rooms[room] = 1
                  else:
                    rooms[room] += 1
                
            if code in course_map:
                course_map[code].append(term)
            else:
                course_map[code] = [term]  
    
    with open(DATA_DIR + "/tmp/course_term_map.json", "w") as f:
        json.dump(course_map, f, indent=2)
    
    with open(DATA_DIR + "/tmp/room_map.json", "w") as f:
        json.dump(rooms, f, indent=2)

  
if __name__ == "__main__":
    run()
