import os
import subprocess
import uuid
import shlex
from pathlib import Path
import multiprocessing
import time
from typing import List, Tuple

# Use local model file instead of system path
# Get the directory where this script is located, then go up one level to backend/
script_dir = Path(__file__).parent
model_path = script_dir.parent / "std.rnnn"
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
                print(f"Cleaned up old file: {file_path}")
            except Exception as e:
                print(f"Error cleaning up {file_path}: {e}")

    except Exception as e:
        print(f"Error during cleanup: {e}")


def denoise_with_rnnoise(input_path: str) -> str:
    # Verify model file exists
    if not model_path.exists():
        print(
            f"Error: RNNoise model file not found at {model_path}. Expected a file with '.rnnn' extension."
        )
        return ""  # Verify input file exists and is readable
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        print(f"Error: Input file not found at {input_path}")
        return ""

    try:
        with open(input_path, "rb"):
            pass
    except Exception as e:
        print(
            f"Error: Input file is not readable or accessible: {input_path}. Exception: {e}"
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
        print(
            f"Error: Cannot create or write to output directory {RNNOISE_OUTPUT_DIR}: {e}"
        )
        return ""  # Generate output filename
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
    print("Running FFmpeg command:")
    print(" ".join(shlex.quote(str(arg)) for arg in cmd))

    try:
        # Run FFmpeg at normal priority for better compatibility
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        print("FFmpeg stdout:", result.stdout)
        print("FFmpeg stderr:", result.stderr)

        # Verify output file was created and has content (atomic check to avoid race conditions)
        try:
            if os.path.getsize(output_path) == 0:
                print("Error: Output file was created but is empty")
                return ""
        except FileNotFoundError:
            print("Error: Output file was not created")
            return ""
        except PermissionError:
            print("Error: Cannot access output file (permission denied)")
            return ""  # Clean up old files if needed
        cleanup_old_files()

        return output_path

    except subprocess.CalledProcessError as e:
        print("RNNoise processing failed!")
        print("Return code:", e.returncode)
        print("Command:", " ".join(shlex.quote(str(arg)) for arg in e.cmd))
        print("FFmpeg stdout:", e.stdout)
        print("FFmpeg stderr:", e.stderr)

        # Provide diagnostic information and troubleshooting guidance
        stderr_lower = e.stderr.lower() if e.stderr else ""

        print("\n--- TROUBLESHOOTING GUIDANCE ---")

        if "not recognized" in stderr_lower or "command not found" in stderr_lower:
            print("❌ CAUSE: FFmpeg is not installed or not in PATH")
            print("🔧 SOLUTION:")
            print("   1. Download FFmpeg from https://ffmpeg.org/download.html")
            print("   2. Add FFmpeg to your system PATH")
            print("   3. Restart your terminal/application")
            print("   4. Test with: ffmpeg -version")

        elif "could not load model" in stderr_lower or "no such file" in stderr_lower:
            print("❌ CAUSE: RNNoise model file issue")
            print("🔧 SOLUTION:")
            print(f"   1. Verify model file exists: {model_path}")
            print("   2. Check file permissions")
            print("   3. Re-download the model if corrupted")

        elif "moov atom not found" in stderr_lower or "invalid data" in stderr_lower:
            print("❌ CAUSE: Audio file is corrupted or unsupported format")
            print("🔧 SOLUTION:")
            print("   1. Try a different audio file")
            print("   2. Supported formats: WAV, MP3, M4A, FLAC")
            print("   3. Convert file to WAV format first")

        elif "permission denied" in stderr_lower or "access denied" in stderr_lower:
            print("❌ CAUSE: File permission issue")
            print("🔧 SOLUTION:")
            print("   1. Check file is not in use by another application")
            print("   2. Verify write permissions to output directory")
            print("   3. Run with administrator privileges if needed")

        elif "no space left" in stderr_lower or "disk full" in stderr_lower:
            print("❌ CAUSE: Insufficient disk space")
            print("🔧 SOLUTION:")
            print("   1. Free up disk space")
            print("   2. Choose a different output directory")
            print("   3. Clean up old files in rnnoise_output/")

        else:
            print("❌ CAUSE: Unknown FFmpeg error")
            print("🔧 SOLUTION:")
            print("   1. Check the FFmpeg stderr output above for clues")
            print("   2. Try with a simpler audio file (short WAV)")
            print("   3. Verify FFmpeg installation: ffmpeg -version")
            print("   4. Check system resources (RAM, CPU)")

        print(
            "📚 For more help, check FFmpeg documentation: https://ffmpeg.org/documentation.html"
        )
        print("=" * 60)

        return ""

    except Exception as e:
        print("Unexpected error:", e)
        return ""
