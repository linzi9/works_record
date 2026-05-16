"""Configuration for qing-agent meta-agent."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
MAX_TOKENS = 8192
WORKDIR = Path(__file__).resolve().parent

TIER_TOOLS = {
    "lite":     ["bash", "read_file", "write_file", "think"],
    "standard": ["bash", "read_file", "write_file", "think", "ls", "glob", "grep", "edit_file"],
    "full":     None,  # None = all tools
}
