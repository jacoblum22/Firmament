import tiktoken
from typing import Optional
from dotenv import load_dotenv
from .openai_client import get_openai_client

load_dotenv()

client = get_openai_client()
encoding = tiktoken.encoding_for_model("gpt-4o-mini")


def expand_bullet_point(
    bullet_point: str,
    topic_chunks: list,
    topic_heading: str,
    layer: int = 1,
    other_bullets: Optional[list] = None,
) -> dict:
    """
    Expand a single bullet point by providing more detailed information based on the topic chunks.

    Args:
        bullet_point (str): The bullet point to expand
        topic_chunks (list): List of text chunks from the same topic
        topic_heading (str): The heading of the topic for context
        layer (int): The expansion layer (1=first sub-layer, 2=second sub-layer, etc.)
        other_bullets (list): List of other bullet points in the same topic to avoid duplication

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
                f"- Generate EXACTLY 1 to 3 sub-bullet points (no more than 3) that break down and unpack the concept\n"
                f"- Focus on key reasons, underlying mechanisms, or logical breakdowns that explain HOW or WHY\n"
                f"- Each sub-bullet should make the original concept simpler and easier to understand\n"
                f"- Only include sub-bullets if they add meaningful, distinct information (use fewer if the concept is simple)\n"
                f"- DO NOT simply restate what's in the original bullet - instead, break it down into component parts\n"
                f"- Each sub-bullet should answer questions like 'Why does this happen?', 'How does this work?', or 'What are the key components?'\n"
            )
        elif layer == 2:
            # Second sub-layer: Examples, implications, or clarifying details
            specific_instructions = (
                f"- Generate EXACTLY 1 to 3 sub-bullet points (no more than 3) that provide examples, implications, or clarifying details\n"
                f"- Focus on concrete examples, practical implications, or specific details that reinforce understanding\n"
                f"- Each sub-bullet should contextualize and reinforce the concept being expanded\n"
                f"- Only include sub-bullets if they provide distinct, valuable examples or details (use fewer if appropriate)\n"
                f"- DO NOT restate the parent bullet - instead, provide supporting examples or clarifying context\n"
                f"- Each sub-bullet should answer questions like 'What are examples of this?', 'What does this mean in practice?', or 'What are the implications?'\n"
            )
        else:
            # Fallback for deeper layers (same as layer 2)
            specific_instructions = (
                f"- Generate EXACTLY 1 to 3 sub-bullet points (no more than 3) that provide concrete examples or specific details\n"
                f"- Focus on very specific, practical examples that illustrate the concept\n"
                f"- Each sub-bullet should provide tangible, real-world context\n"
                f"- Only include sub-bullets if they offer distinct, valuable examples (use fewer if appropriate)\n"
                f"- DO NOT restate higher-level concepts - instead, get more specific and concrete\n"
                f"- Each sub-bullet should answer 'What does this look like in practice?' or 'What are specific instances of this?'\n"
            )

        # Build the prompt for GPT-4o
        prompt = (
            f"You are a helpful assistant expanding study note bullet points with additional detail.\n"
            f"The student is studying the topic: '{topic_heading}'\n\n"
            f"They want more information about this specific bullet point:\n"
            f"{bullet_point}\n\n"
        )

        # Add other bullets context if provided
        if other_bullets and len(other_bullets) > 0:
            prompt += f"Other bullet points in this topic (DO NOT repeat or restate these ideas):\n"
            for other_bullet in other_bullets:
                if (
                    other_bullet.strip()
                    and other_bullet.strip() != bullet_point.strip()
                ):
                    prompt += f"- {other_bullet}\n"
            prompt += f"\nIMPORTANT: Don't repeat or restate the same ideas as any of the other bullets above. Just expand upon the specific bullet you were given.\n\n"

        prompt += f"Below are the source text chunks from this topic that you can reference:\n\n"

        # Token limit management for GPT-4o-mini (128k context window)
        # Leave room for response (300 tokens) and safety margin
        MAX_PROMPT_TOKENS = 120000  # Conservative limit

        def estimate_tokens(text: str) -> int:
            """Precise token counting using tiktoken encoding for gpt-4o-mini"""
            return len(encoding.encode(text))

        # Calculate base prompt tokens
        base_prompt_tokens = estimate_tokens(prompt)

        # Add the instructions that will be appended later
        duplication_warning = ""
        if other_bullets and len(other_bullets) > 0:
            duplication_warning = f"- CRITICAL: Do not repeat, restate, or overlap with any of the other bullet points listed above\n"

        instructions = (
            f"Please provide a detailed expansion of the bullet point above. Your response should:\n"
            + duplication_warning
            + specific_instructions
            + f"- IMPORTANT: Provide EXACTLY 1 to 3 sub-bullets (no more than 3, no less than 1)\n"
            + f"- Each sub-bullet should start with a dash (-) and contain ONLY ONE specific idea, detail, or example\n"
            f"- Ensure each sub-bullet directly addresses the bullet point being expanded and does not veer into unrelated concepts\n"
            f"- Each sub-bullet must be concise (maximum 15-20 words) and focused on a single concept\n"
            f"- Include specific examples, details, or explanations from the source chunks when possible, but DO NOT reference specific chunk numbers (e.g., 'In chunk 2...')\n"
            f"- Maintain the same academic tone and style as the main bullet points\n"
            f"- Stay focused on the specific bullet point topic\n"
            f"- Each sub-bullet should provide actionable study information\n\n"
            f"Format your response as a simple list of bullet points, one per line, starting with '-'. "
            f"Remember: MAXIMUM 3 bullets total."
        )
        instructions_tokens = estimate_tokens(instructions)

        total_tokens = base_prompt_tokens + instructions_tokens
        chunks_added = 0
        chunks_omitted = 0

        # Add chunks while staying within token limit
        for i, chunk in enumerate(topic_chunks, 1):
            chunk_text = f"Chunk {i}:\n{chunk}\n\n"
            chunk_tokens = estimate_tokens(chunk_text)

            if total_tokens + chunk_tokens > MAX_PROMPT_TOKENS:
                chunks_omitted = len(topic_chunks) - chunks_added
                print(
                    f"[WARNING] Token limit reached. Added {chunks_added}/{len(topic_chunks)} chunks, omitted {chunks_omitted} chunks"
                )
                if chunks_omitted > 0:
                    prompt += f"\n[Note: {chunks_omitted} additional chunks were omitted due to token limit constraints]\n\n"
                break

            prompt += chunk_text
            total_tokens += chunk_tokens
            chunks_added += 1

        prompt += instructions

        print(
            f"[EXPAND] Expanding bullet point (Layer {layer}): {bullet_point[:50]}..."
        )
        if other_bullets and len(other_bullets) > 0:
            print(
                f"[CONTEXT] Using {len(other_bullets)} other bullets for anti-duplication context"
            )
        print(
            f"[CHUNKS] Using {chunks_added}/{len(topic_chunks)} chunks for context (topic: {topic_heading})"
        )
        if chunks_omitted > 0:
            print(
                f"[TOKEN] Token management: {chunks_omitted} chunks omitted to stay within {MAX_PROMPT_TOKENS:,} token limit"
            )
        print(f"[TOKENS] Estimated prompt tokens: {total_tokens:,}")

        # Log chunk statistics for verification
        if chunks_added > 0:
            # Only calculate stats for chunks that were actually added
            used_chunks = topic_chunks[:chunks_added]
            total_words = sum(len(chunk.split()) for chunk in used_chunks)
            avg_words = total_words / len(used_chunks)
            print(
                f"[CHUNKS] Chunk statistics: {total_words} total words, avg {avg_words:.1f} words per chunk"
            )
            print(f"[PREVIEW] First chunk preview: {used_chunks[0][:100]}...")
            if len(used_chunks) > 1:
                print(f"[PREVIEW] Last chunk preview: {used_chunks[-1][:100]}...")
        else:
            print(
                "[WARNING] Warning: No chunks could be added due to token constraints!"
            )

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

        # Log the raw response for debugging
        print(f"[DEBUG] Raw GPT response:\n{expanded_content}\n")

        # Parse the bullet points from the response
        expanded_bullets = [
            point.strip()
            for point in expanded_content.split("\n")
            if point.strip() and point.strip().startswith("-")
        ]

        print(
            f"[SUCCESS] Successfully expanded bullet point (Layer {layer}) with {len(expanded_bullets)} sub-bullets using {len(topic_chunks)} chunks"
        )
        print(
            f"[BULLETS] Generated sub-bullets: {[bullet[:30] + '...' for bullet in expanded_bullets]}"
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
