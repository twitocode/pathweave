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
    m = mode_str.strip().lower()
    # Check if "online" or "virtual" is in the mode.
    # If it has "online" or "virtual", we only mark it in-person if it's a hybrid
    # mode that explicitly contains "in person", "in-person", or "blended".
    if "online" in m or "virtual" in m:
        return "in person" in m or "in-person" in m or "blended" in m
    # Otherwise, check for standard virtual indicators; default to True for normal modes.
    return True


def parse_location(location_str):
    if not location_str:
        return "", ""

    raw = location_str.strip()
    upper_raw = raw.upper()

    # Match common placeholders like TBD, TBA, To Be Announced, or See Class Notes
    if (
        "TBD" in upper_raw
        or "TBA" in upper_raw
        or "ANNOUNCED" in upper_raw
        or "SEE CLASS NOTES" in upper_raw
    ):
        return "TBD", "TBD"

    if "ONLINE" in upper_raw or "VIRTUAL" in upper_raw:
        return "Online", "Online"

    # Normalize "Prefix - BUILDING_ROOM" to "BUILDING_ROOM"
    if " - " in raw:
        raw = raw.split(" - ", 1)[1].strip()

    if "_" in raw:
        building, room = raw.split("_", 1)
        cleaned_room = re.sub(r"lab", "", room, flags=re.IGNORECASE).strip()
        return building.strip(), cleaned_room

    # Handle space-separated building and room numbers: e.g. "ABB 271", "BSB B156"
    # We split by the first whitespace. If the first part is all uppercase alphanumeric
    # (e.g. "ABB", "T13") and there's a second part, we treat it as building and room.
    parts = raw.split(None, 1)
    if len(parts) == 2:
        building, room = parts
        if re.match(r"^[A-Z0-9]+$", building):
            cleaned_room = re.sub(r"lab", "", room, flags=re.IGNORECASE).strip()
            return building, cleaned_room

    return raw.strip(), ""


def get_instructor_names(instructor_str):
    if not instructor_str:
        return []
    
    parts = instructor_str.split(',')
    clean_parts = []
    for part in parts:
        clean_part = re.sub(r'\s+', ' ', part).strip()
        if clean_part and clean_part.lower() != "staff":
            clean_parts.append(clean_part)
            
    return clean_parts


def parse_instructor_name(instructor_str):
    clean_parts = get_instructor_names(instructor_str)
    if not clean_parts:
        return "Staff"
    return ", ".join(clean_parts)


def parse_section_name(raw_section):
    if not raw_section:
        return ""
    match = re.match(r"^([A-Z0-9]+)\s*-\s*([A-Z]+)(?:\s+\(\d+\))?$", raw_section.strip(), flags=re.IGNORECASE)
    if match:
        section_code = match.group(1).upper()
        section_type = match.group(2).upper()
        return f"{section_type} {section_code}"
    return raw_section.strip()


def build_schedule_values(all_schedules, course_map):
    schedule_values = []

    for item in all_schedules:
        course_id = course_map.get(item["course_code"])
        if not course_id:
            continue

        for combo in item.get("combinations", []):
            combo_index = combo.get("index", 0)
            section_details = {}
            for section in combo.get("sections", []):
                raw_sec = section.get("section")
                if raw_sec:
                    clean_sec = parse_section_name(raw_sec)
                    section_details[clean_sec] = section

            for block in combo.get("schedule_blocks", []):
                clean_sec_name = parse_section_name(block.get("section", ""))
                details = section_details.get(clean_sec_name, {})
                mode = details.get("mode", "Unknown")
                building, room = parse_location(details.get("location", ""))

                schedule_values.append(
                    (
                        course_id,
                        combo_index,
                        block["day"][:3],  # Ensure it matches VARCHAR(3)
                        parse_time(block["start"]),
                        parse_time(block["end"]),
                        block["type"],
                        clean_sec_name,
                        parse_instructor_name(details.get("instructor", "Staff")),
                        building,
                        room,
                        mode,
                        parse_mode_to_is_in_person(mode),
                    )
                )

    return schedule_values
