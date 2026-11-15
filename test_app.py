"""Unit tests for the HKU Waste Recycling Assistant (run with: pytest)."""
import pytest
from app import retrieve_answer, process_query, is_unsafe, is_ambiguous

MOCK = [
    {"name": "Paper Cup", "aliases": ["coffee cup"], "category": "Paper",
     "preparation": "Remove the plastic lid.", "facility": "Main Library",
     "source": "https://facilities.hku.hk/", "access_date": "2026-11-16"},
    {"name": "Glass Bottle", "aliases": ["wine bottle"], "category": "Glass",
     "preparation": "Rinse and remove cap.", "facility": "Main Building",
     "source": "https://facilities.hku.hk/", "access_date": "2026-11-16"},
]


@pytest.fixture
def corpus():
    return MOCK


def test_normal_retrieval(corpus):
    item, score = retrieve_answer("how do I recycle a coffee cup", corpus)
    assert item is not None and item["category"] == "Paper"
    assert score >= 3


def test_answer_format_includes_fields(corpus):
    _, code, resp = process_query("recycle a glass bottle", corpus, use_llm=False)
    assert code == "ANSWERED"
    assert "Category:" in resp and "Preparation:" in resp and "Facility:" in resp


def test_hazardous_refused(corpus):
    _, code, resp = process_query("how do I recycle a lithium battery", corpus, use_llm=False)
    assert code == "REFUSED"
    assert "cannot help" in resp


def test_unsafe_detector():
    assert is_unsafe("dispose of a power bank")
    assert not is_unsafe("recycle a paper cup")


def test_ambiguous_clarify(corpus):
    _, code, _ = process_query("I have a greasy cardboard box", corpus, use_llm=False)
    assert code == "AMBIGUOUS"


def test_ambiguous_detector():
    assert is_ambiguous("not sure if this is plastic")
    assert not is_ambiguous("recycle a plastic bottle")


def test_unsupported_item(corpus):
    _, code, _ = process_query("recycle a piano", corpus, use_llm=False)
    assert code == "UNSUPPORTED"


def test_empty_query(corpus):
    _, code, _ = process_query("   ", corpus, use_llm=False)
    assert code == "EMPTY"
