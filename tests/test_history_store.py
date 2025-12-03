import pytest

from app.helper.history_store import (
    HISTORY,
    HISTORY_LIMIT,
    add_history,
    get_history,
)


def setup_function(_):
    """
    Run before each test: start with a clean HISTORY store.
    """
    HISTORY.clear()


def test_add_history_single_entry():
    token = "user1"
    add_history(token, "What is the deadline?", "The deadline is 1 May.")

    history = get_history(token)

    assert len(history) == 1
    assert history[0]["question"] == "What is the deadline?"
    assert history[0]["answer"] == "The deadline is 1 May."


def test_add_history_preserves_order():
    token = "userX"
    add_history(token, "Q1", "A1")
    add_history(token, "Q2", "A2")
    add_history(token, "Q3", "A3")

    history = get_history(token)

    assert [h["question"] for h in history] == ["Q1", "Q2", "Q3"]
    assert [h["answer"] for h in history] == ["A1", "A2", "A3"]


def test_history_is_isolated_by_token():
    add_history("u1", "Q1", "A1")
    add_history("u2", "QX", "AY")

    hist1 = get_history("u1")
    hist2 = get_history("u2")

    assert len(hist1) == 1
    assert len(hist2) == 1

    assert hist1[0]["question"] == "Q1"
    assert hist2[0]["question"] == "QX"


def test_get_history_for_new_token_returns_empty_list():
    history = get_history("unknown_user")
    assert history == []


def test_history_respects_limit():
    token = "limited_user"

    limit = int(HISTORY_LIMIT)

    for i in range(limit + 5):
        add_history(token, f"Q{i}", f"A{i}")

    history = get_history(token)

    assert len(history) == limit

    expected_questions = [f"Q{i}" for i in range(5, limit + 5)]
    assert [h["question"] for h in history] == expected_questions
