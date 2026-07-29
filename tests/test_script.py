"""Tests for script parsing and validation."""
from demo_vid_mcp.pipeline.script import default_script, validate_script


def test_default_script_has_steps():
    s = default_script("chitchat")
    assert "steps" in s
    # chitchat is a local repo, so we should get a script with actual steps
    assert len(s["steps"]) >= 2


def test_default_script_unknown_repo():
    """Unknown repo should get the placeholder script."""
    s = default_script("nonexistent-repo-12345")
    assert "steps" in s
    assert len(s["steps"]) >= 2


def test_validate_empty():
    r = validate_script("")
    assert not r["success"]


def test_validate_null():
    r = validate_script("null")
    assert not r["success"]


def test_validate_good():
    y = "steps:\n  - action: goto\n    url: /\n    wait: 2\n  - action: end\n    say: done"
    r = validate_script(y)
    assert r["success"]
    assert len(r["script"]["steps"]) == 2


def test_validate_missing_action():
    y = "steps:\n  - url: /"
    r = validate_script(y)
    assert not r["success"]
