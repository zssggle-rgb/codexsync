"""Tests for sync module."""

from codexsync.sync import scan_sessions, check_locked


def test_scan_sessions_returns_list():
    """scan_sessions should return a list of tuples."""
    result = scan_sessions()
    assert isinstance(result, list)


def test_check_locked_returns_list():
    """check_locked should return a list of locked db names."""
    result = check_locked()
    assert isinstance(result, list)
