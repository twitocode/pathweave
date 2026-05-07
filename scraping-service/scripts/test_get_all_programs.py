import importlib.util
import pathlib
import unittest

SCRIPT_PATH = pathlib.Path(__file__).resolve().parent / "get_all_programs.py"
SPEC = importlib.util.spec_from_file_location("get_all_programs", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
GET_ALL_PROGRAMS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GET_ALL_PROGRAMS)


class ParseRequirementsByLevelTests(unittest.TestCase):
    def test_parses_program_wide_unit_groups_without_explicit_level_headers(self):
        raw_text = """
Requirements
120 units total (Levels I to IV), of which 48 units may be Level I

30 units
from

the Level I program completed prior to admission to the program. (See Admission above.)
6 units
ECON 2Z03 - Intermediate Microeconomics I
ECON 2ZZ3 - Intermediate Microeconomics II
12 units
ECON 2B03 - Analysis of Economic Data
ECON 2H03 - Intermediate Macroeconomics I
ECON 2HH3 - Intermediate Macroeconomics II
ECON 4A03 - Honours Economic Analysis
"""

        grouped, flat_courses = GET_ALL_PROGRAMS.parse_requirements_by_level(raw_text)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["level"], "I-IV")
        self.assertEqual(grouped[0]["total_units"], 120)
        self.assertEqual([group["units"] for group in grouped[0]["unit_groups"]], ["30", "6", "12"])
        self.assertTrue(grouped[0]["unit_groups"][0]["choose_one"])
        self.assertFalse(grouped[0]["unit_groups"][1]["choose_one"])
        self.assertEqual(
            grouped[0]["unit_groups"][0]["requirements"],
            [
                {
                    "type": "text",
                    "text": "the Level I program completed prior to admission to the program. (See Admission above.)",
                    "course_code": None,
                }
            ],
        )
        self.assertEqual(
            [item["course_code"] for item in grouped[0]["unit_groups"][1]["requirements"]],
            ["ECON 2Z03", "ECON 2ZZ3"],
        )
        self.assertEqual(
            [item["course_code"] for item in grouped[0]["unit_groups"][2]["requirements"]],
            ["ECON 2B03", "ECON 2H03", "ECON 2HH3", "ECON 4A03"],
        )
        self.assertIn("ECON 2Z03 - Intermediate Microeconomics I", flat_courses)

    def test_parses_unit_ranges_as_strings(self):
        raw_text = """
Requirements
Level I: 30 Units
0-3 units
ANTHROP 1AA3 - Introduction to Anthropology: Sex, Food and Death
ANTHROP 1AB3 - Introduction to Anthropology: Race, Religion, and Social Justice
(See Note 2)

33-36 units
Electives, of which at least six units must be taken from outside of Anthropology
"""
        grouped, _ = GET_ALL_PROGRAMS.parse_requirements_by_level(raw_text)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["unit_groups"][0]["units"], "0-3")
        self.assertEqual(grouped[0]["unit_groups"][1]["units"], "33-36")
        self.assertFalse(grouped[0]["unit_groups"][0]["choose_one"])
        self.assertFalse(grouped[0]["unit_groups"][1]["choose_one"])


if __name__ == "__main__":
    unittest.main()
