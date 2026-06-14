import importlib.util
import pathlib
import sys
import types
import unittest

TRANSFORM_PATH = pathlib.Path(__file__).resolve().parent / "schedule_seed_transform.py"
SPEC = importlib.util.spec_from_file_location("schedule_seed_transform", TRANSFORM_PATH)
assert SPEC is not None
assert SPEC.loader is not None
TRANSFORM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSFORM)

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda *_args, **_kwargs: None))
sys.modules.setdefault(
    "psycopg2.extras",
    types.SimpleNamespace(
        execute_values=lambda *_args, **_kwargs: None,
        Json=lambda value: value,
    ),
)
sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *_args, **_kwargs: None))

SEED_PATH = pathlib.Path(__file__).resolve().parent / "seed_db.py"
SEED_SPEC = importlib.util.spec_from_file_location("seed_db", SEED_PATH)
assert SEED_SPEC is not None
assert SEED_SPEC.loader is not None
SEED = importlib.util.module_from_spec(SEED_SPEC)
SEED_SPEC.loader.exec_module(SEED)


class ParseTimeTests(unittest.TestCase):
    def test_parses_no_space_format(self):
        self.assertEqual(TRANSFORM.parse_time("4:30PM"), "16:30:00")
        self.assertEqual(TRANSFORM.parse_time("10:30AM"), "10:30:00")
        self.assertEqual(TRANSFORM.parse_time("12:00PM"), "12:00:00")

    def test_parses_space_format(self):
        self.assertEqual(TRANSFORM.parse_time("1:30 PM"), "13:30:00")
        self.assertEqual(TRANSFORM.parse_time("9:30 AM"), "09:30:00")

    def test_handles_tba_and_empty(self):
        self.assertIsNone(TRANSFORM.parse_time("TBA"))
        self.assertIsNone(TRANSFORM.parse_time(""))
        self.assertIsNone(TRANSFORM.parse_time(None))


class ParseLocationTests(unittest.TestCase):
    def test_parses_standard_building_room(self):
        self.assertEqual(TRANSFORM.parse_location("ABB 271"), ("ABB", "271"))
        self.assertEqual(TRANSFORM.parse_location("BSB B156"), ("BSB", "B156"))

    def test_parses_in_person_placeholder(self):
        self.assertEqual(TRANSFORM.parse_location("In Person"), ("", ""))

    def test_parses_online(self):
        self.assertEqual(TRANSFORM.parse_location("Online"), ("Online", "Online"))
        self.assertEqual(TRANSFORM.parse_location("Virtual Classroom"), ("Online", "Online"))

    def test_parses_tba(self):
        self.assertEqual(TRANSFORM.parse_location("TBA"), ("TBD", "TBD"))
        self.assertEqual(TRANSFORM.parse_location("TBD"), ("TBD", "TBD"))

    def test_parses_empty(self):
        self.assertEqual(TRANSFORM.parse_location(""), ("", ""))
        self.assertEqual(TRANSFORM.parse_location(None), ("", ""))


class ParseSectionNameTests(unittest.TestCase):
    def test_converts_raw_format(self):
        self.assertEqual(TRANSFORM.parse_section_name("C01-LEC (5432)"), ("LEC C01", "LEC"))
        self.assertEqual(TRANSFORM.parse_section_name("L01-LAB (7679)"), ("LAB L01", "LAB"))
        self.assertEqual(TRANSFORM.parse_section_name("T03-TUT (9104)"), ("TUT T03", "TUT"))

    def test_handles_already_clean_format(self):
        # Already clean format should pass through
        name, type_ = TRANSFORM.parse_section_name("LEC C01")
        self.assertEqual(name, "LEC C01")

    def test_handles_empty(self):
        self.assertEqual(TRANSFORM.parse_section_name(""), ("", ""))
        self.assertEqual(TRANSFORM.parse_section_name(None), ("", ""))


class GetInstructorNamesTests(unittest.TestCase):
    def test_parses_single_name(self):
        self.assertEqual(TRANSFORM.get_instructor_names("John Smith"), ["John Smith"])

    def test_parses_newline_separated(self):
        self.assertEqual(
            TRANSFORM.get_instructor_names("Reza Nejat,\nSara Cormier"),
            ["Reza Nejat", "Sara Cormier"]
        )

    def test_parses_multi_instructor_with_nbsp(self):
        result = TRANSFORM.get_instructor_names("Miranda Schmidt,\nOleksiy\u00a0\u00a0\u00a0\u00a0 Alex Vorobyov")
        self.assertEqual(result, ["Miranda Schmidt", "Oleksiy Alex Vorobyov"])

    def test_parses_three_instructors(self):
        result = TRANSFORM.get_instructor_names("Adrienne Davidson,\nNibaldo Galleguillos,\nPeter Graefe")
        self.assertEqual(result, ["Adrienne Davidson", "Nibaldo Galleguillos", "Peter Graefe"])

    def test_includes_staff(self):
        result = TRANSFORM.get_instructor_names("Staff")
        self.assertEqual(result, ["Staff"])

    def test_empty(self):
        self.assertEqual(TRANSFORM.get_instructor_names(""), [])
        self.assertEqual(TRANSFORM.get_instructor_names(None), [])


class GetSectionInstructorSetTests(unittest.TestCase):
    def test_extracts_non_staff_instructors(self):
        section = {
            "details": [
                {"instructor": "John Smith"},
                {"instructor": "Staff"},
                {"instructor": "Jane Doe"},
            ]
        }
        result = TRANSFORM.get_section_instructor_set(section)
        self.assertEqual(result, {"John Smith", "Jane Doe"})

    def test_returns_empty_for_staff_only(self):
        section = {
            "details": [
                {"instructor": "Staff"},
            ]
        }
        result = TRANSFORM.get_section_instructor_set(section)
        self.assertEqual(result, set())


class DetectDeliveryModeTests(unittest.TestCase):
    def test_in_person(self):
        section = {"details": [{"room": "ABB 271"}]}
        mode, is_in_person = TRANSFORM.detect_delivery_mode(section)
        self.assertEqual(mode, "In Person")
        self.assertTrue(is_in_person)

    def test_online(self):
        section = {"details": [{"room": "Online"}]}
        mode, is_in_person = TRANSFORM.detect_delivery_mode(section)
        self.assertEqual(mode, "Online")
        self.assertFalse(is_in_person)

    def test_blended(self):
        section = {"details": [{"room": "ABB 271"}, {"room": "Online"}]}
        mode, is_in_person = TRANSFORM.detect_delivery_mode(section)
        self.assertEqual(mode, "Blended")
        self.assertTrue(is_in_person)

    def test_in_person_placeholder(self):
        section = {"details": [{"room": "In Person"}]}
        mode, is_in_person = TRANSFORM.detect_delivery_mode(section)
        self.assertEqual(mode, "In Person")
        self.assertTrue(is_in_person)


class RequirementNormalizationTests(unittest.TestCase):
    def test_normalizes_flat_requirements_to_unique_course_codes(self):
        requirements = [
            "ECON 2Z03 - Intermediate Microeconomics I",
            "ECON 2ZZ3 - Intermediate Microeconomics II",
            "ECON 2Z03 - Intermediate Microeconomics I",
            "electives",
        ]
        normalized = SEED.normalize_program_requirement_codes(requirements)
        self.assertEqual(normalized, ["ECON 2Z03", "ECON 2ZZ3"])

    def test_extracts_course_level_number_from_course_code(self):
        self.assertEqual(SEED.extract_course_level_number("PHYSICS 2B03"), 2)
        self.assertEqual(SEED.extract_course_level_number("SCIENCE 1A03"), 1)
        self.assertIsNone(SEED.extract_course_level_number("INVALID"))

    def test_normalize_term(self):
        self.assertEqual(SEED.normalize_term("2026 Spring/Summer"), "Spring/Summer 2026")
        self.assertEqual(SEED.normalize_term("Spring/Summer 2026"), "Spring/Summer 2026")
        self.assertEqual(SEED.normalize_term("2021 Winter"), "Winter 2021")
        self.assertEqual(SEED.normalize_term("Winter 2021"), "Winter 2021")
        self.assertEqual(SEED.normalize_term("Unknown"), "Unknown")
        self.assertEqual(SEED.normalize_term(""), "Unknown")

    def test_builds_course_title_code_map_from_catalog_shapes(self):
        courses = [
            {"course_name": "COMPSCI 1DM3 - Discrete Mathematics for Computer Science"},
            {"code": "MATH 1B03", "name": "Linear Algebra I"},
        ]

        self.assertEqual(
            SEED.build_course_title_code_map(courses),
            {
                "Discrete Mathematics for Computer Science": "COMPSCI 1DM3",
                "Linear Algebra I": "MATH 1B03",
            },
        )

    def test_resolves_schedule_course_id_by_title_when_code_is_title(self):
        course_map = {"COMPSCI 1DM3": 42}
        title_code_map = {
            "Discrete Mathematics for Computer Science": "COMPSCI 1DM3",
        }
        course = {
            "course_code": "Discrete Mathematics for Computer Science",
            "course_title": "Discrete Mathematics for Computer Science",
        }

        self.assertEqual(
            SEED.resolve_schedule_course_id(course, course_map, title_code_map),
            42,
        )


if __name__ == "__main__":
    unittest.main()
