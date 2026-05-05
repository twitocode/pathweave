import importlib.util
import pathlib
import unittest

TRANSFORM_PATH = pathlib.Path(__file__).resolve().parent / "schedule_seed_transform.py"
SPEC = importlib.util.spec_from_file_location("schedule_seed_transform", TRANSFORM_PATH)
assert SPEC is not None
assert SPEC.loader is not None
TRANSFORM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSFORM)


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


if __name__ == "__main__":
    unittest.main()
