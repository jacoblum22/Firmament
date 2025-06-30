import json

# Load the processed data
with open("processed/COGS 200 L1_processed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Looking for segment_positions in clusters:")
if "clusters" in data:
    for cluster in data["clusters"]:
        cluster_id = cluster.get("cluster_id")
        segment_positions = cluster.get("segment_positions", [])
        examples = cluster.get("examples", [])

        print(f'Cluster {cluster_id}: {cluster.get("heading", "Unknown")}')
        print(f"  - Examples: {len(examples)} chunks")
        print(f"  - Segment positions: {len(segment_positions)} chunks")
        print(
            f"  - Improvement: {len(segment_positions) - len(examples)} additional chunks"
        )
        print()
else:
    print("No clusters found in data")

print("\nData keys:", list(data.keys()))
print("Topics keys:", list(data["topics"].keys()) if "topics" in data else "No topics")
if "topics" in data:
    sample_topic = next(iter(data["topics"].values()))
    print("Sample topic keys:", list(sample_topic.keys()))
