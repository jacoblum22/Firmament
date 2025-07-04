import json
import sys
import argparse
from pathlib import Path


def analyze_chunk_data(file_path):
    """Analyze chunk data from a processed JSON file"""

    # Convert to Path object and resolve to absolute path
    file_path = Path(file_path).resolve()

    # Load the processed data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        print("Please ensure the file exists and try again.")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        print("Please check the file format and try again.")
        return False
    except Exception as e:
        print(f"Unexpected error loading the file: {e}")
        return False

    print(f"Analyzing data from: {file_path}")
    print("Data structure analysis:")
    print(f'Total segments: {len(data["segments"])}')
    print(f'Total topics: {len(data["topics"])}')
    print()

    for topic_id, topic in data["topics"].items():
        segment_positions = topic.get("segment_positions", [])
        examples = topic.get("examples", [])

        print(f'Topic {topic_id}: {topic["heading"]}')
        print(f"  - Examples (current): {len(examples)} chunks")
        print(f"  - Segment positions: {len(segment_positions)} chunks")
        print(
            f"  - Improvement: {len(segment_positions) - len(examples)} additional chunks"
        )
        print()

    return True


def test_chunk_analysis():
    """Pytest-compatible test function for chunk analysis"""
    # Get the backend directory (parent of tests directory)
    backend_dir = Path(__file__).parents[2]
    default_file = backend_dir / "processed" / "COGS 200 L1_processed.json"

    # Skip test if file doesn't exist (don't fail the test suite)
    if not default_file.exists():
        print(f"⚠️  Skipping chunk analysis test - file not found: {default_file}")
        return

    # Run the analysis
    success = analyze_chunk_data(default_file)
    assert success, f"Failed to analyze chunk data from {default_file}"
    print("✅ Chunk analysis test completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze processed chunk data from a JSON file"
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to the processed JSON file",
        default="processed/COGS 200 L1_processed.json",
    )

    args = parser.parse_args()

    # If running from the backend directory, the relative path should work
    # Otherwise, try to construct the absolute path
    file_path = Path(args.file_path)

    # If it's a relative path and doesn't exist, try relative to script location
    if not file_path.is_absolute() and not file_path.exists():
        # Try relative to the backend directory (2 levels up from this script)
        backend_dir = Path(__file__).parents[2]
        alternative_path = backend_dir / file_path
        if alternative_path.exists():
            file_path = alternative_path

    success = analyze_chunk_data(file_path)
    sys.exit(0 if success else 1)
