import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from typing import Any
from dotenv import load_dotenv

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"


load_dotenv()

def load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_artifacts_payload(data_dir: pathlib.Path = DATA_DIR) -> dict[str, Any]:
    rmp_data = load_json(data_dir / "rmp_data.json")
    return {
        "courses": load_json(data_dir / "all_courses.json"),
        "programs": load_json(data_dir / "all_programs_with_requirements.json"),
        "teachers": rmp_data.get("professors", []),
        "schedules": load_json(data_dir / "all_possible_schedules.json"),
    }


def build_json_request(url: str, token: str, payload: dict[str, Any]) -> urllib.request.Request:
    body = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def post_json(url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = build_json_request(url, token, payload)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise RuntimeError(f"POST {url} failed with {e.code}: {detail}") from e


def run_publish(
    api_base_url: str,
    token: str,
    data_dir: pathlib.Path = DATA_DIR,
    source: str = "scraping",
    promote: bool = True,
) -> dict[str, Any]:
    if not token:
        raise ValueError("INTERNAL_SERVICE_TOKEN is required")

    api_base_url = api_base_url.rstrip("/")
    run = post_json(
        f"{api_base_url}/internal/scrape-runs",
        token,
        {"source": source, "metadata": {"publisher": "publish_scrape_run.py"}},
    )
    run_id = run["ID"] if "ID" in run else run["id"]

    artifacts = build_artifacts_payload(data_dir)
    staged = post_json(
        f"{api_base_url}/internal/scrape-runs/{run_id}/artifacts",
        token,
        artifacts,
    )

    result: dict[str, Any] = {"run": run, "staged": staged}
    if promote:
        result["promoted"] = post_json(
            f"{api_base_url}/internal/scrape-runs/{run_id}/promote",
            token,
            {},
        )
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish scraper artifacts to the Go ingest API.")
    parser.add_argument("--api-base-url", default=os.getenv("GO_API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--token", default=os.getenv("INTERNAL_SERVICE_TOKEN", ""))
    parser.add_argument("--data-dir", type=pathlib.Path, default=DATA_DIR)
    parser.add_argument("--source", default="scraping")
    parser.add_argument("--no-promote", action="store_true", help="Stage artifacts without promoting them.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = run_publish(
        api_base_url=args.api_base_url,
        token=args.token,
        data_dir=args.data_dir,
        source=args.source,
        promote=not args.no_promote,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
