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
    bullet_point: str, topic_chunks: list, topic_heading: str, layer: int = 1
) -> dict:
    """
    Expand a single bullet point by providing more detailed information based on the topic chunks.

    Args:
        bullet_point (str): The bullet point to expand
        topic_chunks (list): List of text chunks from the same topic
        topic_heading (str): The heading of the topic for context
        layer (int): The expansion layer (1=first sub-layer, 2=second sub-layer, etc.)

    Returns:
        dict: A dictionary with the expanded content
    """
    try:
        # Limit expansion to maximum of 2 layers
        if layer > 2:
            return {
                "error": f"Maximum expansion depth of 2 layers reached. Cannot expand beyond layer 2.",
                "original_bullet": bullet_point,
                "layer": layer,
            }

        # Build layer-specific prompts
        if layer == 1:
            # First sub-layer: Key reasons, mechanisms, or breakdowns
            specific_instructions = (
                f"- Generate exactly 2-4 sub-bullet points that break down and unpack the concept\n"
                f"- Focus on key reasons, underlying mechanisms, or logical breakdowns that explain HOW or WHY\n"
                f"- Each sub-bullet should make the original concept simpler and easier to understand\n"
                f"- DO NOT simply restate what's in the original bullet - instead, break it down into component parts\n"
                f"- Each sub-bullet should answer questions like 'Why does this happen?', 'How does this work?', or 'What are the key components?'\n"
            )
        elif layer == 2:
            # Second sub-layer: Examples, implications, or clarifying details
            specific_instructions = (
                f"- Generate exactly 2-4 sub-bullet points that provide examples, implications, or clarifying details\n"
                f"- Focus on concrete examples, practical implications, or specific details that reinforce understanding\n"
                f"- Each sub-bullet should contextualize and reinforce the concept being expanded\n"
                f"- DO NOT restate the parent bullet - instead, provide supporting examples or clarifying context\n"
                f"- Each sub-bullet should answer questions like 'What are examples of this?', 'What does this mean in practice?', or 'What are the implications?'\n"
            )
        else:
            # Fallback for deeper layers (same as layer 2)
            specific_instructions = (
                f"- Generate exactly 2-4 sub-bullet points that provide concrete examples or specific details\n"
                f"- Focus on very specific, practical examples that illustrate the concept\n"
                f"- Each sub-bullet should provide tangible, real-world context\n"
                f"- DO NOT restate higher-level concepts - instead, get more specific and concrete\n"
                f"- Each sub-bullet should answer 'What does this look like in practice?' or 'What are specific instances of this?'\n"
            )

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
            + specific_instructions
            + f"- Each sub-bullet should start with a dash (-) and contain ONLY ONE specific idea, detail, or example\n"
            f"- Ensure each sub-bullet directly addresses the bullet point being expanded and does not veer into unrelated concepts\n"
            f"- Each sub-bullet must be concise (maximum 15-20 words) and focused on a single concept\n"
            f"- Include specific examples, details, or explanations from the source chunks when possible, but DO NOT reference specific chunk numbers (e.g., 'In chunk 2...')\n"
            f"- Maintain the same academic tone and style as the main bullet points\n"
            f"- Stay focused on the specific bullet point topic\n"
            f"- Each sub-bullet should provide actionable study information\n\n"
            f"Format your response as a simple list of bullet points, one per line, starting with '-'."
        )

        print(f"🚀 Expanding bullet point (Layer {layer}): {bullet_point[:50]}...")
        print(
            f"📦 Using {len(topic_chunks)} chunks for context (topic: {topic_heading})"
        )

        # Log chunk statistics for verification
        if topic_chunks:
            total_words = sum(len(chunk.split()) for chunk in topic_chunks)
            avg_words = total_words / len(topic_chunks)
            print(
                f"📊 Chunk statistics: {total_words} total words, avg {avg_words:.1f} words per chunk"
            )
            print(f"📄 First chunk preview: {topic_chunks[0][:100]}...")
            if len(topic_chunks) > 1:
                print(f"📄 Last chunk preview: {topic_chunks[-1][:100]}...")
        else:
            print("⚠️ Warning: No chunks provided for expansion!")

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
            f"✅ Successfully expanded bullet point (Layer {layer}) with {len(expanded_bullets)} sub-bullets using {len(topic_chunks)} chunks"
        )
        print(
            f"📝 Generated sub-bullets: {[bullet[:30] + '...' for bullet in expanded_bullets]}"
        )

        return {
            "original_bullet": bullet_point,
            "expanded_bullets": expanded_bullets,  # Changed from expanded_content to expanded_bullets
            "topic_heading": topic_heading,
            "chunks_used": len(topic_chunks),
            "layer": layer,
        }

    except Exception as e:
        print(f"Error expanding bullet point: {e}")
        return {"error": f"Failed to expand bullet point: {str(e)}"}
