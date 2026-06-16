import os
import re
from datetime import datetime
from glob import glob
from typing import Any, Dict, List, Set

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

COURSE_CODE_RE = re.compile(r"\b[A-Z]{2,10}\s\d[A-Z0-9]{2,4}(?:\s+A/B)?\b")


# ---------------------------------------------------------------------------
# File / data utilities
# ---------------------------------------------------------------------------

def cleanup_worker_files(prefix: str) -> None:
    """Remove worker partial-result files matching the given prefix."""
    pattern = os.path.join(DATA_DIR, f"{prefix}.worker_*.json")
    for path in glob(pattern):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Warning: failed to remove worker file {path}: {e}")


# ---------------------------------------------------------------------------
# Course catalog helpers
# ---------------------------------------------------------------------------

def split_catalog_course_name(course_name: str) -> tuple[str, str]:
    """Split 'COMPSCI 1DM3 - Discrete Mathematics' into ('COMPSCI 1DM3', 'Discrete Mathematics')."""
    if not course_name or " - " not in course_name:
        return "", (course_name or "").strip()
    code, title = course_name.split(" - ", 1)
    return code.strip(), title.strip()


def build_course_title_code_map(courses: List[Dict[str, Any]]) -> Dict[str, str]:
    """Build a mapping from course title to course code from the catalog data.

    Handles both raw format (course_name: "CODE - Title") and processed format
    (code: "CODE", name: "Title"). Ambiguous titles (same title, different codes)
    are excluded.
    """
    title_to_code: Dict[str, str] = {}
    ambiguous_titles: Set[str] = set()

    for course in courses:
        code = course.get("code")
        title = course.get("name")
        if not code or not title:
            code, title = split_catalog_course_name(course.get("course_name", ""))

        if not code or not title:
            continue

        if title in title_to_code and title_to_code[title] != code:
            ambiguous_titles.add(title)
            continue

        title_to_code[title] = code

    for title in ambiguous_titles:
        title_to_code.pop(title, None)

    return title_to_code


def resolve_scraped_course_code(scraped_code: str, course_title: str, title_code_map: Dict[str, str]) -> str:
    """Resolve a scraped course code, falling back to title lookup if the code is malformed."""
    scraped_code = (scraped_code or "").strip()
    course_title = (course_title or "").strip()

    if COURSE_CODE_RE.fullmatch(scraped_code):
        return scraped_code

    return title_code_map.get(course_title, scraped_code or course_title)


# ---------------------------------------------------------------------------
# Schedule / section parsing utilities
# ---------------------------------------------------------------------------

def parse_time(time_str):
    """Parse a 12-hour time string (e.g. '4:30PM') to 24-hour format ('16:30:00')."""
    if not time_str or time_str == "TBA":
        return None
    try:
        t = datetime.strptime(time_str, "%I:%M%p")
        return t.strftime("%H:%M:%S")
    except ValueError:
        pass
    try:
        t = datetime.strptime(time_str, "%I:%M %p")
        return t.strftime("%H:%M:%S")
    except ValueError:
        return None


def parse_mode_to_is_in_person(mode_str):
    """Determine if a delivery mode string indicates in-person attendance."""
    if not mode_str:
        return False
    m = mode_str.strip().lower()
    if "online" in m or "virtual" in m:
        return "in person" in m or "in-person" in m or "blended" in m
    return True


def parse_location(room_str):
    """Parse the 'room' field into (building, room).

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
    """Convert 'C01-LEC (5432)' to ('LEC C01', 'LEC')."""
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
