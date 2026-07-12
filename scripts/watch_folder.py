import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]

INCOMING_DIR = PROJECT_DIR / "incoming"
ARCHIVE_DIR = PROJECT_DIR / "archive"
FAILED_DIR = PROJECT_DIR / "failed"
LOG_DIR = PROJECT_DIR / "logs"

FME_EXE = Path(r"C:\Program Files\FME\fme.exe")
FME_WORKSPACE = PROJECT_DIR / "fme_workspaces" / "roads_to_postgis.fmw"

POLL_INTERVAL_SECONDS = 5


def write_log(message: str) -> None:
    """Write a timestamped message to terminal and watcher log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"

    print(full_message)

    log_file = LOG_DIR / "watcher_log.txt"
    with log_file.open("a", encoding="utf-8") as file:
        file.write(full_message + "\n")


def create_required_directories() -> None:
    """Make sure processing folders exist."""
    for directory in (INCOMING_DIR, ARCHIVE_DIR, FAILED_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def build_destination_path(destination_dir: Path, source_file: Path) -> Path:
    """
    Create a timestamped destination filename.

    This prevents overwriting an older archived or failed file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return destination_dir / f"{source_file.stem}_{timestamp}{source_file.suffix}"


def run_fme(input_file: Path) -> bool:
    """Run the FME workspace for one GeoJSON file."""
    command = [
        str(FME_EXE),
        str(FME_WORKSPACE),
        "--SourceDataset_GEOJSON_3",
        str(input_file),
    ]

    write_log(f"Starting FME for: {input_file.name}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        write_log(f"Could not start FME: {error}")
        return False

    if result.stdout:
        write_log("FME output:")
        print(result.stdout)

    if result.stderr:
        write_log("FME error output:")
        print(result.stderr)

    if result.returncode == 0:
        write_log(f"FME completed successfully for: {input_file.name}")
        return True

    write_log(f"FME failed for {input_file.name}. " f"Exit code: {result.returncode}")
    return False


def process_file(input_file: Path) -> None:
    """Process one file and move it to archive or failed."""
    success = run_fme(input_file)

    if success:
        destination = build_destination_path(ARCHIVE_DIR, input_file)
        shutil.move(str(input_file), str(destination))
        write_log(f"Moved file to archive: {destination.name}")
    else:
        destination = build_destination_path(FAILED_DIR, input_file)
        shutil.move(str(input_file), str(destination))
        write_log(f"Moved file to failed: {destination.name}")


def main() -> None:
    create_required_directories()

    if not FME_EXE.exists():
        raise FileNotFoundError(f"FME executable not found: {FME_EXE}")

    if not FME_WORKSPACE.exists():
        raise FileNotFoundError(f"FME workspace not found: {FME_WORKSPACE}")

    write_log("Folder watcher started.")
    write_log(f"Watching: {INCOMING_DIR}")
    write_log("Press Ctrl+C to stop.")

    try:
        while True:
            geojson_files = sorted(INCOMING_DIR.glob("*.geojson"))

            for geojson_file in geojson_files:
                process_file(geojson_file)

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        write_log("Folder watcher stopped by user.")


if __name__ == "__main__":
    main()
