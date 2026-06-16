# Backwards-compatibility shim — all utilities now live in utils.py
from utils import (  # noqa: F401
    parse_time,
    parse_mode_to_is_in_person,
    parse_location,
    get_instructor_names,
    parse_section_name,
    get_section_instructor_set,
    get_all_instructor_names_for_section,
    detect_delivery_mode,
)
