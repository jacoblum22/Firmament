"""
Utility function for saving bullet point expansions to processed JSON files.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional


def save_bullet_expansion(
    processed_data: Dict[str, Any],
    topic_id: str,
    bullet_point: str,
    expansion_data: Dict[str, Any],
    layer: int = 1,
    parent_bullet: Optional[str] = None,
) -> bool:
    """
    Save bullet point expansion to the processed data structure.

    Args:
        processed_data: The loaded processed JSON data
        topic_id: ID of the topic/cluster
        bullet_point: The original bullet point text
        expansion_data: The expansion result data to save
        layer: Expansion layer (1 for top-level, 2 for nested)
        parent_bullet: Parent bullet text for layer 2 expansions

    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        # Find the cluster in the processed data
        clusters = processed_data.get("clusters", [])
        cluster = None
        for c in clusters:
            if str(c.get("cluster_id")) == str(topic_id):
                cluster = c
                break

        if not cluster:
            print(f"[WARNING] Cluster {topic_id} not found in processed data")
            return False

        # Initialize bullet_expansions if it doesn't exist
        if "bullet_expansions" not in cluster:
            cluster["bullet_expansions"] = {}

        # Generate a consistent bullet key
        bullet_key = _generate_bullet_key(bullet_point)
        print(f"[SAVE] Generated bullet key: '{bullet_key}'")

        # Prepare the expansion data with metadata
        full_expansion_data = {
            **expansion_data,
            "original_bullet": bullet_point,
            "layer": layer,
            "timestamp": str(datetime.now()),
        }

        if layer == 1:
            # Save as top-level expansion
            cluster["bullet_expansions"][bullet_key] = full_expansion_data
            print(f"[SAVE] Saved layer 1 expansion: '{bullet_key}'")
            return True

        elif layer == 2:
            # Save as nested expansion under parent
            if not parent_bullet:
                print(
                    f"[WARNING] No parent_bullet provided for layer 2 expansion, saving as top-level"
                )
                cluster["bullet_expansions"][bullet_key] = full_expansion_data
                return True

            # Clean parent bullet text
            parent_bullet_clean = _clean_parent_bullet_text(parent_bullet, topic_id)

            # Find the parent bullet's expansion
            parent_found = _save_nested_expansion(
                cluster, bullet_key, full_expansion_data, parent_bullet_clean
            )

            if not parent_found:
                print(
                    f"[WARNING] Parent bullet not found for layer 2 expansion. Parent: '{parent_bullet_clean}', saving as top-level fallback"
                )
                cluster["bullet_expansions"][bullet_key] = full_expansion_data

            return True

        else:
            print(f"[WARNING] Unsupported expansion layer: {layer}")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to save bullet expansion: {e}")
        return False


def _generate_bullet_key(bullet_point: str) -> str:
    """Generate a consistent key for the bullet point."""
    clean_bullet = re.sub(r"^[-*+]\s*", "", bullet_point).strip()
    return clean_bullet[:80]


def _clean_parent_bullet_text(parent_bullet: str, topic_id: str) -> str:
    """Clean parent bullet text by removing topic ID prefix if present."""
    if parent_bullet.startswith(f"{topic_id}_"):
        return parent_bullet[len(f"{topic_id}_") :]
    return parent_bullet


def _save_nested_expansion(
    cluster: Dict[str, Any],
    bullet_key: str,
    expansion_data: Dict[str, Any],
    parent_bullet_clean: str,
) -> bool:
    """
    Save nested expansion under the parent bullet.

    Returns:
        bool: True if parent was found and expansion saved, False otherwise
    """
    for existing_key, existing_data in cluster["bullet_expansions"].items():
        # Check if this is the parent bullet by key or original bullet text
        is_parent = existing_key == parent_bullet_clean or (
            existing_data.get("original_bullet")
            and existing_data["original_bullet"] == parent_bullet_clean
        )

        if is_parent:
            # Initialize sub_expansions if it doesn't exist
            if "sub_expansions" not in existing_data:
                existing_data["sub_expansions"] = {}

            # Save the layer 2 expansion under the parent
            existing_data["sub_expansions"][bullet_key] = expansion_data
            print(
                f"[SAVE] Saved layer 2 expansion '{bullet_key}' under parent '{existing_key}'"
            )
            return True

    return False
