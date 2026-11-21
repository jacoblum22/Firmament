import re
import nltk
from nltk.corpus import stopwords
from typing import List, Dict

# Ensure the 'stopwords' resource is downloaded
try:
    nltk.data.find("corpora/stopwords.zip")
except LookupError:
    nltk.download("stopwords")

# Make sure you've run: nltk.download('stopwords')
stopword_set = set(stopwords.words("english"))


def is_informative(
    text: str, min_words: int = 5, max_stopword_ratio: float = 0.75
) -> bool:
    """
    Check if a text chunk contains useful information.
    More lenient filtering that only removes clearly uninformative chunks.

    A chunk is considered "clearly uninformative" if:
        - It contains fewer than `min_words` (e.g., "Hi", "OK").
        - The ratio of stopwords to total words exceeds `max_stopword_ratio` (e.g., "the and of in").

    Args:
        text: Text chunk to evaluate
        min_words: Minimum number of words (default: 5)
        max_stopword_ratio: Maximum ratio of stopwords allowed (default: 0.75)

    Returns:
        bool: True if chunk is informative, False if clearly uninformative
    """
    # Tokenize words
    words = re.findall(r"\b\w+\b", text.lower())

    # Skip very short chunks
    if len(words) < min_words:
        return False

    # Count stopwords
    stopword_count = sum(1 for w in words if w in stopword_set)
    stopword_ratio = stopword_count / len(words)

    # Only filter out chunks that are almost entirely stopwords
    return stopword_ratio < max_stopword_ratio


def filter_chunks(
    chunks: List[Dict[str, str]], min_words: int = 5, max_stopword_ratio: float = 0.9
) -> List[Dict[str, str]]:
    """
    Filter out clearly uninformative chunks from a list of text chunks.

    Args:
        chunks: List of chunk dictionaries with 'position' and 'text' keys
        min_words: Minimum number of words (default: 5)
        max_stopword_ratio: Maximum ratio of stopwords allowed (default: 0.9)

    Returns:
        List[Dict[str, str]]: Filtered list of chunks
    """
    return [
        chunk
        for chunk in chunks
        if is_informative(chunk["text"], min_words, max_stopword_ratio)
    ]
