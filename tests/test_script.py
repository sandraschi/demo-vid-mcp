"""Tests for script parsing and validation."""

from demo_vid_mcp.pipeline.script import (
    default_page_level,
    default_script,
    list_pages_with_defaults,
    validate_script,
)


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


def test_default_script_duration_target_at_least_30():
    """duration_target should always meet the 30s floor even for short scripts."""
    s = default_script("nonexistent-repo-12345")
    assert s["duration_target"] >= 30


def test_default_page_level_keywords():
    assert default_page_level("Logs") == "skip"
    assert default_page_level("Swagger") == "skip"
    assert default_page_level("Search") == "detail"
    assert default_page_level("Depot") == "detail"
    assert default_page_level("Settings") == "skip"
    assert default_page_level("Gallery") == "show"


def test_default_script_page_config_skip_excludes_page():
    """A page_config override of 'skip' should drop that page's goto step."""
    baseline = default_script("chitchat")
    pages = list_pages_with_defaults("chitchat")
    if not pages:
        return  # nothing to override against in this environment
    target = pages[0]["name"]
    urls_before = {s.get("url") for s in baseline["steps"]}
    overridden = default_script("chitchat", {target: "skip"})
    matching_page = next((p for p in pages if p["name"] == target), None)
    if matching_page and matching_page["path"] in urls_before:
        urls_after = {s.get("url") for s in overridden["steps"]}
        assert matching_page["path"] not in urls_after


def test_default_script_page_config_detail_gets_longer_wait():
    """A page_config override of 'detail' should dwell longer than 'show'/default."""
    pages = list_pages_with_defaults("chitchat")
    if not pages:
        return
    target = pages[0]["name"]
    detail_script = default_script("chitchat", {target: "detail"})
    show_script = default_script("chitchat", {target: "show"})
    detail_step = next(
        (s for s in detail_script["steps"] if s.get("say", "").startswith(f"The {target}")), None
    )
    show_step = next(
        (s for s in show_script["steps"] if s.get("say", "").startswith(f"The {target}")), None
    )
    if detail_step and show_step:
        assert detail_step["wait"] > show_step["wait"]


def test_list_pages_with_defaults_shape():
    pages = list_pages_with_defaults("nonexistent-repo-12345")
    assert pages == []


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
