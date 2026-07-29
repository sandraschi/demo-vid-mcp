"""Script parsing, validation, and default narration YAML generation."""

import yaml


def default_script(repo: str) -> dict:
    raw = _SCRIPT_TEMPLATE.format(repo=repo)
    return yaml.safe_load(raw)


def validate_script(raw: str) -> dict:
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


_SCRIPT_TEMPLATE = """title: "Demo of {repo}"
duration_target: 60
voice: "heart"
steps:
  - action: goto
    url: "/"
    wait: 3
    say: "Welcome to {repo}. Let's take a quick tour."
  - action: end
    say: "That was {repo}. Open source. Install in one command."
"""
