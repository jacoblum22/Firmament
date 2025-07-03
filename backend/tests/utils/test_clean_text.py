import pytest
from backend.utils.clean_text import (
    remove_filler_words,
    remove_duplicate_phrases,
    restore_punctuation,
    clean_chunk_text,
)


def test_remove_filler_words_basic():
    text = "Um, so, I think, like, this is actually, well, basically, a test."
    cleaned = remove_filler_words(text)
    # Should remove most filler words but keep contextually meaningful ones
    assert "Um" not in cleaned
    assert "so" not in cleaned
    assert "well" not in cleaned
    assert "basically" not in cleaned
    assert "test" in cleaned


def test_remove_duplicate_phrases():
    text = "This is a test. This is a test. This is only a test."
    cleaned = remove_duplicate_phrases(text)
    # Should remove the repeated phrase
    assert cleaned.count("This is a test.") <= 1
    assert "This is only a test." in cleaned


def test_restore_punctuation():
    text = "this is a test this is only a test"
    punctuated = restore_punctuation(text)
    # Should add a period and capitalize
    assert punctuated[0].isupper()
    assert punctuated.strip().endswith(".")


def test_clean_chunk_text_basic():
    text = "Um, so, I think this is a test. This is a test. This is only a test."
    result = clean_chunk_text(text)
    cleaned = result["cleaned_text"]
    # Should remove filler words and duplicates, restore punctuation
    assert "Um" not in cleaned
    assert "so" not in cleaned
    assert cleaned.count("This is a test.") <= 1
    assert "This is only a test." in cleaned
    assert cleaned[0].isupper()
    assert cleaned.strip().endswith(".")


def test_clean_chunk_text_empty():
    result = clean_chunk_text("")
    assert result["cleaned_text"] == ""
    assert result["metadata"]["original_length"] == 0
    assert result["metadata"]["cleaned_length"] == 0


def test_filler_word_not_removed_when_important():
    # 'well' is important here
    text = "He means well but that isn't enough."
    cleaned = remove_filler_words(text)
    assert "well" in cleaned
    # 'well' at the start as a filler should be removed
    text2 = "Well, I think this is fine."
    cleaned2 = remove_filler_words(text2)
    assert "Well" not in cleaned2


def test_filler_word_in_word_not_removed():
    # 'Um' in 'Umpire' should not be removed
    text = "Umpire, go over there."
    cleaned = remove_filler_words(text)
    assert "Umpire" in cleaned
    # 'uh' in 'uh-oh' should not be removed
    text2 = "Uh-oh, that's not good."
    cleaned2 = remove_filler_words(text2)
    assert "Uh-oh" in cleaned2


def test_contextual_filler_removal():
    # 'well' surrounded by commas should be removed
    text = "This is, well, basically, a test."
    cleaned = remove_filler_words(text)
    assert "well" not in cleaned
    # 'well' not surrounded by commas should be kept
    text2 = "He did well in the exam."
    cleaned2 = remove_filler_words(text2)
    assert "well" in cleaned2


def test_like_contextual_preservation():
    # 'like' should be removed when used as filler (surrounded by commas)
    text1 = "This is, like, really good."
    cleaned1 = remove_filler_words(text1)
    assert "like" not in cleaned1

    # 'like' should be removed when at start with comma
    text2 = "Like, I don't know what to say."
    cleaned2 = remove_filler_words(text2)
    assert "like" not in cleaned2

    # 'like' should be kept when used meaningfully (comparison)
    text3 = "I like chocolate ice cream."
    cleaned3 = remove_filler_words(text3)
    assert "like" in cleaned3

    # 'like' should be kept when used meaningfully (similarity)
    text4 = "This tastes like vanilla."
    cleaned4 = remove_filler_words(text4)
    assert "like" in cleaned4


def test_actually_contextual_preservation():
    # 'actually' should be removed when used as filler
    text1 = "This is, actually, quite interesting."
    cleaned1 = remove_filler_words(text1)
    assert "actually" not in cleaned1

    # 'actually' should be kept when used meaningfully with 'is/was/has/have'
    text2 = "This is actually the correct answer."
    cleaned2 = remove_filler_words(text2)
    assert "actually" in cleaned2

    # 'actually' should be kept when used meaningfully
    text3 = "What actually happened yesterday?"
    cleaned3 = remove_filler_words(text3)
    assert "actually" in cleaned3


def test_basically_contextual_preservation():
    # 'basically' should be removed when used as filler
    text1 = "So, basically, this is how it works."
    cleaned1 = remove_filler_words(text1)
    assert "basically" not in cleaned1

    # 'basically' should be kept when used meaningfully
    text2 = "The plan is basically sound but needs refinement."
    cleaned2 = remove_filler_words(text2)
    assert "basically" in cleaned2


def test_literally_contextual_preservation():
    # 'literally' should be removed when used as filler
    text1 = "This is, literally, the best thing ever."
    cleaned1 = remove_filler_words(text1)
    assert "literally" not in cleaned1

    # 'literally' should be kept when used meaningfully
    text2 = "He literally ran five miles."
    cleaned2 = remove_filler_words(text2)
    assert "literally" in cleaned2


def test_honestly_contextual_preservation():
    # 'honestly' should be removed when used as filler
    text1 = "Honestly, I don't know what to say."
    cleaned1 = remove_filler_words(text1)
    assert "honestly" not in cleaned1

    # 'honestly' should be kept when used meaningfully
    text2 = "He spoke honestly about his mistakes."
    cleaned2 = remove_filler_words(text2)
    assert "honestly" in cleaned2


def test_thinking_phrases_contextual_preservation():
    # Thinking phrases should be removed at start of sentence
    text1 = "I think this is a good idea."
    cleaned1 = remove_filler_words(text1)
    assert "I think" not in cleaned1

    # Thinking phrases should be removed when preceded by comma
    text2 = "This is, I think, a good solution."
    cleaned2 = remove_filler_words(text2)
    assert "I think" not in cleaned2

    # 'think' should be kept when used meaningfully
    text3 = "Let me think about this problem."
    cleaned3 = remove_filler_words(text3)
    assert "think" in cleaned3

    # Test other thinking phrases
    text4 = "I guess we should go now."
    cleaned4 = remove_filler_words(text4)
    assert "I guess" not in cleaned4

    text5 = "I mean, that's not what I expected."
    cleaned5 = remove_filler_words(text5)
    assert "I mean" not in cleaned5

    text6 = "I feel like this could work."
    cleaned6 = remove_filler_words(text6)
    assert "I feel like" not in cleaned6


def test_sort_of_kind_of_contextual():
    # 'sort of' should be removed when preceded by modal verbs
    text1 = "I should sort of go there."
    cleaned1 = remove_filler_words(text1)
    assert "sort of" not in cleaned1

    # 'kind of' should be removed when followed by action verbs
    text2 = "We kind of have to leave."
    cleaned2 = remove_filler_words(text2)
    assert "kind of" not in cleaned2

    # 'sort of' should be kept when used meaningfully for classification
    text3 = "What sort of music do you like?"
    cleaned3 = remove_filler_words(text3)
    assert "sort" in cleaned3 and "of" in cleaned3

    # 'kind of' should be kept when used meaningfully for type
    text4 = "This kind of behavior is unacceptable."
    cleaned4 = remove_filler_words(text4)
    assert "kind" in cleaned4 and "of" in cleaned4


def test_so_contextual_preservation():
    # 'so' should be removed at start of sentence with comma
    text1 = "So, what do you think?"
    cleaned1 = remove_filler_words(text1)
    assert not cleaned1.startswith("So")

    # 'so' should be removed when surrounded by commas
    text2 = "This is, so, interesting to me."
    cleaned2 = remove_filler_words(text2)
    assert ", so," not in cleaned2

    # 'so' should be kept when used meaningfully (result/consequence)
    text3 = "He was tired, so he went to bed."
    cleaned3 = remove_filler_words(text3)
    assert "so" in cleaned3

    # 'so' should be kept when used meaningfully (degree)
    text4 = "This is so important to understand."
    cleaned4 = remove_filler_words(text4)
    assert "so" in cleaned4


def test_you_know_contextual_preservation():
    # 'you know' should be removed when used as filler
    text1 = "This is, you know, really difficult."
    cleaned1 = remove_filler_words(text1)
    assert "you know" not in cleaned1

    # 'you know' should be removed at start of sentence
    text2 = "You know, I think this is right."
    cleaned2 = remove_filler_words(text2)
    assert not cleaned2.startswith("You know")

    # 'you know' should be kept when used meaningfully
    text3 = "Do you know the answer to this question?"
    cleaned3 = remove_filler_words(text3)
    assert "you know" in cleaned3


def test_sentence_openers_contextual():
    # Sentence openers should be removed at start
    text1 = "Okay, let's begin the lesson."
    cleaned1 = remove_filler_words(text1)
    assert not cleaned1.startswith("Okay")

    text2 = "Alright, this is the plan."
    cleaned2 = remove_filler_words(text2)
    assert not cleaned2.startswith("Alright")

    # These words should be kept when used meaningfully
    text3 = "Is everything okay with you?"
    cleaned3 = remove_filler_words(text3)
    assert "okay" in cleaned3

    text4 = "Turn alright at the next corner."
    cleaned4 = remove_filler_words(text4)
    assert "alright" in cleaned4


def test_multiple_context_words_in_sentence():
    # Test complex sentence with multiple potential filler words
    text = "Well, I actually think that, like, this solution is basically, you know, really good."
    cleaned = remove_filler_words(text)

    # Filler uses should be removed
    assert not cleaned.startswith("Well")
    assert "like," not in cleaned
    assert "basically," not in cleaned
    assert "you know" not in cleaned

    # Meaningful words should be preserved
    assert "think" in cleaned
    assert "solution" in cleaned
    assert "really good" in cleaned


def test_edge_cases_with_punctuation():
    # Test that punctuation doesn't interfere with filler detection
    text1 = "This is well, actually, quite simple."
    cleaned1 = remove_filler_words(text1)
    assert "well" in cleaned1  # 'well' here is not surrounded by commas properly

    text2 = "This is, well, quite simple."
    cleaned2 = remove_filler_words(text2)
    assert "well" not in cleaned2  # 'well' here is properly surrounded by commas

    # Test with various punctuation marks
    text3 = "Like... I don't know what to say."
    cleaned3 = remove_filler_words(text3)
    # Should handle punctuation variations gracefully


def test_preserve_important_vs_filler_same_word():
    # Test that the same word is handled differently based on context

    # 'well' as filler vs meaningful
    filler_text = "Well, I suppose that's fine."
    meaningful_text = "The water well was deep."

    filler_cleaned = remove_filler_words(filler_text)
    meaningful_cleaned = remove_filler_words(meaningful_text)

    assert not filler_cleaned.startswith("Well")
    assert "well" in meaningful_cleaned

    # 'like' as filler vs meaningful
    filler_text2 = "This is, like, really good."
    meaningful_text2 = "I like this approach."

    filler_cleaned2 = remove_filler_words(filler_text2)
    meaningful_cleaned2 = remove_filler_words(meaningful_text2)

    assert "like" not in filler_cleaned2
    assert "like" in meaningful_cleaned2


def test_capitalization_preservation():
    # Test that capitalization is preserved correctly after filler removal
    text1 = "Well, this is important."
    cleaned1 = remove_filler_words(text1)
    assert cleaned1[0].isupper()  # Should start with capital letter

    text2 = "I like this, well, it works."
    cleaned2 = remove_filler_words(text2)
    assert "I " in cleaned2  # 'I' should remain capitalized when 'I like' is meaningful


def test_advanced_contextual_edge_cases():
    # Test words that could be both meaningful and filler in different contexts

    # 'actually' in different contexts
    text1 = "What actually happened was surprising."
    cleaned1 = remove_filler_words(text1)
    assert "actually" in cleaned1  # meaningful usage

    text2 = "This is, actually, quite surprising."
    cleaned2 = remove_filler_words(text2)
    assert "actually" not in cleaned2  # filler usage

    # 'literally' in different contexts
    text3 = "He literally jumped over the fence."
    cleaned3 = remove_filler_words(text3)
    assert "literally" in cleaned3  # meaningful usage

    text4 = "This is, literally, the best day ever."
    cleaned4 = remove_filler_words(text4)
    assert "literally" not in cleaned4  # filler usage


def test_compound_filler_removal():
    # Test sentences with multiple types of fillers
    text = "Um, well, I actually think that, you know, this is, like, basically, really good, honestly."
    cleaned = remove_filler_words(text)

    # All filler words should be removed
    assert "Um" not in cleaned
    assert "well" not in cleaned
    assert "you know" not in cleaned
    assert "like," not in cleaned  # with comma
    assert "basically," not in cleaned  # with comma
    assert "honestly." not in cleaned  # at end

    # Meaningful content should remain
    assert "think" in cleaned
    assert "really good" in cleaned


def test_filler_vs_content_boundary_cases():
    # Test cases where the same word appears as both filler and content

    text1 = "I like pizza and I like, you know, ice cream too."
    cleaned1 = remove_filler_words(text1)
    # First 'like' is meaningful, second 'like' context should be preserved, 'you know' removed
    assert cleaned1.count("like") >= 1  # At least one 'like' should remain
    assert "you know" not in cleaned1

    text2 = "He's basically a good person, but this plan is basically, well, flawed."
    cleaned2 = remove_filler_words(text2)
    # First 'basically' is meaningful, second 'basically,' is filler
    assert "basically a good person" in cleaned2
    assert "basically," not in cleaned2
    assert "well" not in cleaned2


def test_punctuation_variations():
    # Test how different punctuation affects filler detection

    text1 = "Well... I don't know what to say."
    cleaned1 = remove_filler_words(text1)
    assert not cleaned1.startswith("Well")

    text2 = "This is, well, interesting."  # comma before well
    cleaned2 = remove_filler_words(text2)
    assert "well" not in cleaned2

    text3 = "Actually! This works great."
    cleaned3 = remove_filler_words(text3)
    assert not cleaned3.startswith("Actually")  # Should be removed as sentence opener


def test_case_sensitivity_preservation():
    # Test that meaningful words preserve their case

    text1 = "Actually, John Actually lives there."
    cleaned1 = remove_filler_words(text1)
    # First 'Actually' should be removed, second 'Actually' (name) should be kept
    assert not cleaned1.startswith("Actually")
    assert "Actually lives" in cleaned1

    text2 = "I LITERALLY can't believe this literally, happened."
    cleaned2 = remove_filler_words(text2)
    # First 'LITERALLY' is meaningful, second 'literally,' is filler
    assert "LITERALLY" in cleaned2
    assert "literally," not in cleaned2


def test_multiple_sentence_processing():
    # Test that filler removal works correctly across multiple sentences

    text = "Well, this is good. Actually, I think this works. Basically, we're done."
    cleaned = remove_filler_words(text)

    sentences = cleaned.split(". ")
    # Each sentence should start with a capital letter
    for sentence in sentences:
        if sentence.strip():
            assert sentence[0].isupper()

    # Filler words at sentence starts should be removed
    assert not any(s.startswith("Well") for s in sentences)
    assert not any(s.startswith("Actually") for s in sentences)
    assert not any(s.startswith("Basically") for s in sentences)
