"""System prompt text for the issue root cause coaching topic (GitHub #132)."""

from pathlib import Path

_PROMPT_PATH = Path(__file__).with_name("issue_root_cause_coaching_system.txt")


def load_issue_root_cause_coaching_system_prompt() -> str:
    """Return the leadership root-cause coaching system prompt from the bundled text file."""
    return _PROMPT_PATH.read_text(encoding="utf-8")
