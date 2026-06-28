# -*- coding: utf-8 -*-
"""Safety checks for TextToSQL database helpers."""

from clients.db.client import apply_default_limit, is_safe_select_sql


def test_allows_single_select() -> None:
    assert is_safe_select_sql("SELECT id, name FROM users;")


def test_rejects_mutating_sql() -> None:
    assert not is_safe_select_sql("DELETE FROM users")
    assert not is_safe_select_sql("SELECT * FROM users; DROP TABLE users")


def test_adds_default_limit() -> None:
    assert apply_default_limit("SELECT * FROM users", max_rows=10) == "SELECT * FROM users LIMIT 10;"


def test_keeps_existing_limit() -> None:
    assert apply_default_limit("SELECT * FROM users LIMIT 5;", max_rows=10) == "SELECT * FROM users LIMIT 5;"
