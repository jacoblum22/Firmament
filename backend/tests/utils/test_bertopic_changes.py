import json
import pytest
from pathlib import Path

# Check for bertopic dependency
try:
    from utils.bertopic_processor import process_with_bertopic

    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False


@pytest.mark.skipif(not BERTOPIC_AVAILABLE, reason="bertopic not available")
def test_bertopic_changes():
    """Test bertopic processor with existing data"""
    # Get the backend directory (parent of tests directory)
    backend_dir = Path(__file__).parents[2]
    data_file = backend_dir / "processed" / "COGS 200 L1_processed.json"

    # Skip test if file doesn't exist
    if not data_file.exists():
        pytest.skip(f"Data file not found: {data_file}")

    # Load existing chunks
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data["segments"]
    print(f"Processing {len(chunks)} chunks...")

    # Process without saving to file to test the basic structure
    try:
        result = process_with_bertopic(chunks)
    except Exception as e:
        pytest.fail(f"Error during BERTopic processing: {e}")

    print(f"Result keys: {list(result.keys())}")
    print(f'Number of segments in result: {len(result.get("segments", []))}')

    # Check if topics have segment_positions
    if result["topics"]:
        sample_topic_id = next(iter(result["topics"].keys()))
        sample_topic = result["topics"][sample_topic_id]
        print(f"Sample topic keys: {list(sample_topic.keys())}")
        if "segment_positions" in sample_topic:
            print(
                f'Sample topic has {len(sample_topic["segment_positions"])} segment positions'
            )
            print(f'Sample topic has {len(sample_topic["examples"])} examples')
        else:
            print("No segment_positions found in sample topic")

    # Verify the result
    assert result is not None
    assert "topics" in result
    print("✅ BERTopic processing completed successfully!")


if __name__ == "__main__":
    if not BERTOPIC_AVAILABLE:
        print("❌ BERTopic not available, skipping test")
    else:
        test_bertopic_changes()
