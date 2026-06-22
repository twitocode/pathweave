import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parent / "publish_scrape_run.py"
SPEC = importlib.util.spec_from_file_location("publish_scrape_run", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
PUBLISHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PUBLISHER)


class BuildArtifactsPayloadTests(unittest.TestCase):
    def test_builds_payload_from_existing_scraper_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = pathlib.Path(tmp)
            (data_dir / "all_courses.json").write_text(
                json.dumps([{"course_name": "COMPSCI 1DM3 - Discrete Mathematics"}])
            )
            (data_dir / "all_programs_with_requirements.json").write_text(
                json.dumps([{"program_name": "Computer Science", "requirements": ["COMPSCI 1DM3"]}])
            )
            (data_dir / "rmp_data.json").write_text(
                json.dumps({"professors": [{"id": "rmp_1", "name": "Jane Doe"}]})
            )
            (data_dir / "all_possible_schedules.json").write_text(
                json.dumps([{"term": "Fall 2026", "courses": []}])
            )

            payload = PUBLISHER.build_artifacts_payload(data_dir)

            self.assertEqual(payload["courses"][0]["courseName"], "COMPSCI 1DM3 - Discrete Mathematics")
            self.assertEqual(payload["programs"][0]["programName"], "Computer Science")
            self.assertEqual(payload["teachers"][0]["id"], "rmp_1")
            self.assertEqual(payload["schedules"][0]["term"], "Fall 2026")


class RequestTests(unittest.TestCase):
    def test_builds_internal_authorization_request(self):
        request = PUBLISHER.build_json_request(
            "http://localhost:8000/internal/scrape-runs",
            "secret",
            {"source": "manual"},
        )

        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers["Authorization"], "Bearer secret")
        self.assertEqual(request.headers["Content-type"], "application/json")


if __name__ == "__main__":
    unittest.main()
