import json
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_DIR / "logs"
SUMMARY_REPORT = LOG_DIR / "summary_report.json"


def save_summary_report(total_features, valid_count, invalid_count, input_file):
    LOG_DIR.mkdir(exist_ok=True)

    status = "SUCCESS" if invalid_count == 0 else "COMPLETED_WITH_ERRORS"

    summary = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_file": input_file,
        "total_features": total_features,
        "valid_features_loaded": valid_count,
        "invalid_features_skipped": invalid_count,
        "status": status,
    }

    with open(SUMMARY_REPORT, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
