import json
import logging
import os

from fastapi import APIRouter, Depends

from utils.common.error_messages import ErrorMessages

from .health import get_llm_api_key

logger = logging.getLogger(__name__)

router = APIRouter(tags=["expansion"])


@router.post("/expand-cluster")
def expand_cluster(data: dict, llm_overrides: dict = Depends(get_llm_api_key)):
    """
    Expand a specific cluster by generating bullet points for it.

    Expects JSON body with 'filename' (str) and 'cluster_id' (str or int).
    Returns expanded cluster information or an error dict.
    """
    full_filename = data.get("filename")
    cluster_id = data.get("cluster_id")

    if (
        full_filename is None and data.get("processing_id") is None
    ) or cluster_id is None:
        return ErrorMessages.get_user_friendly_error(
            "invalid_request",
            "Missing filename/processing_id or cluster_id",
            {
                "operation": "cluster expansion",
                "required_fields": ["filename or processing_id", "cluster_id"],
            },
        )

    try:
        cluster_id = int(cluster_id)
    except (ValueError, TypeError):
        return ErrorMessages.get_user_friendly_error(
            "invalid_request",
            f"Invalid cluster_id format: {cluster_id}",
            {
                "operation": "cluster expansion",
                "expected_type": "integer",
                "received_value": str(cluster_id),
            },
        )

    processing_id = data.get("processing_id")
    base = processing_id or os.path.splitext(full_filename)[0]
    processed_filename = base + "_processed.json"

    from utils.nlp.expand_cluster import expand_cluster as expand_cluster_util

    result = expand_cluster_util(
        processed_filename,
        cluster_id,
        api_key=llm_overrides.get("api_key"),
        base_url_override=llm_overrides.get("base_url"),
        model_override=llm_overrides.get("model"),
    )
    return result


@router.post("/expand-bullet-point")
def expand_bullet_point_endpoint(
    data: dict, llm_overrides: dict = Depends(get_llm_api_key)
):
    """
    Expand a bullet point with additional detail and context.
    """
    bullet_point = data.get("bullet_point")
    chunks = data.get("chunks", [])
    topic_heading = data.get("topic_heading", "Unknown Topic")
    filename = data.get("filename")
    processing_id = data.get("processing_id")
    topic_id = data.get("topic_id")
    layer = data.get("layer", 1)
    other_bullets = data.get("other_bullets", [])

    logger.info(
        f"Expand bullet point: layer={layer}, chunks={len(chunks)}, "
        f"topic={topic_heading}, id={topic_id}"
    )

    if not bullet_point or not chunks:
        error_msg = "Missing required fields: 'bullet_point' or 'chunks'."
        logger.warning(f"Expand bullet point error: {error_msg}")
        return {"error": error_msg}

    try:
        from utils.nlp.expand_bullet_point import expand_bullet_point

        result = expand_bullet_point(
            bullet_point,
            chunks,
            topic_heading,
            layer,
            other_bullets,
            api_key=llm_overrides.get("api_key"),
            base_url_override=llm_overrides.get("base_url"),
            model_override=llm_overrides.get("model"),
        )
        logger.info("Expansion completed successfully")

        if (filename or processing_id) and topic_id and not result.get("error"):
            try:
                from utils.nlp.save_bullet_expansion import save_bullet_expansion

                base_name = processing_id or os.path.splitext(filename)[0]
                processed_file = os.path.join(
                    "processed", f"{base_name}_processed.json"
                )

                if os.path.exists(processed_file):
                    with open(processed_file, "r", encoding="utf-8") as f:
                        processed_data = json.load(f)

                    expansion_data = {
                        "expanded_bullets": result.get("expanded_bullets", []),
                        "topic_heading": topic_heading,
                        "chunks_used": result.get("chunks_used", 0),
                    }

                    parent_bullet = data.get("parent_bullet") if layer == 2 else None

                    success = save_bullet_expansion(
                        processed_data=processed_data,
                        topic_id=topic_id,
                        bullet_point=bullet_point,
                        expansion_data=expansion_data,
                        layer=layer,
                        parent_bullet=parent_bullet,
                    )

                    if success:
                        with open(processed_file, "w", encoding="utf-8") as f:
                            json.dump(processed_data, f, indent=2)
                        logger.info(
                            f"Saved expansion to cluster {topic_id} in {processed_file}"
                        )
                    else:
                        logger.warning(
                            "Failed to save expansion using utility function"
                        )
                else:
                    logger.warning(f"Processed file not found: {processed_file}")
            except Exception as save_error:
                logger.warning(f"Failed to save expansion: {save_error}")

        return result
    except Exception as e:
        error_msg = f"Failed to expand bullet point: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

