import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


with open(
    "/Users/twito/Documents/Code/projects/PathWeave/python-api/data/all_courses.json"
) as f:
    data = json.load(f)

count = 0
for d in data:
    count += 1
    #print(data[i]["course_name"])

print(f"Course count: {count}")