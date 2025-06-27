import re
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
from difflib import SequenceMatcher
import string
from concurrent.futures import ThreadPoolExecutor

# Download required NLTK data
nltk.download("punkt", quiet=True)

# Common filler words and phrases that should be removed
FILLER_WORDS = {"um", "uh", "er", "ah", "anyway", "anyways", "well", "so yeah"}

# Words that should be preserved when used in certain contexts
CONTEXT_WORDS = {
    "like",
    "actually",
    "basically",
    "literally",
    "honestly",
    "i guess",
    "i think",
    "i mean",
    "i feel like",
}

# Sentence openers to remove
SENTENCE_OPENERS = {"so", "okay", "alright", "well", "all right", "actually"}

# Precompute sorted openers by length (longest first)
SORTED_OPENERS = sorted(SENTENCE_OPENERS.union(FILLER_WORDS), key=len, reverse=True)

# Redundant pairs to remove
REDUNDANT_PAIRS = {"yeah so", "yeah, so", "so, yeah", "so yeah"}

# Prefixes that indicate "sort of" or "kind of" should be removed
SORT_OF_PREFIXES = {
    "should",
    "could",
    "would",
    "might",
    "can",
    "will",
    "i",
    "we",
    "you",
    "they",
    "to",
}

# Suffixes that indicate "sort of" or "kind of" should be removed
SORT_OF_SUFFIXES = {
    "be",
    "do",
    "go",
    "have",
    "get",
    "think",
    "thought",
    "see",
    "saw",
    "feel",
    "felt",
    "try",
    "trying",
}


def is_filler_word(word: str, context: str) -> bool:
    """
    Determines whether a given word should be considered a filler word in the provided context.
    This function applies special rules for certain words and phrases, such as "like", "actually", "basically", "literally", and "honestly",
    to distinguish between their use as fillers and their meaningful usage within a sentence. It also ensures that important pronouns like "I"
    and "I'm" are never removed. The function relies on the global sets CONTEXT_WORDS and FILLER_WORDS to identify context-sensitive and
    generic filler words, respectively.

    Args:
        word (str): The word to check for filler status.
        context (str): The full context (sentence or phrase) in which the word appears.

    Returns:
        bool: True if the word is considered a filler in the given context and should be removed, False otherwise.

    Examples:
        >>> is_filler_word("like", "I feel like this is important.")
        False
        >>> is_filler_word("like", "Like, this is important.")
        True
        >>> is_filler_word("um", "Um, I don't know.")
        True
        >>> is_filler_word("I", "I think this is correct.")
        False
    """

    word = word.lower()
    context = context.lower()

    # Never remove 'I' or 'I'm'
    if word in ["i", "i'm"]:
        return False

    # Check if it's a context word that should be preserved
    if word in CONTEXT_WORDS:
        # Special handling for 'like'
        if word == "like":
            # Remove if surrounded by commas
            if re.search(r",\s*" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if at start of sentence followed by comma
            if re.match(r"^" + re.escape(word) + r"\s*,", context):
                return True
            return False

        # Special handling for "I think", "I guess", "I mean", "I feel like"
        if word in ["i think", "i guess", "i mean", "i feel like"]:
            # Remove if preceded by comma
            if re.search(r",\s*" + re.escape(word), context):
                return True
            # Remove if at start of sentence
            if re.match(r"^" + re.escape(word), context):
                return True
            return False

        # Special handling for individual words that can be meaningful
        if word == "actually":
            # Remove if surrounded by commas (filler usage)
            if re.search(r",\s*" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if at start of sentence followed by comma
            if re.match(r"^" + re.escape(word) + r"\s*,", context):
                return True
            return False

        if word == "basically":
            # Remove if surrounded by commas (filler usage)
            if re.search(r",\s*" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if at start of sentence followed by comma
            if re.match(r"^" + re.escape(word) + r"\s*,", context):
                return True
            return False

        if word == "literally":
            # Remove if surrounded by commas (filler usage)
            if re.search(r",\s*" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if at start of sentence followed by comma
            if re.match(r"^" + re.escape(word) + r"\s*,", context):
                return True
            return False

        if word == "honestly":
            # Remove if at start of sentence followed by comma
            if re.match(r"^" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if surrounded by commas (filler usage)
            if re.search(r",\s*" + re.escape(word) + r"\s*,", context):
                return True
            # Remove if at end of sentence with punctuation (appears to be filler)
            if re.search(re.escape(word) + r"[.!?]?\s*$", context):
                return True
            return False

        # For other context words, default to keeping them
        return False

    # Always remove filler words
    return word in FILLER_WORDS


def remove_sentence_openers(sentence: str) -> str:
    """
    Removes common sentence openers and filler words from the beginning of a sentence.

    This function checks if the input sentence starts with any word from the combined set of
    SENTENCE_OPENERS and FILLER_WORDS, followed by punctuation or whitespace. If such an opener
    is found, it is removed from the start of the sentence. The function uses a `break` statement
    to exit the loop after removing one opener, ensuring only one opener is removed per call.
    After removal, the function ensures the first character of the resulting sentence is capitalized
    if necessary, and leading/trailing whitespace is stripped.

    Args:
        sentence (str): The input sentence from which to remove the opener.

    Returns:
        str: The sentence with the opener removed from the start, if present.
    """
    # Use precomputed sorted openers
    for opener in SORTED_OPENERS:
        # Only match as a standalone word at the start, not as a prefix (e.g., 'Umpire')
        pattern = rf"^({re.escape(opener)})[,. !?]+"
        if re.match(pattern, sentence, flags=re.IGNORECASE):
            # Remove the matched opener from the start of the sentence
            sentence = re.sub(pattern, "", sentence, flags=re.IGNORECASE)
            # Capitalize first letter if we removed the opener
            if sentence and len(sentence) > 0 and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]
            break  # Only remove one opener at the start
    return sentence.strip()


def remove_redundant_pairs(sentence: str) -> str:
    """
    Removes redundant word pairs from a sentence.

    This function iterates through a predefined list of redundant pairs (REDUNDANT_PAIRS)
    and removes any occurrences of these pairs from the input sentence, ignoring case.
    After removal, it also fixes punctuation and capitalization if the redundant pair
    was at the start of the sentence.

    Args:
        sentence (str): The input sentence from which redundant pairs should be removed.

    Returns:
        str: The cleaned sentence with redundant pairs removed and formatting corrected.
    """
    for pair in REDUNDANT_PAIRS:
        sentence = re.sub(
            r"\b" + re.escape(pair) + r"\b", "", sentence, flags=re.IGNORECASE
        )
        # Fix punctuation and capitalization if we removed from the start
        if re.match(f"^{pair}[, ]", sentence.lower()):
            sentence = sentence[len(pair) :].strip()
            if sentence.startswith(","):
                sentence = sentence[1:].strip()
            if sentence and not sentence[0].isupper():
                sentence = sentence[0].upper() + sentence[1:]
    return sentence.strip()


def should_remove_sort_of(context: str) -> bool:
    """
    Determines whether a given context string should be removed based on the presence of specific prefixes or suffixes.
    The function checks if the first word of the context is in the set `SORT_OF_PREFIXES` or if the last word is in the set `SORT_OF_SUFFIXES`.
    If either condition is met and the context contains at least three words, the function returns True.
    Args:
        context (str): The input string to evaluate.
    Returns:
        bool: True if the context should be removed based on the prefix or suffix, False otherwise.
    """
    words = context.lower().split()
    if len(words) < 3:
        return False

    # Check if preceded by a prefix
    if words[0] in SORT_OF_PREFIXES:
        return True

    # Check if followed by a suffix
    if words[-1] in SORT_OF_SUFFIXES:
        return True

    return False


def remove_thinking_phrases(sentence: str) -> str:
    """
    Removes common "thinking phrases" (e.g., "I think", "I guess", "I mean", "I feel like") from the given sentence.
    The function targets these phrases when they appear at the start of the sentence, surrounded by commas, or after a comma and before punctuation or the end of the sentence. After removal, it ensures proper capitalization and cleans up extra spaces and commas.
    Args:
        sentence (str): The input sentence from which to remove thinking phrases.
    Returns:
        str: The cleaned sentence with thinking phrases removed and formatting corrected.
    """
    thinking_phrases = ["i think", "i guess", "i mean", "i feel like"]

    for phrase in thinking_phrases:
        # Remove at start of sentence (case insensitive)
        pattern = rf"^{re.escape(phrase)}[,\s]+"
        sentence = re.sub(pattern, "", sentence, flags=re.IGNORECASE)

        # Remove when surrounded by commas
        pattern = rf",\s*{re.escape(phrase)}\s*,"
        sentence = re.sub(pattern, ",", sentence, flags=re.IGNORECASE)

        # Remove when preceded by comma and at end or followed by punctuation
        pattern = rf",\s*{re.escape(phrase)}(?=\s*[.!?]|$)"
        sentence = re.sub(pattern, "", sentence, flags=re.IGNORECASE)

    # Fix capitalization if we removed from start
    if sentence and not sentence[0].isupper():
        sentence = sentence[0].upper() + sentence[1:]
    # Clean up extra spaces and commas
    sentence = re.sub(r"\s+", " ", sentence)
    sentence = re.sub(r",\s*,", ",", sentence)

    return sentence.strip()


def remove_you_know(sentence: str) -> str:
    """
    Removes occurrences of the phrase "you know" from a sentence, specifically when it is surrounded by punctuation or appears at the start of the sentence.

    Args:
        sentence (str): The input sentence from which to remove "you know".

    Returns:
        str: The sentence with "you know" removed where appropriate.
    """
    # Remove when surrounded by punctuation
    sentence = re.sub(r"[.,]\s*you know\s*[.,]", ",", sentence, flags=re.IGNORECASE)
    # Remove when at the start of a sentence
    sentence = re.sub(r"^you know\s*[.,]", "", sentence, flags=re.IGNORECASE)
    return sentence.strip()


def remove_internal_repetition(sentence: str) -> str:
    """
    Removes internal repetition of long phrases within a sentence.
    If a phrase (sequence of words) longer than half the sentence is repeated later in the sentence,
    the function removes the second occurrence of that phrase. Sentences shorter than 6 words are not processed.
    Args:
        sentence (str): The input sentence to process.
    Returns:
        str: The sentence with internal repetition removed, if any; otherwise, the original sentence.
    """
    words = sentence.split()
    if len(words) < 6:  # Don't process very short sentences
        return sentence

    # Look for repeated phrases
    for i in range(len(words) - 2):
        for j in range(i + 3, len(words)):
            phrase = " ".join(words[i:j])
            # Check if this phrase appears again later in the sentence
            if phrase in " ".join(words[j:]):
                # If the repeated phrase is more than half the sentence, remove the second occurrence
                if len(phrase.split()) > len(words) / 2:
                    return sentence.replace(phrase, "", 1)
    return sentence


def remove_so_phrases(sentence: str) -> str:
    """
    Removes occurrences of the word 'so' at the beginning of a sentence (when followed by a comma)
    and when framed by commas within the sentence. Also cleans up punctuation and spacing issues
    that may result from the removal.
    Args:
        sentence (str): The input sentence to process.
    Returns:
        str: The cleaned sentence with specified 'so' phrases removed and punctuation/spacing corrected.
    """
    # Remove 'so' at start of sentence followed by comma
    sentence = re.sub(r"^[Ss]o,\s*", "", sentence)

    # Remove 'so' framed by commas
    sentence = re.sub(r",\s*[Ss]o,\s*", ", ", sentence)

    # Fix capitalization if we removed from start
    if sentence and not sentence[0].isupper():
        sentence = sentence[0].upper() + sentence[1:]

    # Fix double commas
    sentence = re.sub(r",\s*,", ",", sentence)

    # Fix spacing around punctuation
    sentence = re.sub(r"\s+([.,!?])", r"\1", sentence)
    sentence = re.sub(r"([.,!?])([^\s])", r"\1 \2", sentence)

    return sentence.strip()


def remove_filler_words(text: str) -> str:
    """
    Removes common filler words and phrases from the input text while preserving sentence context and structure.
    This function processes the input text by splitting it into sentences, then applies a series of cleaning steps to each sentence:
    - Removes sentence openers and redundant word pairs.
    - Removes filler phrases such as "so", "you know", and thinking phrases.
    - Handles special cases for words like "well", "basically", "actually", "literally", and "honestly", removing them when used as fillers.
    - Removes phrases like "sort of" and "kind of" when used as fillers.
    - Cleans up internal repetition and ensures proper capitalization.
    Args:
        text (str): The input text to be cleaned.
    Returns:
        str: The cleaned text with filler words and phrases removed.
    """

    # Split into sentences to preserve context
    sentences = sent_tokenize(text)

    def clean_sentence(sentence: str) -> str:
        # Skip empty sentences
        if not sentence.strip():
            return ""

        # Remove sentence openers
        sentence = remove_sentence_openers(sentence)

        # Remove redundant pairs
        sentence = remove_redundant_pairs(sentence)

        # Remove 'so' in various contexts
        sentence = remove_so_phrases(sentence)

        # Remove 'you know' in appropriate contexts
        sentence = remove_you_know(sentence)

        # Remove thinking phrases
        sentence = remove_thinking_phrases(sentence)

        # Get words while preserving spacing
        words = sentence.split()
        cleaned_words = []

        for i, word in enumerate(words):
            # Strip punctuation for filler check
            word_stripped = word.strip(string.punctuation)
            prev_word = words[i - 1] if i > 0 else ""
            next_word = words[i + 1] if i < len(words) - 1 else ""
            context = f"{prev_word} {word} {next_word}"

            # Special handling for 'well': only remove if surrounded by commas or at sentence start and followed by comma
            if word_stripped.lower() == "well":
                # Remove if at start and followed by comma (word ends with comma)
                if i == 0 and word.endswith(","):
                    continue  # treat as filler
                # Remove if previous word ends with comma and current word ends with comma (surrounded by commas)
                if prev_word.endswith(",") and word.endswith(","):
                    continue  # treat as filler
                # Remove if word itself is ',well,' (though this case is unlikely with space splitting)
                if word.startswith(",") and word.endswith(","):
                    continue  # treat as filler
                # Otherwise, keep 'well'
                cleaned_words.append(word)

            # Special handling for context words that can be fillers
            elif word_stripped.lower() in [
                "basically",
                "actually",
                "literally",
                "honestly",
            ]:
                # Remove if preceded by comma and word ends with comma (surrounded by commas)
                if prev_word.endswith(",") and word.endswith(","):
                    continue  # treat as filler
                # Remove if at start and word ends with comma
                elif i == 0 and word.endswith(","):
                    continue  # treat as filler
                # Remove if word ends with comma and appears to be used as filler (not meaningful)
                elif word.endswith(","):
                    # This catches cases like "is basically," where it's used as filler
                    continue  # treat as filler
                # Remove if word ends with punctuation at end of sentence and appears to be filler
                elif word.endswith((".", "!", "?")) and i == len(words) - 1:
                    # Check if this is likely filler usage (e.g., "good, honestly.")
                    if prev_word.endswith(","):
                        continue  # treat as filler
                # Otherwise, check normal filler word logic
                elif not is_filler_word(word_stripped, context):
                    cleaned_words.append(word)

            # Handle 'sort of' and 'kind of'
            elif (
                word_stripped.lower() in ["sort", "kind"]
                and i < len(words) - 1
                and words[i + 1].lower() == "of"
            ):
                if should_remove_sort_of(context):
                    continue
                cleaned_words.append(word)
            elif (
                word_stripped.lower() == "of"
                and i > 0
                and words[i - 1].lower() in ["sort", "kind"]
            ):
                if should_remove_sort_of(context):
                    continue
                cleaned_words.append(word)
            elif not is_filler_word(word_stripped, context):
                cleaned_words.append(word)

        # Join words and clean up spacing
        cleaned_sentence = " ".join(cleaned_words)
        cleaned_sentence = re.sub(r"\s+", " ", cleaned_sentence).strip()

        # Remove internal repetition
        cleaned_sentence = remove_internal_repetition(cleaned_sentence)

        # Ensure first letter is capitalized
        if cleaned_sentence and not cleaned_sentence[0].isupper():
            cleaned_sentence = cleaned_sentence[0].upper() + cleaned_sentence[1:]

        return cleaned_sentence.strip()

    # Decide whether to use threading based on the number of sentences
    if len(sentences) > 10:  # Threshold for threading
        with ThreadPoolExecutor() as executor:
            try:
                cleaned_sentences = list(executor.map(clean_sentence, sentences))
            except Exception as e:
                print(f"Error during sentence processing: {e}")
                cleaned_sentences = []
    else:
        cleaned_sentences = [clean_sentence(sentence) for sentence in sentences]

    # Use filter(None, cleaned_sentences) to remove empty strings from the list of cleaned sentences
    return " ".join(filter(None, cleaned_sentences))


def remove_duplicate_phrases(text: str) -> str:
    """
    Removes duplicate sentences from the input text, preserving the order of their first occurrence.

    Args:
        text (str): The input text containing one or more sentences.

    Returns:
        str: The text with duplicate sentences removed, joined into a single string.

    Note:
        Sentence comparison is case-insensitive and ignores leading/trailing whitespace.
        Requires `sent_tokenize` to be available in the scope.
    """
    sentences = sent_tokenize(text)
    cleaned_sentences = []
    seen = set()
    for sentence in sentences:
        norm = sentence.strip().lower()
        if norm and norm not in seen:
            cleaned_sentences.append(sentence)
            seen.add(norm)
    return " ".join(cleaned_sentences)


def restore_punctuation(text: str) -> str:
    """
    Restores basic punctuation and capitalization to a given text string.
    This function performs the following operations:
    - Adds a period at the end of the text if it is missing.
    - Removes unnecessary spaces before punctuation marks (.,!?) and ensures there is a single space after them.
    - Collapses multiple consecutive punctuation marks into a single one.
    - Capitalizes the first letter of each sentence.
    - Ensures the pronoun 'I' is capitalized.
    Args:
        text (str): The input text string to be processed.
    Returns:
        str: The text with restored punctuation and capitalization.
    """
    # Add period at the end if missing
    if text and len(text) > 0 and not text[-1] in ".!?":
        text += "."

    # Fix spacing around punctuation
    text = re.sub(r"\s+([.,!?])", r"\1", text)

    # Ensure space after punctuation
    text = re.sub(r"([.,!?])([^\s])", r"\1 \2", text)

    # Fix multiple punctuation
    sentences = sent_tokenize(text)
    sentences = [re.sub(r"([.,!?])\1+", r"\1", sentence) for sentence in sentences]
    text = " ".join(sentences)

    # Tokenize the text into sentences and capitalize the first letter of each sentence
    sentences = sent_tokenize(text)
    sentences = [s[0].upper() + s[1:] for s in sentences if s]

    # Preserve 'I' capitalization
    sentences = [re.sub(r"\b[i]\b", "I", s) for s in sentences]

    return " ".join(sentences)


def clean_chunk_text(text: str) -> dict:
    """
    Clean and process text chunks with comprehensive error correction and formatting.

    Args:
        text: Raw text to clean

    Returns:
        dict: A dictionary containing:
            - "cleaned_text" (str): The processed and cleaned text.
            - "metadata" (dict): A dictionary with the following keys:
                - "original_length" (int): The length of the original text.
                - "cleaned_length" (int): The length of the cleaned text.
    """
    # Store the original text for metadata calculation
    original_text = text

    # Initial cleaning
    text = text.strip()
    from concurrent.futures import ThreadPoolExecutor

    # Process sentences with remove_filler_words only once
    sentences = sent_tokenize(text)
    with ThreadPoolExecutor() as executor:
        cleaned_sentences = list(executor.map(remove_filler_words, sentences))
    text = " ".join(cleaned_sentences)

    # Remove duplicates
    text = remove_duplicate_phrases(text)

    # Restore punctuation
    text = restore_punctuation(text)

    return {
        "cleaned_text": text,
        "metadata": {
            "original_length": len(original_text),
            "cleaned_length": len(text),
        },
    }
