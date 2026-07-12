import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Allow this script to import modules from the project root, such as:
# api.services.job_status
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from api.services.job_status import update_job_status  # noqa: E402

INCOMING_DIR = PROJECT_DIR / "incoming"
ARCHIVE_DIR = PROJECT_DIR / "archive"
FAILED_DIR = PROJECT_DIR / "failed"
LOG_DIR = PROJECT_DIR / "logs"

FME_EXE = Path(r"C:\Program Files\FME\fme.exe")
FME_WORKSPACE = PROJECT_DIR / "fme_workspaces" / "roads_to_postgis.fmw"


# ---------------------------------------------------------------------
# Watcher configuration
# ---------------------------------------------------------------------

# Prevent multiple files from being processed simultaneously.
PROCESSING_LOCK = Lock()

# Windows may generate more than one event for the same file.
PROCESSED_PATHS: dict[Path, float] = {}

EVENT_DEBOUNCE_SECONDS = 3


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------


def write_log(message: str) -> None:
    """Write a timestamped message to the terminal and watcher log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"

    print(full_message, flush=True)

    log_file = LOG_DIR / "watcher_realtime_log.txt"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(full_message + "\n")


# ---------------------------------------------------------------------
# Directory and filename helpers
# ---------------------------------------------------------------------


def create_required_directories() -> None:
    """Create the required ETL folders if they do not exist."""
    for directory in (
        INCOMING_DIR,
        ARCHIVE_DIR,
        FAILED_DIR,
        LOG_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def build_destination_path(
    destination_dir: Path,
    source_file: Path,
) -> Path:
    """Create a timestamped archive or failed filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return destination_dir / (f"{source_file.stem}_{timestamp}{source_file.suffix}")


def extract_job_id(input_file: Path) -> str | None:
    """
    Extract the job ID from a filename such as:

    abc123__roads.geojson
    """
    if "__" not in input_file.name:
        return None

    return input_file.name.split("__", 1)[0]


def extract_original_filename(input_file: Path) -> str:
    """
    Return the original uploaded filename.

    abc123__roads.geojson becomes roads.geojson.
    """
    if "__" not in input_file.name:
        return input_file.name

    return input_file.name.split("__", 1)[1]


# ---------------------------------------------------------------------
# File readiness check
# ---------------------------------------------------------------------


def wait_until_file_is_ready(
    file_path: Path,
    attempts: int = 10,
    delay_seconds: float = 1.0,
) -> bool:
    """
    Wait until a file has finished copying.

    A Windows creation event may be triggered before the complete file
    has been written to disk.
    """
    previous_size = -1

    for _ in range(attempts):
        if not file_path.exists():
            return False

        try:
            current_size = file_path.stat().st_size
        except OSError:
            time.sleep(delay_seconds)
            continue

        if current_size > 0 and current_size == previous_size:
            return True

        previous_size = current_size
        time.sleep(delay_seconds)

    return False


# ---------------------------------------------------------------------
# FME execution
# ---------------------------------------------------------------------


def run_fme(input_file: Path) -> bool:
    """Run the FME workspace for one GeoJSON input file."""
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
        print(result.stdout, flush=True)

    if result.stderr:
        write_log("FME error output:")
        print(result.stderr, flush=True)

    if result.returncode == 0:
        write_log(f"FME completed successfully: {input_file.name}")
        return True

    write_log(f"FME failed for {input_file.name}; " f"exit code: {result.returncode}")

    return False


# ---------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------


def process_file(input_file: Path) -> None:
    """Process one GeoJSON and update its job status."""
    with PROCESSING_LOCK:
        if not input_file.exists():
            return

        if input_file.suffix.lower() != ".geojson":
            write_log(f"Ignored unsupported file: {input_file.name}")
            return

        job_id = extract_job_id(input_file)
        original_filename = extract_original_filename(input_file)

        write_log(f"Detected new GeoJSON: {input_file.name}")

        if job_id:
            update_job_status(
                job_id=job_id,
                status="PROCESSING",
                filename=original_filename,
                message="FME processing started.",
            )

        # Wait until the upload or copy operation has fully completed.
        if not wait_until_file_is_ready(input_file):
            write_log(f"File was not ready: {input_file.name}")

            if job_id:
                update_job_status(
                    job_id=job_id,
                    status="FAILED",
                    filename=original_filename,
                    message=("The uploaded file was not ready " "for processing."),
                )

            if input_file.exists():
                destination = build_destination_path(
                    FAILED_DIR,
                    input_file,
                )

                shutil.move(
                    str(input_file),
                    str(destination),
                )

                write_log("Moved unready file to failed: " f"{destination.name}")

            return

        success = run_fme(input_file)

        if success:
            destination = build_destination_path(
                ARCHIVE_DIR,
                input_file,
            )

            shutil.move(
                str(input_file),
                str(destination),
            )

            write_log(f"Moved file to archive: {destination.name}")

            if job_id:
                update_job_status(
                    job_id=job_id,
                    status="SUCCESS",
                    filename=original_filename,
                    message=("FME processing completed successfully."),
                )

        else:
            destination = build_destination_path(
                FAILED_DIR,
                input_file,
            )

            shutil.move(
                str(input_file),
                str(destination),
            )

            write_log(f"Moved file to failed: {destination.name}")

            if job_id:
                update_job_status(
                    job_id=job_id,
                    status="FAILED",
                    filename=original_filename,
                    message="FME processing failed.",
                )


# ---------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------


class GeoJsonEventHandler(FileSystemEventHandler):
    """React when a GeoJSON file is added to incoming."""

    def _handle_path(self, raw_path: str) -> None:
        file_path = Path(raw_path)

        if file_path.suffix.lower() != ".geojson":
            return

        now = time.time()
        last_processed = PROCESSED_PATHS.get(file_path)

        if last_processed is not None and now - last_processed < EVENT_DEBOUNCE_SECONDS:
            return

        PROCESSED_PATHS[file_path] = now
        process_file(file_path)

    def on_created(self, event) -> None:
        """Handle files newly created inside incoming."""
        if not event.is_directory:
            self._handle_path(event.src_path)

    def on_moved(self, event) -> None:
        """Handle files moved into incoming."""
        if not event.is_directory:
            self._handle_path(event.dest_path)


# ---------------------------------------------------------------------
# Existing file handling
# ---------------------------------------------------------------------


def process_existing_files() -> None:
    """Process GeoJSON files already present at startup."""
    existing_files = sorted(INCOMING_DIR.glob("*.geojson"))

    for input_file in existing_files:
        process_file(input_file)


# ---------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------


def main() -> None:
    """Start the real-time watcher."""
    create_required_directories()

    if not FME_EXE.exists():
        raise FileNotFoundError(f"FME executable not found: {FME_EXE}")

    if not FME_WORKSPACE.exists():
        raise FileNotFoundError(f"FME workspace not found: {FME_WORKSPACE}")

    event_handler = GeoJsonEventHandler()
    observer = Observer()

    observer.schedule(
        event_handler,
        str(INCOMING_DIR),
        recursive=False,
    )

    write_log("Real-time folder watcher started.")
    write_log(f"Watching: {INCOMING_DIR}")
    write_log("Press Ctrl+C to stop.")

    # Process files left behind before starting the observer.
    process_existing_files()

    observer.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        write_log("Stopping real-time folder watcher.")
        observer.stop()

    observer.join()

    write_log("Real-time folder watcher stopped.")


if __name__ == "__main__":
    main()
