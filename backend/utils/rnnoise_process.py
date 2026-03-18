import os
import logging
import subprocess
import uuid
import shlex
from pathlib import Path
import multiprocessing
import time
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Use local model file instead of system path
# Get the directory where this script is located, then go up one level to backend/
script_dir = Path(__file__).parent
model_path = script_dir.parent / "models" / "std.rnnn"
RNNOISE_OUTPUT_DIR = "rnnoise_output"
MAX_DIR_SIZE_MB = 1024  # 1GB limit


def get_file_info(file_path: Path) -> Tuple[float, float]:
    """Get file size in MB and modification time."""
    return (file_path.stat().st_size / (1024 * 1024), file_path.stat().st_mtime)


def cleanup_old_files():
    """Remove oldest files if directory size exceeds MAX_DIR_SIZE_MB."""
    try:
        # Get all files in the directory with their sizes and modification times
        files: List[Tuple[Path, float, float]] = []
        total_size = 0

        for file_path in Path(RNNOISE_OUTPUT_DIR).glob("*.wav"):
            size_mb, mtime = get_file_info(file_path)
            files.append((file_path, size_mb, mtime))
            total_size += size_mb

        # If we're under the limit, no cleanup needed
        if total_size <= MAX_DIR_SIZE_MB:
            return

        # Sort files by modification time (oldest first)
        files.sort(key=lambda x: x[2])

        # Remove oldest files until we're under the limit
        for file_path, size_mb, _ in files:
            if total_size <= MAX_DIR_SIZE_MB:
                break
            try:
                os.remove(file_path)
                total_size -= size_mb
                logger.info(f"Cleaned up old file: {file_path}")
            except Exception as e:
                logger.warning(f"Error cleaning up {file_path}: {e}")

    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")


def denoise_with_rnnoise(input_path: str) -> str:
    # Verify model file exists
    if not model_path.exists():
        logger.error(
            f"RNNoise model file not found at {model_path}. Expected a file with '.rnnn' extension."
        )
        return ""
    # Verify input file exists and is readable
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        logger.error(f"Input file not found at {input_path}")
        return ""

    try:
        with open(input_path, "rb"):
            pass
    except Exception as e:
        logger.error(
            f"Input file is not readable or accessible: {input_path}. Exception: {e}"
        )
        return ""

    # Create output directory and verify write permissions
    try:
        os.makedirs(RNNOISE_OUTPUT_DIR, exist_ok=True)
        # Test actual write capability by trying to create a temporary file
        test_file = Path(RNNOISE_OUTPUT_DIR) / ".write_test"
        test_file.touch()
        test_file.unlink()  # Clean up the test file
    except Exception as e:
        logger.error(
            f"Cannot create or write to output directory {RNNOISE_OUTPUT_DIR}: {e}"
        )
        return ""
    # Generate output filename
    base_name = Path(input_path).stem
    run_id = str(uuid.uuid4()).replace(
        "-", ""
    )  # Full UUID without hyphens for uniqueness
    output_path = Path(RNNOISE_OUTPUT_DIR) / f"{base_name}_{run_id}_denoised.wav"
    output_path = output_path.as_posix()

    # Calculate optimal thread count (leave one core free for system)
    thread_count = max(
        1, multiprocessing.cpu_count() - 1
    )  # Use the working command syntax with performance optimizations
    cmd = [
        "ffmpeg",
        "-threads",
        str(thread_count),  # Use multiple threads for FFmpeg operations
        "-thread_queue_size",
        "1024",  # Increase thread queue size
        "-i",
        str(input_path),
        "-af",
        f"arnndn=m={model_path.as_posix()}",
        "-y",
        "-bufsize",
        "16M",  # Increase buffer size
        "-maxrate",
        "16M",  # Set maximum bitrate
        output_path,
    ]
    # Print command with proper shell escaping for debugging
    logger.debug("Running FFmpeg command: %s", " ".join(shlex.quote(str(arg)) for arg in cmd))

    try:
        # Run FFmpeg at normal priority for better compatibility
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        logger.debug("FFmpeg stdout: %s", result.stdout)
        logger.debug("FFmpeg stderr: %s", result.stderr)

        # Verify output file was created and has content (atomic check to avoid race conditions)
        try:
            if os.path.getsize(output_path) == 0:
                logger.error("Output file was created but is empty")
                return ""
        except FileNotFoundError:
            logger.error("Output file was not created")
            return ""
        except PermissionError:
            logger.error("Cannot access output file (permission denied)")
            return ""  # Clean up old files if needed
        cleanup_old_files()

        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(
            "RNNoise processing failed! Return code: %s, stderr: %s",
            e.returncode,
            e.stderr,
        )
        return ""

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return ""
