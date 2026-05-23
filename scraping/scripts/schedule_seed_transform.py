from datetime import datetime
import re


def parse_time(time_str):
    if not time_str or time_str == "TBA":
        return None
    try:
        # Handle formats like "4:30PM" (no space)
        t = datetime.strptime(time_str, "%I:%M%p")
        return t.strftime("%H:%M:%S")
    except ValueError:
        pass
    try:
        # Handle formats like "1:30 PM" (with space)
        t = datetime.strptime(time_str, "%I:%M %p")
        return t.strftime("%H:%M:%S")
    except ValueError:
        return None


def parse_mode_to_is_in_person(mode_str):
    if not mode_str:
        return False
    m = mode_str.strip().lower()
    if "online" in m or "virtual" in m:
        return "in person" in m or "in-person" in m or "blended" in m
    return True


def parse_location(room_str):
    """Parse the 'room' field from JSON details into (building, room).
    
    Examples:
        'ABB 271'     -> ('ABB', '271')
        'BSB B156'    -> ('BSB', 'B156')
        'In Person'   -> ('', '')
        'Online'      -> ('Online', 'Online')
        'TBA'         -> ('TBD', 'TBD')
    """
    if not room_str:
        return "", ""

    raw = room_str.strip()
    upper_raw = raw.upper()

    if upper_raw in ("IN PERSON", "IN-PERSON"):
        return "", ""

    if (
        "TBD" in upper_raw
        or "TBA" in upper_raw
        or "ANNOUNCED" in upper_raw
        or "SEE CLASS NOTES" in upper_raw
    ):
        return "TBD", "TBD"

    if "ONLINE" in upper_raw or "VIRTUAL" in upper_raw:
        return "Online", "Online"

    # Handle space-separated building and room numbers: e.g. "ABB 271", "BSB B156"
    parts = raw.split(None, 1)
    if len(parts) == 2:
        building, room = parts
        if re.match(r"^[A-Z0-9]+$", building):
            cleaned_room = re.sub(r"lab", "", room, flags=re.IGNORECASE).strip()
            return building, cleaned_room

    return raw.strip(), ""


def get_instructor_names(instructor_str):
    """Parse an instructor string into a list of cleaned individual names.
    
    Handles newline-separated, comma-separated, and mixed formats.
    Strips non-breaking spaces and normalizes whitespace.
    """
    if not instructor_str:
        return []

    # Replace non-breaking spaces
    cleaned = instructor_str.replace('\xa0', ' ')
    
    # Split by newline first, then by comma
    parts = []
    for line in cleaned.split('\n'):
        for part in line.split(','):
            clean_part = re.sub(r'\s+', ' ', part).strip()
            if clean_part:
                parts.append(clean_part)

    return parts


def parse_section_name(raw_section):
    """Convert 'C01-LEC (5432)' to 'LEC C01'."""
    if not raw_section:
        return "", ""
    match = re.match(r"^([A-Z0-9]+)\s*-\s*([A-Z]+)(?:\s+\(\d+\))?$", raw_section.strip(), flags=re.IGNORECASE)
    if match:
        section_code = match.group(1).upper()
        section_type = match.group(2).upper()
        return f"{section_type} {section_code}", section_type
    return raw_section.strip(), ""


def get_section_instructor_set(section):
    """Get the set of non-Staff instructor names for a section."""
    names = set()
    for detail in section.get("details", []):
        for name in get_instructor_names(detail.get("instructor", "")):
            if name.lower() != "staff":
                names.add(name)
    return names


def get_all_instructor_names_for_section(section):
    """Get ALL instructor names for a section (including Staff)."""
    names = set()
    for detail in section.get("details", []):
        for name in get_instructor_names(detail.get("instructor", "")):
            names.add(name)
    return names


def detect_delivery_mode(section):
    """Detect the delivery mode from a section's room fields."""
    has_online = False
    has_in_person = False
    
    for detail in section.get("details", []):
        room = (detail.get("room") or "").strip().upper()
        if "ONLINE" in room or "VIRTUAL" in room:
            has_online = True
        elif room and room not in ("IN PERSON", "IN-PERSON", "TBA", "TBD"):
            has_in_person = True
        elif room in ("IN PERSON", "IN-PERSON"):
            has_in_person = True
    
    if has_online and has_in_person:
        return "Blended", True
    elif has_online:
        return "Online", False
    elif has_in_person:
        return "In Person", True
    return "Unknown", False
