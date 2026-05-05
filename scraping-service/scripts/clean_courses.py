import json
import os

def process_courses(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            courses = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    processed_courses = []
    for course in courses:
        full_name = course.get('course_name', '')
        if ' - ' in full_name:
            code, name = full_name.split(' - ', 1)
        else:
            code = ""
            name = full_name
        
        # Create a new dict with fields in preferred order
        new_course = {
            'code': code.strip(),
            'name': name.strip()
        }
        # Copy over other fields
        for key, value in course.items():
            if key != 'course_name':
                new_course[key] = value
        
        processed_courses.append(new_course)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_courses, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(processed_courses)} courses.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    input_file = 'data/all_courses.json'
    output_file = 'data/all_courses_processed.json'
    process_courses(input_file, output_file)
