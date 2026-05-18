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


class BuildScheduleValuesTests(unittest.TestCase):
    def test_includes_section_metadata_for_each_schedule_block(self):
        all_schedules = [
            {
                "course_code": "CHEM 1E03",
                "combinations": [
                    {
                        "index": 7,
                        "schedule_blocks": [
                            {
                                "day": "Tue",
                                "start": "1:30 PM",
                                "end": "4:20 PM",
                                "type": "LEC",
                                "section": "LEC C01",
                            },
                            {
                                "day": "Wed",
                                "start": "9:30 AM",
                                "end": "11:50 AM",
                                "type": "LAB",
                                "section": "LAB L02",
                            },
                        ],
                        "sections": [
                            {
                                "section": "LEC C01",
                                "instructor": "Linda Davis",
                                "location": "Bldg - JHE_376",
                                "mode": "In Person",
                            },
                            {
                                "section": "LAB L02",
                                "instructor": "Staff",
                                "location": "Bldg - ABB_122LAB",
                                "mode": "Online",
                            },
                        ],
                    }
                ],
            }
        ]
        course_map = {"CHEM 1E03": 42}

        rows = TRANSFORM.build_schedule_values(all_schedules, course_map)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 42)  # course_id
        self.assertEqual(rows[0][1], 7)  # combo_index
        self.assertEqual(rows[0][6], "LEC C01")  # section
        self.assertEqual(rows[0][7], "Linda Davis")  # instructor_name
        self.assertEqual(rows[0][8], "JHE")  # building
        self.assertEqual(rows[0][9], "376")  # room_number
        self.assertEqual(rows[0][10], "In Person")  # mode
        self.assertTrue(rows[0][11])  # is_in_person

        self.assertEqual(rows[1][6], "LAB L02")
        self.assertEqual(rows[1][7], "Staff")
        self.assertEqual(rows[1][8], "ABB")
        self.assertEqual(rows[1][9], "122")
        self.assertEqual(rows[1][10], "Online")
        self.assertFalse(rows[1][11])

    def test_parses_online_and_tbd_locations(self):
        all_schedules = [
            {
                "course_code": "COMP 1XX3",
                "combinations": [
                    {
                        "index": 1,
                        "schedule_blocks": [
                            {
                                "day": "Mon",
                                "start": "10:30 AM",
                                "end": "11:20 AM",
                                "type": "LEC",
                                "section": "LEC C01",
                            },
                            {
                                "day": "Tue",
                                "start": "10:30 AM",
                                "end": "11:20 AM",
                                "type": "TUT",
                                "section": "TUT T01",
                            },
                        ],
                        "sections": [
                            {
                                "section": "LEC C01",
                                "instructor": "Staff",
                                "location": "Master - ONLINE",
                                "mode": "Online",
                            },
                            {
                                "section": "TUT T01",
                                "instructor": "Staff",
                                "location": "TBD",
                                "mode": "Unknown",
                            },
                        ],
                    }
                ],
            }
        ]
        course_map = {"COMP 1XX3": 100}

        rows = TRANSFORM.build_schedule_values(all_schedules, course_map)

        self.assertEqual(rows[0][8], "Online")
        self.assertEqual(rows[0][9], "Online")
        self.assertEqual(rows[1][8], "TBD")
        self.assertEqual(rows[1][9], "TBD")


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


if __name__ == "__main__":
    unittest.main()
