import json
import logging
import os
from dotenv import load_dotenv
from ..common.openai_client import (
    call_openai_with_retries,
    get_openai_client,
    get_default_model,
)

load_dotenv()

logger = logging.getLogger(__name__)


def expand_cluster(
    filename: str,
    cluster_id: str,
    api_key: str | None = None,
    base_url_override: str | None = None,
    model_override: str | None = None,
) -> dict:
    """
    Expand a cluster by generating a bullet point list of important points.

    Args:
        filename (str): The name of the file in the processed folder.
        cluster_id (str): The ID of the cluster to expand.

    Returns:
        dict: A dictionary with the following structure:
            {
                "message": str,  # Status message
                "cluster": dict  # Updated cluster metadata, including "bullet_points"
            }
    """
    processed_file = os.path.join("processed", filename)

    logger.info(f"Expanding cluster: filename={filename}, cluster_id={cluster_id}")

    if not os.path.exists(processed_file):
        logger.error(f"File {filename} not found in processed folder.")
        return {"error": f"File {filename} not found in processed folder."}

    with open(processed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    clusters = data.get("clusters", [])
    cluster = None
    for c in clusters:
        if str(c.get("cluster_id")) == str(cluster_id):
            cluster = c
            break

    if not cluster:
        logger.error(f"Cluster ID {cluster_id} not found in file {filename}.")
        return {"error": f"Cluster ID {cluster_id} not found in file {filename}."}

    # Check and log the presence of the segment_positions field
    if "segment_positions" not in cluster:
        logger.warning(f"'segment_positions' field is missing in cluster {cluster_id}.")
    else:
        logger.debug(
            f"'segment_positions' field found in cluster {cluster_id}: {cluster['segment_positions']}"
        )

    # Retrieve segment texts based on segment_positions
    segment_positions = cluster.get("segment_positions", [])
    segments = data.get("segments", [])

    logger.debug(f"Segment positions for cluster {cluster_id}: {segment_positions}")
    logger.debug(f"Total segments available: {len(segments)}")

    # Extract the text of the segments at the specified positions
    chunks = []
    for pos in segment_positions:
        matching_segment = next(
            (segment for segment in segments if segment.get("position") == pos), None
        )
        if matching_segment:
            chunks.append(matching_segment["text"])
        else:
            logger.warning(f"No matching segment found for position: {pos}")

    if not chunks:
        logger.error(f"No valid segments found for Cluster ID {cluster_id}.")
        return {"error": f"No valid segments found for Cluster ID {cluster_id}."}

    # Build role-separated prompts: strict style rules in system message, raw chunk text in user message.
    system_prompt = (
        "You are an expert study notes generator. Your job is to create clear, self-contained bullet points from lecture content.\n\n"
        "Below is a cluster of text chunks from a lecture. Generate 5-15 concise bullet points summarizing the most important ideas.\n\n"
        "FORMAT (strictly follow this for every bullet):\n"
        "- Start with a bolded question: **What is X?** or **How does X work?** or **Why is X important?**\n"
        "- Follow immediately with a clear, complete answer on the same line\n"
        "- Example: **What is the kernel trick?** It allows efficient computation in high-dimensional feature spaces by using inner products instead of explicit feature mappings.\n\n"
        "QUALITY RULES:\n"
        "- Every bullet MUST follow the **Question?** Answer format — no exceptions\n"
        "- Answers must be SELF-CONTAINED — a reader should understand the point without seeing the original lecture slides, equations, or diagrams\n"
        '- If the source text references a visual element (formula, graph, table, expression), describe what it represents in words rather than saying "the expression" or "as shown"\n'
        '- Replace vague references like "this method", "the above", "as we saw" with specific names and descriptions\n'
        "- Each bullet should cover ONE distinct idea — no compound bullets\n"
        "- Use clear, specific academic language — avoid filler words\n"
        "- Focus on concepts, definitions, mechanisms, and relationships — not lecture logistics\n"
        "- Aim for 15-30 words per answer — concise but complete\n"
    )
    user_content = "\n".join(chunks)

    logger.debug(
        f"Generated prompts: system={len(system_prompt)} chars, user={len(user_content)} chars"
    )

    # GPT call
    client = get_openai_client(api_key, base_url_override=base_url_override)
    response = call_openai_with_retries(
        client.chat.completions.create,
        model=get_default_model("gpt-4o", model_override=model_override),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=500,  # Adjust as needed for bullet points
    )

    # Ensure response and content exist
    if not response.choices or not response.choices[0].message.content:
        logger.error("GPT-4 response is empty or malformed.")
        return {"error": "GPT-4 response is empty or malformed."}

    raw_bullet_points = response.choices[0].message.content.strip()

    # Parse the bullet points from the response
    bullet_points = [
        point.strip() for point in raw_bullet_points.split("\n") if point.strip()
    ]

    logger.info(
        f"Generated {len(bullet_points)} bullet points for cluster {cluster_id}"
    )

    # Update cluster metadata
    cluster["bullet_points"] = bullet_points

    # Save updated data back to the file
    with open(processed_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Cluster {cluster_id} expanded successfully")

    return {"message": "Cluster expanded successfully.", "cluster": cluster}
