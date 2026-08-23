from book2audio.utils import (
    is_numeric_token,
    normalize_artifact_key,
    repair_hyphenation,
)


def test_numeric_token():
    assert is_numeric_token("123")
    assert is_numeric_token("— 123 —")
    assert not is_numeric_token("123 apples")


def test_artifact_key():
    assert normalize_artifact_key("THE BOOK 123") == "the book #"


def test_hyphenation():
    assert repair_hyphenation("some-\nthing") == "something"
    assert repair_hyphenation("well-known\nword") == "well-knownword"
