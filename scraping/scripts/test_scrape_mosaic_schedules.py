import importlib.util
import pathlib
import sys
import types
import unittest


sys.modules.setdefault("dotenv", types.SimpleNamespace(load_dotenv=lambda *_args, **_kwargs: None))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=lambda *_args, **_kwargs: None))
sys.modules.setdefault(
    "playwright",
    types.SimpleNamespace(async_api=types.SimpleNamespace(async_playwright=None)),
)
sys.modules.setdefault(
    "playwright.async_api",
    types.SimpleNamespace(
        async_playwright=None,
        Page=object,
        Frame=object,
        Browser=object,
    ),
)


class _Console:
    def print(self, *_args, **_kwargs):
        pass


class _Table:
    last_instance = None

    def __init__(self, *_args, **_kwargs):
        self.columns = []
        self.rows = []
        _Table.last_instance = self

    def add_column(self, *_args, **_kwargs):
        self.columns.append(_args[0] if _args else "")

    def add_row(self, *_args, **_kwargs):
        self.rows.append(_args)


sys.modules.setdefault(
    "rich.console",
    types.SimpleNamespace(Console=lambda *_args, **_kwargs: _Console()),
)
sys.modules.setdefault("rich.table", types.SimpleNamespace(Table=_Table))
sys.modules.setdefault(
    "rich.live",
    types.SimpleNamespace(Live=lambda *_args, **_kwargs: None),
)
sys.modules.setdefault("rich.panel", types.SimpleNamespace(Panel=object))


SCRIPT_PATH = pathlib.Path(__file__).resolve().parent / "scrape_mosaic_schedules.py"
SPEC = importlib.util.spec_from_file_location("scrape_mosaic_schedules", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
SCRAPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCRAPER)


class MissingSectionSkipTests(unittest.TestCase):
    def setUp(self):
        SCRAPER.worker_states.clear()
        _Table.last_instance = None

    def test_parses_selected_letters_from_common_formats(self):
        self.assertEqual(SCRAPER.parse_selected_letters("CD"), ["C", "D"])
        self.assertEqual(SCRAPER.parse_selected_letters("c,d"), ["C", "D"])
        self.assertEqual(SCRAPER.parse_selected_letters(" C D C "), ["C", "D"])

    def test_rejects_selected_letters_with_invalid_characters(self):
        with self.assertRaises(ValueError):
            SCRAPER.parse_selected_letters("C,1")

        with self.assertRaises(ValueError):
            SCRAPER.parse_selected_letters("C-D")

    def test_builds_letter_chunks_from_selected_letters(self):
        self.assertEqual(
            SCRAPER.build_letter_chunks(["C", "D", "E"], headless=True, one_worker_per_letter=True),
            ([["C"], ["D"], ["E"]], 3),
        )
        self.assertEqual(
            SCRAPER.build_letter_chunks(["C", "D", "E"], headless=False, one_worker_per_letter=True),
            ([["C"], ["D"], ["E"]], 3),
        )

    def test_builds_default_letter_chunks_in_pairs_when_headless(self):
        self.assertEqual(
            SCRAPER.build_letter_chunks(["A", "B", "C"], headless=True, one_worker_per_letter=False),
            ([["A", "B"], ["C"]], 2),
        )
        self.assertEqual(
            SCRAPER.build_letter_chunks(["A", "B", "C"], headless=False, one_worker_per_letter=False),
            ([["A", "B", "C"]], 1),
        )

    def test_validates_courses_per_worker(self):
        self.assertEqual(SCRAPER.validate_courses_per_worker(100), 100)
        self.assertEqual(SCRAPER.validate_courses_per_worker("25"), 25)

        with self.assertRaises(ValueError):
            SCRAPER.validate_courses_per_worker(0)

    def test_splits_large_letters_by_courses_per_worker(self):
        assignments = SCRAPER.build_worker_assignments(
            ["C"],
            {"C": 250},
            courses_per_worker=100,
        )

        self.assertEqual(
            assignments,
            [
                [{"letter": "C", "start": 0, "end": 100, "total": 250}],
                [{"letter": "C", "start": 100, "end": 200, "total": 250}],
                [{"letter": "C", "start": 200, "end": 250, "total": 250}],
            ],
        )

    def test_packs_small_adjacent_letters_until_threshold(self):
        assignments = SCRAPER.build_worker_assignments(
            ["D", "E", "F", "G"],
            {"D": 3, "E": 10, "F": 20, "G": 90},
            courses_per_worker=100,
        )

        self.assertEqual(
            assignments,
            [
                [
                    {"letter": "D", "start": 0, "end": 3, "total": 3},
                    {"letter": "E", "start": 0, "end": 10, "total": 10},
                    {"letter": "F", "start": 0, "end": 20, "total": 20},
                ],
                [{"letter": "G", "start": 0, "end": 90, "total": 90}],
            ],
        )

    def test_skips_letters_with_no_courses_when_assigning_workers(self):
        assignments = SCRAPER.build_worker_assignments(
            ["A", "B"],
            {"A": 0, "B": 2},
            courses_per_worker=100,
        )

        self.assertEqual(assignments, [[{"letter": "B", "start": 0, "end": 2, "total": 2}]])

    def test_resolves_title_fallback_to_catalog_course_code(self):
        catalog_courses = [
            {
                "course_name": "COMPSCI 1DM3 - Discrete Mathematics for Computer Science",
            },
            {
                "course_name": "MATH 1B03 - Linear Algebra I",
            },
        ]
        title_code_map = SCRAPER.build_course_title_code_map(catalog_courses)

        course_code = SCRAPER.resolve_scraped_course_code(
            scraped_code="Discrete Mathematics for Computer Science",
            course_title="Discrete Mathematics for Computer Science",
            title_code_map=title_code_map,
        )

        self.assertEqual(course_code, "COMPSCI 1DM3")

    def test_keeps_scraped_code_when_it_already_has_subject_and_number(self):
        title_code_map = {
            "Discrete Mathematics for Computer Science": "COMPSCI 1DM3",
        }

        course_code = SCRAPER.resolve_scraped_course_code(
            scraped_code="COMPSCI 1DM3",
            course_title="Discrete Mathematics for Computer Science",
            title_code_map=title_code_map,
        )

        self.assertEqual(course_code, "COMPSCI 1DM3")

    def test_worker_state_and_table_include_active_letter_range(self):
        SCRAPER.update_worker(1, active="C 101-200", current="Clicking course", reset=True)

        SCRAPER.generate_table()

        self.assertEqual(SCRAPER.worker_states[1]["active"], "C 101-200")
        table = _Table.last_instance
        self.assertIn("Active", table.columns)
        self.assertEqual(table.rows[0][2], "C 101-200")
        self.assertEqual(table.rows[0][3], "Clicking course")

    def test_groups_only_courses_with_sections_by_term(self):
        rows = [
            ("COMPSCI 1MD3", "Fall 2026"),
            ("MATH 1A03", "Fall 2026"),
            ("COMPSCI 1MD3", "Winter 2027"),
        ]

        grouped = SCRAPER.group_existing_section_codes_by_term(rows)

        self.assertEqual(grouped["Fall 2026"], {"COMPSCI 1MD3", "MATH 1A03"})
        self.assertEqual(grouped["Winter 2027"], {"COMPSCI 1MD3"})
        self.assertNotIn("Spring/Summer 2027", grouped)

    def test_merges_new_results_into_existing_term_without_dropping_courses(self):
        existing = [
            {
                "term": "Fall 2026",
                "courses": [
                    {"course_code": "COMPSCI 1MD3", "sections": [{"section_name": "C01-LEC"}]},
                ],
            },
            {
                "term": "Winter 2027",
                "courses": [
                    {"course_code": "MATH 1A03", "sections": [{"section_name": "C01-LEC"}]},
                ],
            },
        ]
        scraped_missing = [
            {"course_code": "PHYSICS 1A03", "sections": [{"section_name": "C02-LEC"}]},
        ]

        merged = SCRAPER.merge_term_results(existing, "Fall 2026", scraped_missing)

        self.assertEqual([term["term"] for term in merged], ["Fall 2026", "Winter 2027"])
        self.assertEqual(
            [course["course_code"] for course in merged[0]["courses"]],
            ["COMPSCI 1MD3", "PHYSICS 1A03"],
        )
        self.assertEqual(
            [course["course_code"] for course in merged[1]["courses"]],
            ["MATH 1A03"],
        )

    def test_merge_replaces_duplicate_course_with_latest_scrape(self):
        existing = [
            {
                "term": "Fall 2026",
                "courses": [
                    {"course_code": "COMPSCI 1MD3", "sections": [{"section_name": "OLD"}]},
                ],
            },
        ]
        scraped_missing = [
            {"course_code": "COMPSCI 1MD3", "sections": [{"section_name": "NEW"}]},
        ]

        merged = SCRAPER.merge_term_results(existing, "Fall 2026", scraped_missing)

        self.assertEqual(merged[0]["courses"][0]["sections"], [{"section_name": "NEW"}])


if __name__ == "__main__":
    unittest.main()
