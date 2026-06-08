from backend.app.utils.text import (
    count_words,
    detect_output_language,
    extract_minimum_word_count,
    normalize_whitespace,
    split_sentences,
)


# --- count_words ---

def test_count_words():
    assert count_words("One two three.") == 3


def test_count_words_empty_string():
    assert count_words("") == 0


def test_count_words_contraction_counts_as_one():
    assert count_words("don't") == 1


def test_count_words_hyphenated_counts_as_one():
    assert count_words("well-known") == 1


# --- split_sentences ---

def test_split_sentences():
    assert split_sentences("Hello world. How are you?") == ["Hello world.", "How are you?"]


def test_split_sentences_empty_returns_empty():
    assert split_sentences("") == []


def test_split_sentences_question_and_exclamation():
    result = split_sentences("Stop! Are you sure? Yes.")
    assert len(result) == 3


def test_split_sentences_no_terminal_punctuation():
    result = split_sentences("Hello world")
    assert result == ["Hello world"]


def test_split_sentences_single_sentence_with_period():
    result = split_sentences("Only one sentence.")
    assert result == ["Only one sentence."]


# --- normalize_whitespace ---

def test_normalize_whitespace_collapses_spaces():
    assert normalize_whitespace("too   many   spaces") == "too many spaces"


def test_normalize_whitespace_trims_edges():
    assert normalize_whitespace("  hello  ") == "hello"


def test_normalize_whitespace_handles_newlines():
    assert normalize_whitespace("line one\nline two") == "line one line two"


# --- detect_output_language ---

def test_detect_output_language_korean():
    assert detect_output_language("저는 학교에서 배운 내용을 바탕으로 이 글을 썼습니다.") == "Korean"


def test_detect_output_language_english():
    assert detect_output_language("I wrote this essay based on what I learned in class.") == "English"


def test_detect_output_language_english_with_small_korean_phrase():
    text = "I wrote this essay about the Korean word 안녕하세요 and how language affects identity."
    assert detect_output_language(text) == "English"


# --- extract_minimum_word_count ---

def test_extract_minimum_word_count_above_pattern():
    assert extract_minimum_word_count("Keep it above 500 words.") == 500


def test_extract_minimum_word_count_plus_pattern():
    assert extract_minimum_word_count("Write 300+ words.") == 300


def test_extract_minimum_word_count_at_least_pattern():
    assert extract_minimum_word_count("Use at least 200 words.") == 200


def test_extract_minimum_word_count_minimum_pattern():
    assert extract_minimum_word_count("minimum 150 words") == 150


def test_extract_minimum_word_count_words_minimum_pattern():
    assert extract_minimum_word_count("100 words minimum") == 100


def test_extract_minimum_word_count_no_match_returns_none():
    assert extract_minimum_word_count("just write naturally") is None


def test_extract_minimum_word_count_empty_returns_none():
    assert extract_minimum_word_count("") is None
