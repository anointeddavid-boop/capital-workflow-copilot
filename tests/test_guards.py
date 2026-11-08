import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from chunk_filings import chunk_text
from sql_tool import check_query


def test_plain_select_is_allowed():
    sql, problem = check_query("SELECT * FROM funds;")
    assert problem is None
    assert sql == "SELECT * FROM funds"


def test_delete_is_blocked():
    sql, problem = check_query("DELETE FROM funds")
    assert sql is None
    assert "SELECT" in problem


def test_two_statements_are_blocked():
    sql, problem = check_query("SELECT 1; DROP TABLE funds")
    assert sql is None
    assert "more than one" in problem


def test_drop_inside_a_select_is_blocked():
    sql, problem = check_query("SELECT * FROM funds WHERE fund_name = 'x' OR drop = 1")
    assert sql is None


def test_no_query_reply_is_handled():
    sql, problem = check_query("NO_QUERY")
    assert sql is None
    assert problem


def test_chunks_stay_under_the_size_limit():
    text = "word " * 1000
    chunks = chunk_text(text, 100, 20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_empty_text_gives_no_chunks():
    assert chunk_text("", 100, 20) == []
