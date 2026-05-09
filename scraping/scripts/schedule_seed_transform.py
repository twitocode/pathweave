from datetime import datetime
import re


def parse_time(time_str):
    if not time_str or time_str == "TBA":
        return "00:00:00"
    try:
        # Handle formats like "1:30 PM"
        t = datetime.strptime(time_str, "%I:%M %p")
        return t.strftime("%H:%M:%S")
    except ValueError:
        return "00:00:00"


def parse_mode_to_is_in_person(mode_str):
    if not mode_str:
        return False
    return mode_str.strip().lower() == "in person"


def parse_location(location_str):
    if not location_str:
        return "", ""

    raw = location_str.strip()
    upper_raw = raw.upper()

    if "TBD" in upper_raw or "TBA" in upper_raw:
        return "TBD", "TBD"

    if "ONLINE" in upper_raw or "VIRTUAL" in upper_raw:
        return "Online", "Online"

    # Normalize "Prefix - BUILDING_ROOM" to "BUILDING_ROOM"
    if " - " in raw:
        raw = raw.split(" - ", 1)[1].strip()

    if "_" in raw:
        building, room_number = raw.split("_", 1)
        cleaned_room = re.sub(r"lab", "", room_number, flags=re.IGNORECASE).strip()
        return building.strip(), cleaned_room

    return raw.strip(), ""


def build_schedule_values(all_schedules, course_map):
    schedule_values = []

    for item in all_schedules:
        course_id = course_map.get(item["course_code"])
        if not course_id:
            continue

        for combo in item.get("combinations", []):
            combo_index = combo.get("index", 0)
            section_details = {
                section.get("section"): section
                for section in combo.get("sections", [])
                if section.get("section")
            }

            for block in combo.get("schedule_blocks", []):
                section_name = block["section"]
                details = section_details.get(section_name, {})
                mode = details.get("mode", "Unknown")
                building, room_number = parse_location(details.get("location", ""))

                schedule_values.append(
                    (
                        course_id,
                        combo_index,
                        block["day"][:3],  # Ensure it matches VARCHAR(3)
                        parse_time(block["start"]),
                        parse_time(block["end"]),
                        block["type"],
                        section_name,
                        details.get("instructor", "Staff"),
                        building,
                        room_number,
                        mode,
                        parse_mode_to_is_in_person(mode),
                    )
                )

    return schedule_values
