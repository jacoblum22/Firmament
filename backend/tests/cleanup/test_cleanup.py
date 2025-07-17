import os
import sys
import pytest
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from cleanup_files import BASE_DIR, directories, show_directory_status


def test_directory_paths():
    """Ensure all directory paths are correctly set relative to BASE_DIR."""
    for dir_path in directories:
        assert dir_path.startswith(
            BASE_DIR
        ), f"Directory {dir_path} is not relative to BASE_DIR"


def test_no_root_level_folders():
    """Ensure no duplicate folders are created at the root level."""
    root_dir = Path(BASE_DIR).parent
    root_folders = ["uploads", "output", "processed", "temp_chunks", "rnnoise_output"]

    for folder in root_folders:
        assert not (
            root_dir / folder
        ).exists(), f"Root-level folder {folder} should not exist"


def test_show_directory_status():
    """Ensure show_directory_status does not raise errors."""
    try:
        show_directory_status()
    except Exception as e:
        pytest.fail(f"show_directory_status raised an exception: {e}")


if __name__ == "__main__":
    pytest.main()
