import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


from ingest_shapefile_zip import process_shapefile_zip  # noqa: E402
from load_roads import process_geojson  # noqa: E402

from api.services.job_status import update_job_status  # noqa: E402

INCOMING_DIR = PROJECT_DIR / "incoming"
ARCHIVE_DIR = PROJECT_DIR / "archive"
FAILED_DIR = PROJECT_DIR / "failed"
LOG_DIR = PROJECT_DIR / "logs"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REJECTED_DIR = PROJECT_DIR / "data" / "rejected"

FME_EXE = Path(r"C:\Program Files\FME\fme.exe")
FME_WORKSPACE = PROJECT_DIR / "fme_workspaces" / "roads_to_postgis.fmw"

SUPPORTED_EXTENSIONS = {".geojson", ".zip"}

PROCESSING_LOCK = Lock()
PROCESSED_PATHS: dict[Path, float] = {}

EVENT_DEBOUNCE_SECONDS = 3


def write_log(message: str) -> None:
    """Write a timestamped message to the console and log file."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"

    print(full_message, flush=True)

    log_file = LOG_DIR / "watcher_realtime_log.txt"

    with log_file.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(full_message + "\n")


def create_required_directories() -> None:
    """Create folders required by the workflow."""

    for directory in (
        INCOMING_DIR,
        ARCHIVE_DIR,
        FAILED_DIR,
        LOG_DIR,
        PROCESSED_DIR,
        REJECTED_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def build_destination_path(
    destination_dir: Path,
    source_file: Path,
) -> Path:
    """Create a unique archived or failed filename."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    return destination_dir / (f"{source_file.stem}_{timestamp}" f"{source_file.suffix}")


def extract_job_id(
    input_file: Path,
) -> str | None:
    """Extract the job ID from an uploaded filename."""

    if "__" not in input_file.name:
        return None

    return input_file.name.split("__", 1)[0]


def extract_original_filename(
    input_file: Path,
) -> str:
    """Return the filename before the job-ID prefix."""

    if "__" not in input_file.name:
        return input_file.name

    return input_file.name.split("__", 1)[1]


def wait_until_file_is_ready(
    file_path: Path,
    attempts: int = 10,
    delay_seconds: float = 1.0,
) -> bool:
    """Wait until an uploaded file has finished writing."""

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


def run_fme(
    input_file: Path,
) -> bool:
    """Process a GeoJSON file using the local FME workspace."""

    if not FME_EXE.exists():
        write_log(f"FME executable not found: {FME_EXE}")
        return False

    if not FME_WORKSPACE.exists():
        write_log(f"FME workspace not found: {FME_WORKSPACE}")
        return False

    command = [
        str(FME_EXE),
        str(FME_WORKSPACE),
        "--SourceDataset_GEOJSON_3",
        str(input_file),
    ]

    write_log(f"Starting FME processing: {input_file.name}")

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
        write_log(f"FME completed successfully: " f"{input_file.name}")
        return True

    write_log(f"FME failed for {input_file.name}; " f"exit code: {result.returncode}")

    return False


def process_zip(
    input_file: Path,
) -> bool:
    """Ingest a Shapefile ZIP and load its roads into PostGIS."""

    safe_stem = input_file.stem.replace(
        "__",
        "_",
    )

    output_file = PROCESSED_DIR / f"{safe_stem}_ingested.geojson"

    rejected_file = REJECTED_DIR / f"{safe_stem}_rejected.geojson"

    try:
        write_log(f"Starting Shapefile ZIP ingestion: " f"{input_file.name}")

        valid_count, rejected_count = process_shapefile_zip(
            input_zip=input_file,
            output_file=output_file,
            rejected_file=rejected_file,
        )

        if valid_count == 0:
            raise RuntimeError("The Shapefile ZIP contained no valid roads.")

        write_log(
            f"ZIP ingestion completed: "
            f"{valid_count} accepted, "
            f"{rejected_count} rejected."
        )

        process_geojson(output_file)

        write_log(f"PostGIS loading completed: " f"{output_file.name}")

        return True

    except Exception as error:
        write_log(f"ZIP processing failed: {error}")
        return False


def move_processed_file(
    input_file: Path,
    destination_dir: Path,
) -> Path:
    """Move the original upload to archive or failed."""

    destination = build_destination_path(
        destination_dir,
        input_file,
    )

    shutil.move(
        str(input_file),
        str(destination),
    )

    return destination


def process_file(
    input_file: Path,
) -> None:
    """Route one uploaded file through its correct workflow."""

    with PROCESSING_LOCK:
        if not input_file.exists():
            return

        suffix = input_file.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            write_log(f"Ignored unsupported file: " f"{input_file.name}")
            return

        job_id = extract_job_id(input_file)
        original_filename = extract_original_filename(input_file)

        write_log(f"Detected new {suffix} file: " f"{input_file.name}")

        if job_id:
            update_job_status(
                job_id=job_id,
                status="PROCESSING",
                filename=original_filename,
                message="ETL processing started.",
            )

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
                destination = move_processed_file(
                    input_file,
                    FAILED_DIR,
                )

                write_log(f"Moved unready file to failed: " f"{destination.name}")

            return

        if suffix == ".zip":
            success = process_zip(input_file)
        else:
            success = run_fme(input_file)

        if success:
            destination = move_processed_file(
                input_file,
                ARCHIVE_DIR,
            )

            write_log(f"Moved file to archive: " f"{destination.name}")

            if job_id:
                update_job_status(
                    job_id=job_id,
                    status="SUCCESS",
                    filename=original_filename,
                    message=("ETL processing completed " "successfully."),
                )

        else:
            destination = move_processed_file(
                input_file,
                FAILED_DIR,
            )

            write_log(f"Moved file to failed: " f"{destination.name}")

            if job_id:
                update_job_status(
                    job_id=job_id,
                    status="FAILED",
                    filename=original_filename,
                    message="ETL processing failed.",
                )


class SpatialFileEventHandler(FileSystemEventHandler):
    """React when a supported spatial file enters incoming."""

    def _handle_path(
        self,
        raw_path: str,
    ) -> None:
        file_path = Path(raw_path)

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return

        now = time.time()
        last_processed = PROCESSED_PATHS.get(file_path)

        if last_processed is not None and now - last_processed < EVENT_DEBOUNCE_SECONDS:
            return

        PROCESSED_PATHS[file_path] = now
        process_file(file_path)

    def on_created(self, event) -> None:
        if not event.is_directory:
            self._handle_path(event.src_path)

    def on_moved(self, event) -> None:
        if not event.is_directory:
            self._handle_path(event.dest_path)


def process_existing_files() -> None:
    """Process supported files left in incoming at startup."""

    existing_files = sorted(
        path
        for path in INCOMING_DIR.iterdir()
        if (path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)
    )

    for input_file in existing_files:
        process_file(input_file)


def main() -> None:
    """Start the real-time folder watcher."""

    create_required_directories()

    event_handler = SpatialFileEventHandler()
    observer = Observer()

    observer.schedule(
        event_handler,
        str(INCOMING_DIR),
        recursive=False,
    )

    write_log("Real-time folder watcher started.")
    write_log(f"Watching: {INCOMING_DIR}")
    write_log("Supported files: .geojson, .zip")

    if not FME_EXE.exists() or not FME_WORKSPACE.exists():
        write_log("FME is not fully configured. " "ZIP processing remains available.")

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
