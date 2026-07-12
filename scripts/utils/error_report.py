import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_DIR / "logs"
ERROR_REPORT = LOG_DIR / "error_report.json"


def save_error_report(errors):
    LOG_DIR.mkdir(exist_ok=True)

    with open(ERROR_REPORT, "w", encoding="utf-8") as file:
        json.dump(errors, file, indent=2)
