"""Tests for the Archivist's read-only SQL tool (no LLM needed)."""
from app.agent.archivist import execute_sql


def test_guard_blocks_writes():
    assert "Rejected" in execute_sql.invoke({"query": "DELETE FROM hero"})
    assert "Rejected" in execute_sql.invoke({"query": "DROP TABLE hero"})
    assert "Rejected" in execute_sql.invoke({"query": "UPDATE hero SET gold = 9999"})


def test_guard_blocks_multiple_statements():
    assert "Rejected" in execute_sql.invoke({"query": "SELECT 1; DROP TABLE hero"})


def test_select_runs_against_seeded_db(client):
    # `client` triggers lifespan -> tables + seed into the test DB.
    out = execute_sql.invoke({"query": "SELECT COUNT(*) AS n FROM monster"})
    assert out.startswith("n"), out  # header line present, query ran


def test_created_at_column_not_falsely_blocked(client):
    # 'created_at' contains 'create' — the guard must use word boundaries, not substrings.
    out = execute_sql.invoke({"query": "SELECT name, created_at FROM hero"})
    assert "Rejected" not in out
