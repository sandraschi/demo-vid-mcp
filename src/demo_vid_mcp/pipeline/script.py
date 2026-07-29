"""Script parsing, validation, and README-aware default generation."""

import re
from pathlib import Path

import yaml

_REPOS_ROOT = Path("D:/Dev/repos")


def _read_repo_readme(repo: str) -> str | None:
    """Try to read the target repo's README for context-aware script generation."""
    readme_path = _REPOS_ROOT / repo / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return None


def _find_pages(repo: str) -> list[dict]:
    """Scan a repo's webapp for page routes to generate meaningful steps."""
    webapp_dirs = ["web_sota/src/pages", "webapp/src/pages", "frontend/src/pages"]
    pages = []
    for rel in webapp_dirs:
        pages_dir = _REPOS_ROOT / repo / rel
        if pages_dir.exists():
            for f in sorted(pages_dir.glob("*.tsx")):
                name = f.stem.replace("Page", "").lower()
                pages.append({"file": f.stem, "name": name, "path": f"/{name.lower()}"})
    return pages


_PLACEHOLDER_SCRIPT = """title: "Demo of {repo}"
duration_target: 30
voice: "heart"
steps:
  - action: goto
    url: /
    wait: 3
    say: "Welcome to {repo}. Let's take a quick tour."
  - action: end
    say: "That was {repo}. Open source. Install in one command."
"""


def default_script(repo: str) -> dict:
    """Generate a default narration script by reading the repo's README.

    Falls back to a generic placeholder if the repo is not found locally.
    """
    readme = _read_repo_readme(repo)
    pages = _find_pages(repo)

    if not readme and not pages:
        return yaml.safe_load(_PLACEHOLDER_SCRIPT.format(repo=repo))

    title = f"Demo of {repo}"
    steps = []

    # Extract a one-liner from README
    first_line = ""
    if readme:
        for line in readme.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("!["):
                first_line = line[:120]
                break

    if first_line:
        steps.append(
            {
                "action": "goto",
                "url": "/",
                "wait": 3,
                "say": f"{repo}: {first_line}",
            }
        )
    else:
        steps.append(
            {
                "action": "goto",
                "url": "/",
                "wait": 2,
                "say": f"Welcome to {repo}.",
            }
        )

    # Add steps for each page found in the webapp
    for page in pages[:4]:
        steps.append(
            {
                "action": "goto",
                "url": page["path"],
                "wait": 2,
                "say": f"The {page['name']} page.",
            }
        )

    # Extract tool list from README for extra content
    if readme:
        tool_section = re.search(
            r"(?:## Tools|## Available Tools|### Tools)[^#]*", readme, re.IGNORECASE
        )
        if tool_section:
            lines = tool_section.group(0).splitlines()
            tool_names = []
            for line in lines:
                m = re.match(r"[|`]\s*\*?`?(\w+)", line)
                if m:
                    tool_names.append(m.group(1))
            if tool_names:
                steps.append(
                    {
                        "action": "end",
                        "say": f"{len(tool_names)} tools available. Try {tool_names[0]} to get started.",
                    }
                )
            else:
                steps.append({"action": "end", "say": f"{repo}. Open source. One command install."})
        else:
            steps.append({"action": "end", "say": f"{repo}. Open source. One command install."})
    else:
        steps.append({"action": "end", "say": f"{repo}. Open source. One command install."})

    return {
        "title": title,
        "duration_target": min(len(steps) * 15, 90),
        "voice": "heart",
        "steps": steps,
    }


def validate_script(raw: str) -> dict:
    """Validate a YAML narration script for structure and timing."""
    try:
        script = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        return {"success": False, "error": f"YAML parse failed: {e}"}
    if (
        not isinstance(script, dict)
        or "steps" not in script
        or not isinstance(script["steps"], list)
    ):
        return {"success": False, "error": "Missing 'steps' list"}
    for i, step in enumerate(script["steps"]):
        if "action" not in step:
            return {"success": False, "error": f"Step {i}: missing 'action'"}
    return {"success": True, "script": script}
