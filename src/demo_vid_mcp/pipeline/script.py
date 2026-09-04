"""Script parsing, validation, and README-aware default generation."""

import re
from pathlib import Path

import yaml

from demo_vid_mcp.config import config


def _read_repo_readme(repo: str) -> str | None:
    """Try to read the target repo's README for context-aware script generation."""
    readme_path = config.repos_root / repo / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return None


def _parse_router_paths(app_tsx: Path) -> dict[str, str]:
    """Parse `<Route path="X" element={<Component` declarations from a react-router
    App.tsx into {ComponentName: "/x"}.

    Component filenames don't reliably predict real route paths - e.g. arxiv-mcp's
    ApiDocsPage.tsx is mounted at /swagger, not /apidocs. Guessing the path from the
    filename (lowercased, "Page" suffix stripped) produced 404s for any repo whose
    routes don't happen to match that convention. Returns {} for SPAs with no
    react-router routes at all (e.g. demo-vid-mcp's own App.tsx, which is a single page
    with in-memory nav state) - callers should fall back to "/" in that case, since
    there's nothing else to goto.
    """
    if not app_tsx.exists():
        return {}
    text = app_tsx.read_text(encoding="utf-8", errors="ignore")
    routes: dict[str, str] = {}
    for m in re.finditer(r'<Route\s+(?:index\s+)?path="([^"]*)"\s+element=\{<(\w+)', text):
        path, component = m.group(1), m.group(2)
        if path in ("", "*"):
            continue
        routes[component] = path if path.startswith("/") else f"/{path}"
    return routes


def _read_webapp_table(readme: str) -> dict[str, str]:
    """Parse a README's `## Webapp` page-purpose table into {lowercase page name: purpose}.

    Matches the fleet README convention (`| Page | Purpose |` markdown table under a
    "## Webapp" heading, e.g. `| **Dashboard** | Backend status, KPI cards... |`) so
    auto-drafted narration can say what a page actually *does* instead of just naming
    it. Returns {} if the repo's README has no such section - callers fall back to a
    generic line in that case.
    """
    section = re.search(r"(?:^|\n)##\s*Webapp\b.*?(?=\n##\s|\Z)", readme, re.IGNORECASE | re.DOTALL)
    if not section:
        return {}
    table: dict[str, str] = {}
    for line in section.group(0).splitlines():
        m = re.match(r"\|\s*\*{0,2}([\w /-]+?)\*{0,2}\s*\|\s*(.+?)\s*\|\s*$", line)
        if m and not re.match(r"^-+$", m.group(1).strip()):
            name, purpose = m.group(1).strip().lower(), m.group(2).strip()
            if name and purpose and name != "page":
                table[name] = purpose
    return table


# Keyword heuristics for a page's default detail level when the caller
# doesn't specify one explicitly. "skip" = leave out of the tour entirely
# (low visual/narrative value); "detail" = worth lingering on and narrating
# more fully; everything else defaults to "show" (a normal brief visit).
_SKIP_KEYWORDS = ("log", "swagger", "apidocs", "api docs", "help", "setting")
_DETAIL_KEYWORDS = ("search", "depot", "dashboard", "chat", "generate")


def default_page_level(name: str) -> str:
    """Heuristic default detail level ("skip" | "show" | "detail") for a page name."""
    lower = name.lower()
    if any(k in lower for k in _SKIP_KEYWORDS):
        return "skip"
    if any(k in lower for k in _DETAIL_KEYWORDS):
        return "detail"
    return "show"


def list_pages_with_defaults(repo: str) -> list[dict]:
    """Pages for a repo, each with its README-sourced purpose (if any) and a
    default detail level, for the Generate page's page-selection checklist.
    """
    readme = _read_repo_readme(repo)
    webapp_table = _read_webapp_table(readme) if readme else {}
    result = []
    for page in _find_pages(repo):
        result.append(
            {
                "name": page["name"],
                "path": page["path"],
                "purpose": webapp_table.get(page["name"]),
                "level": default_page_level(page["name"]),
            }
        )
    return result


def _find_pages(repo: str) -> list[dict]:
    """Scan a repo's webapp for page routes to generate meaningful steps.

    Prefers the real route table parsed from App.tsx; falls back to a
    lowercased-filename guess only for a page whose component isn't found in that
    table at all (e.g. the router file couldn't be parsed for some reason).
    """
    webapp_dirs = ["web_sota/src/pages", "webapp/src/pages", "frontend/src/pages"]
    pages = []
    for rel in webapp_dirs:
        pages_dir = config.repos_root / repo / rel
        if pages_dir.exists():
            router_paths = _parse_router_paths(pages_dir.parent / "App.tsx")
            for f in sorted(pages_dir.glob("*.tsx")):
                name = f.stem.replace("Page", "").lower()
                path = router_paths.get(f.stem) or f"/{name}"
                pages.append({"file": f.stem, "name": name, "path": path})
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


def default_script(repo: str, page_config: dict[str, str] | None = None) -> dict:
    """Generate a default narration script by reading the repo's README.

    page_config optionally maps {page name: "skip"|"show"|"detail"}, overriding
    default_page_level()'s keyword-based guess per page (see the Generate page's
    page-selection checklist). Falls back to a generic placeholder if the repo is
    not found locally.
    """
    readme = _read_repo_readme(repo)
    pages = _find_pages(repo)
    page_config = page_config or {}

    if not readme and not pages:
        return yaml.safe_load(_PLACEHOLDER_SCRIPT.format(repo=repo))

    title = f"Demo of {repo}"
    steps = []

    # Extract a one-liner from README - skip headings, images, raw HTML
    # (badge wrappers like <p align="center">), and standalone badge/link
    # lines that are just a wall of markdown link syntax with no prose.
    first_line = ""
    if readme:
        for line in readme.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "![", "<", "[![")):
                continue
            if line.count("](") >= 2:  # a line that's mostly badges/links, not prose
                continue
            first_line = line[:160]
            break

    # Title card first: a text_overlay held on screen before the webapp is
    # ever shown, rather than cutting straight to clicking around. say text
    # is the fuller intro; on-screen text is a short version of the same.
    intro_say = f"{repo}. {first_line}" if first_line else f"Welcome to {repo}."
    steps.append(
        {
            "action": "text_overlay",
            "text": f"{repo}\n\n{first_line}" if first_line else repo,
            "wait": 4,
            "say": intro_say,
        }
    )
    steps.append(
        {
            "action": "goto",
            "url": "/",
            "wait": 2,
            "say": "Let's take a look.",
        }
    )

    # Add steps for each page found in the webapp, narrated from the
    # README's Webapp/page-purpose table when available (what the page
    # actually does) rather than just naming it. Detail level - "skip"
    # (leave out), "show" (brief visit), "detail" (linger + fuller
    # narration) - comes from page_config if the caller specified one for
    # this page, else a keyword-based default (see default_page_level()).
    webapp_table = _read_webapp_table(readme) if readme else {}
    for page in pages:
        level = page_config.get(page["name"], default_page_level(page["name"]))
        if level == "skip":
            continue
        purpose = webapp_table.get(page["name"])
        if level == "detail" and purpose:
            say = f"The {page['name']} page. {purpose}. Here's what you can do here."
            wait = 8
        elif purpose:
            say = f"The {page['name']} page: {purpose}"
            wait = 4
        elif level == "detail":
            # No README purpose table entry, but this page still earned "detail"
            # from the keyword heuristic (default_page_level) - give it real
            # dwell time and a line that frames it as worth exploring instead of
            # falling back to the same bare "The X page." as a skipped-over "show".
            say = (
                f"The {page['name']} page. This is one of the most useful parts "
                f"of {repo} - take a moment to see what's here."
            )
            wait = 6
        else:
            say = f"The {page['name']} page."
            wait = 2
        steps.append(
            {
                "action": "goto",
                "url": page["path"],
                "wait": wait,
                "say": say,
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
            # Require a backtick-wrapped name specifically (`tool_name(...)`) -
            # matching on a bare "| Word" also caught the table's own header
            # row ("| Tool | Description |"), producing "Try Tool to get
            # started" as the closing line.
            for line in lines:
                m = re.match(r"\|\s*`(\w+)", line)
                if m:
                    tool_names.append(m.group(1))
            if tool_names:
                steps.append(
                    {
                        "action": "end",
                        "wait": 2,
                        "say": f"{len(tool_names)} tools available. Try {tool_names[0]} to get started.",
                    }
                )
            else:
                steps.append(
                    {
                        "action": "end",
                        "wait": 2,
                        "say": f"{repo}. Open source. One command install.",
                    }
                )
        else:
            steps.append(
                {"action": "end", "wait": 2, "say": f"{repo}. Open source. One command install."}
            )
    else:
        steps.append(
            {"action": "end", "wait": 2, "say": f"{repo}. Open source. One command install."}
        )

    content_seconds = sum(float(s.get("wait", 0)) for s in steps)
    return {
        "title": title,
        "duration_target": max(30, round(content_seconds) + 5),
        "voice": "heart",
        "aspect_ratio": "16:9",
        "resolution": "720p",
        "bg_music": False,
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

    # Validate aspect_ratio if specified
    aspect = script.get("aspect_ratio")
    if aspect and aspect not in ("16:9", "9:16"):
        return {
            "success": False,
            "error": f"Invalid aspect_ratio '{aspect}'. Supported: '16:9', '9:16'",
        }

    # Validate resolution if specified
    resolution = script.get("resolution")
    if resolution and resolution not in ("720p", "1080p"):
        return {
            "success": False,
            "error": f"Invalid resolution '{resolution}'. Supported: '720p', '1080p'",
        }

    for i, step in enumerate(script["steps"]):
        if "action" not in step:
            return {"success": False, "error": f"Step {i}: missing 'action'"}
    return {"success": True, "script": script}
