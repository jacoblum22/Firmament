import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def get_openai_client():
    """Initialize and return the OpenAI client, handling missing API key gracefully."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set in the environment variables."
        )
    return OpenAI(api_key=api_key)


client = get_openai_client()


def expand_bullet_point(
    bullet_point: str, topic_chunks: list, topic_heading: str
) -> dict:
    """
    Expand a single bullet point by providing more detailed information based on the topic chunks.

    Args:
        bullet_point (str): The bullet point to expand
        topic_chunks (list): List of text chunks from the same topic
        topic_heading (str): The heading of the topic for context

    Returns:
        dict: A dictionary with the expanded content
    """
    try:
        # Build the prompt for GPT-4o
        prompt = (
            f"You are a helpful assistant expanding study note bullet points with additional detail.\n"
            f"The student is studying the topic: '{topic_heading}'\n\n"
            f"They want more information about this specific bullet point:\n"
            f"{bullet_point}\n\n"
            f"Below are the source text chunks from this topic that you can reference:\n\n"
        )

        # Add the topic chunks as context
        for i, chunk in enumerate(topic_chunks, 1):
            prompt += f"Chunk {i}:\n{chunk}\n\n"

        prompt += (
            f"Please provide a detailed expansion of the bullet point above. Your response should:\n"
            f"- Generate exactly 2-4 sub-bullet points that elaborate on the concept\n"
            f"- Each sub-bullet should start with a dash (-) and contain ONLY ONE specific idea, detail, or example\n"
            f"- Each sub-bullet must be concise (maximum 15-20 words) and focused on a single concept\n"
            f"- Include specific examples, details, or explanations from the source chunks when possible, but DO NOT reference specific chunk numbers (e.g., 'In chunk 2...')\n"
            f"- Maintain the same academic tone and style as the main bullet points\n"
            f"- Stay focused on the specific bullet point topic\n"
            f"- Each sub-bullet should provide actionable study information\n\n"
            f"Format your response as a simple list of bullet points, one per line, starting with '-'."
        )

        print(f"Expanding bullet point: {bullet_point[:50]}...")
        print(f"Using {len(topic_chunks)} chunks for context")

        # GPT-4o call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for faster/cheaper expansion
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,  # Reasonable limit for expansion
        )

        # Ensure response and content exist
        if not response.choices or not response.choices[0].message.content:
            print("Error: GPT-4o response is empty or malformed.")
            return {"error": "GPT-4o response is empty or malformed."}

        expanded_content = response.choices[0].message.content.strip()

        # Parse the bullet points from the response
        expanded_bullets = [
            point.strip()
            for point in expanded_content.split("\n")
            if point.strip() and point.strip().startswith("-")
        ]

        print(
            f"Successfully expanded bullet point with {len(expanded_bullets)} sub-bullets"
        )

        return {
            "original_bullet": bullet_point,
            "expanded_bullets": expanded_bullets,  # Changed from expanded_content to expanded_bullets
            "topic_heading": topic_heading,
            "chunks_used": len(topic_chunks),
        }

    except Exception as e:
        print(f"Error expanding bullet point: {e}")
        return {"error": f"Failed to expand bullet point: {str(e)}"}
