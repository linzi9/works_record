"""
agent.py -- Agent Loop for qing-agent.

The loop never changes -- only the tool dispatch layer grows.
Principle: while True + stop_reason + TOOL_HANDLERS dispatch.
"""

import os
import sys
import time
from dataclasses import dataclass, field

try:
    import readline
    readline.parse_and_bind("set bind-tty-special-chars off")
    readline.parse_and_bind("set input-meta on")
    readline.parse_and_bind("set output-meta on")
    readline.parse_and_bind("set convert-meta off")
    readline.parse_and_bind("set enable-meta-keybindings on")
except ImportError:
    pass

from anthropic import Anthropic
from anthropic import (
    APITimeoutError,
    RateLimitError,
    InternalServerError,
)

from config import MODEL, MAX_TOKENS
from tools import TOOLS, TOOL_HANDLERS, run_subagent, run_scaffold

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))

SYSTEM = (
    # ============================================================
    # [Identity] -- who you are, what you can do, what you cannot
    # ============================================================
    "You are qing-agent, a meta-agent that builds other AI agents. "
    "Your purpose is to help users design, build, and verify AI agents "
    "by generating well-structured, minimal, and correct code.\n\n"

    "## Core Identity\n"
    "- You are a META-agent: your job is to CREATE other agents, not to be one yourself.\n"
    "- You work in the qing-agent project directory as your workspace.\n"
    "- You generate agent code through builder/scaffold.py -- you do NOT hand-write agent loops.\n"
    "- You use knowledge tools to reference architecture patterns and skill modules.\n\n"

    "## Principles\n"
    "1. Think before coding -- clarify vague requests, present options with tradeoffs\n"
    "2. Simplicity first -- minimum code that solves the problem, nothing more\n"
    "3. Surgical changes -- touch only what you must, leave surrounding code alone\n"
    "4. Verifiable goals -- define success criteria before starting implementation\n\n"

    # ============================================================
    # [Workflow] -- 6-step agent building workflow (mandatory)
    # ============================================================
    "## Workflow: Building an Agent (MANDATORY)\n\n"

    "These steps are NOT optional. You MUST follow them in order. "
    "Never skip from a request directly to code generation.\n\n"

    "### RULE 0: think first\n"
    "After EVERY new request, start with think('Analyzing requirements...'). "
    "Do NOT call any other tool before think. This is your internal analysis step.\n\n"

    "### RULE 1: Confirmation gate\n"
    "You MUST NOT call scaffold_agent until the user explicitly confirms "
    "your proposed module combination and architecture design. "
    "Present options, wait for confirmation, then generate.\n\n"

    "### RULE 2: Step by step, no skipping\n"
    "Complete each step before moving to the next. Do not combine steps.\n\n"

    "### RULE 3: Structured output per step\n"
    "At the end of each step, output a clear marker:\n"
    "  [Step 1] Requirements: <analysis summary>\n"
    "  [Step 2] Tools: <selected tools>\n"
    "  [Step 3] Modules: <recommended modules + why>\n"
    "  [Step 4] Reference: <patterns consulted>\n"
    "  [Step 5] Generated: <files created>\n"
    "  [Step 6] Next steps: <what user should do>\n\n"

    "### The 6 Steps\n\n"

    "Step 1 -- Requirements Analysis:\n"
    "  Use think to decompose core vs. optional capabilities.\n"
    "  Decide architecture complexity: flat / subagent / team / autonomous.\n"
    "  Present 2-3 options with tradeoffs.\n"
    "  Output: [Step 1] ...\n\n"

    "Step 2 -- Select Tools:\n"
    "  Mandatory: bash, read_file, write_file, think\n"
    "  Optional: ls, glob, grep, edit_file (add as needed)\n"
    "  Keep it minimal -- start with what the agent MUST do, not what it COULD do.\n"
    "  Output: [Step 2] ...\n\n"

    "Step 3 -- Select Enhancement Modules:\n"
    "  Use list_skills to browse available module skills.\n"
    "  Use load_pattern to study architecture patterns.\n"
    "  Use search_reference to read reference implementation code.\n"
    "  After research: think('Comparing options...') and present your recommendation.\n"
    "  WAIT for user confirmation before proceeding to Step 4.\n"
    "  Output: [Step 3] ...\n\n"

    "Step 4 -- Reference Code Patterns:\n"
    "  Use load_pattern and search_reference to find patterns that match.\n"
    "  Explain how each pattern applies to the user's needs.\n"
    "  Output: [Step 4] ...\n\n"

    "Step 5 -- Generate Scaffold:\n"
    "  Call scaffold_agent (DO NOT hand-write agent loops).\n"
    "  The scaffold engine handles code generation and AST validation.\n"
    "  Output: [Step 5] ...\n\n"

    "Step 6 -- Verify & Output:\n"
    "  Check that generated files exist.\n"
    "  Return file paths, key design decisions, and suggested next steps.\n"
    "  Output: [Step 6] ...\n\n"

    # ============================================================
    # [Knowledge] -- what you know, where knowledge comes from
    # ============================================================
    "## Knowledge Architecture\n\n"

    "Your knowledge comes from four sources, loaded ON DEMAND (not pre-loaded):\n\n"
    "- list_skills -- Skills Catalog (19 module skills from s00 to s19). "
    "Call this first to discover what modules exist.\n"
    "- list_patterns / load_pattern -- Architecture Patterns (18 reusable patterns "
    "with code skeletons). Use load_pattern when you need to understand a specific pattern.\n"
    "- search_reference -- Reference implementations. Use this to read working code "
    "from the curriculum.\n"
    "- builder/scaffold.py -- Code generation engine. Generates agent.py + tools.py "
    "with AST validation.\n\n"

    "Knowledge loading strategy:\n"
    "  1. Start with list_skills to see available modules\n"
    "  2. Use think to analyze which modules fit the user's needs\n"
    "  3. Load specific patterns with load_pattern when design is confirmed\n"
    "  4. Read reference code with search_reference during implementation\n"
    "  5. Generate final code with scaffold_agent\n\n"

    # ============================================================
    # [Output] -- output standards
    # ============================================================
    "## Output Standards\n"
    "- Always explain your reasoning before generating code\n"
    "- Present clear options with tradeoffs when there are multiple valid approaches\n"
    "- Keep generated files pure ASCII (avoid GBK crashes on Windows)\n"
    "- All open() calls must specify encoding='utf-8'\n"
    "- Return file paths and key design decisions after scaffolding\n\n"

    # ============================================================
    # [Constraints]
    # ============================================================
    "## Constraints\n"
    "- Never run generated agents -- let the user do that\n"
    "- Never access external networks without explicit authorization\n"
    "- Do not hand-write agent loops -- always use scaffold_agent for code generation\n"
    "- The subagent (task tool) cannot spawn other agents (no recursive subagents)\n"
    "- All generated .py files must be valid Python (AST-verified by scaffold engine)"
)


# ============================================================
# Message normalization (s02 pattern)
# ============================================================

def normalize_messages(messages: list) -> list:
    """Normalize messages for API protocol compliance.

    Three steps:
    1. Strip internal fields (starting with '_')
    2. Fill missing tool_results with '(cancelled)'
    3. Merge consecutive same-role messages
    """
    if not messages:
        return []

    # Step 1: strip internal fields
    normalized = []
    for msg in messages:
        clean = {"role": msg["role"]}
        content = msg.get("content")
        if isinstance(content, str):
            clean["content"] = content
        elif isinstance(content, list):
            clean["content"] = [
                {k: v for k, v in b.items() if not k.startswith("_")}
                for b in content
            ]
        elif content is not None:
            clean["content"] = str(content)
        else:
            continue
        normalized.append(clean)

    # Step 2: fill missing tool_results
    existing = set()
    for msg in normalized:
        if isinstance(msg.get("content"), list):
            for b in msg["content"]:
                if b.get("type") == "tool_result":
                    existing.add(b.get("tool_use_id"))

    for msg in normalized:
        if msg["role"] == "assistant" and isinstance(msg.get("content"), list):
            for b in msg["content"]:
                if b.get("type") == "tool_use" and b.get("id") not in existing:
                    normalized.append({"role": "user", "content": [{
                        "type": "tool_result",
                        "tool_use_id": b["id"],
                        "content": "(cancelled)",
                    }]})

    # Step 3: merge consecutive same-role
    merged = [normalized[0]] if normalized else []
    for msg in normalized[1:]:
        if msg["role"] == merged[-1]["role"]:
            prev = merged[-1]
            pc = prev["content"] if isinstance(prev["content"], list) \
                else [{"type": "text", "text": prev["content"]}]
            cc = msg["content"] if isinstance(msg["content"], list) \
                else [{"type": "text", "text": msg["content"]}]
            prev["content"] = pc + cc
        else:
            merged.append(msg)
    return merged


# ============================================================
# Error Recovery (s10 pattern)
# ============================================================

@dataclass
class RecoveryState:
    """Tracks retry state for API error recovery."""
    retries: int = 0
    max_retries: int = 3


def handle_api_error(e: Exception, state: RecoveryState, messages: list) -> bool:
    """Attempt recovery from an API error.

    Returns True if recovered and the caller should retry.
    Returns False if the error is not recoverable.
    """
    if isinstance(e, (RateLimitError, InternalServerError, APITimeoutError)):
        if state.retries < state.max_retries:
            state.retries += 1
            delay = 2 ** state.retries  # 2s, 4s, 8s
            print(f"\033[33m[retry] {type(e).__name__}: waiting {delay}s "
                  f"(attempt {state.retries}/{state.max_retries})\033[0m")
            time.sleep(delay)
            return True

    # Non-recoverable: auth errors, bad request, etc.
    return False


# ============================================================
# Agent Loop
# ============================================================

def agent_loop(messages: list):
    """Run the agent loop: model -> stop_reason -> tool -> loop."""
    recovery = RecoveryState()
    while True:
        try:
            response = client.messages.create(
                model=MODEL,
                system=SYSTEM,
                messages=normalize_messages(messages),
                tools=TOOLS,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            if handle_api_error(e, recovery, messages):
                continue
            raise  # Non-recoverable, let main.py catch it

        # Reset recovery state on successful API call
        recovery = RecoveryState()
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return

        results = []
        for block in response.content:
            if block.type == "tool_use":
                name = block.name
                inp = block.input
                handler = TOOL_HANDLERS.get(name)

                # Pretty-print tool calls
                if name == "bash":
                    print(f"\033[33m$ {inp.get('command', '')}\033[0m")
                elif name == "think":
                    print(f"\033[90m[think] {inp.get('text', '')[:200]}\033[0m")
                elif name == "task":
                    desc = inp.get("description", "subtask")
                    print(f"\033[36m[task] {desc}\033[0m")
                elif name == "scaffold_agent":
                    print(f"\033[35m[scaffold_agent] {inp.get('name', 'agent')}\033[0m")
                else:
                    print(f"\033[36m[{name}] {inp.get('path', '')}\033[0m")

                if handler:
                    try:
                        output = handler(**inp)
                    except Exception as e:
                        output = f"Error executing {name}: {e}"
                elif name == "task":
                    prompt = inp.get("prompt", "")
                    desc = inp.get("description", "subtask")
                    print(f"\033[36m[task] {desc}: {prompt[:60]}...\033[0m")
                    try:
                        output = run_subagent(prompt)
                    except Exception as e:
                        output = f"Error in subagent: {e}"
                    print(f"\033[36m  result: {str(output)[:300]}\033[0m")
                elif name == "scaffold_agent":
                    name_val = inp.get("name", "agent")
                    desc_val = inp.get("description", "")
                    tools_val = inp.get("tools")
                    out_dir = inp.get("output_dir", ".")
                    tier_val = inp.get("tier", "standard")
                    print(f"\033[35m[scaffold_agent] Generating '{name_val}' (tier: {tier_val}) via subagent...\033[0m")
                    # Route through subagent for isolated execution context
                    tools_repr = str(tools_val) if tools_val is not None else "None"
                    sub_prompt = (
                        f"Scaffold a new agent named '{name_val}'.\n"
                        f"Description: {desc_val}\n"
                        f"Output directory: {out_dir}\n"
                        f"Tier: {tier_val}\n\n"
                        "1. Create a temp script .scaffold_task.py with this content "
                        "(use write_file):\n"
                        f"from builder.scaffold import scaffold\n"
                        f"result = scaffold('{name_val}', '{desc_val}', "
                        f"{tools_repr}, '{out_dir}', tier='{tier_val}')\n"
                        "for k, v in result.items():\n"
                        "    print(f'  {k}: {v}')\n\n"
                        "2. Run: python .scaffold_task.py\n"
                        f"3. Verify both agent.py and tools.py exist in {out_dir} "
                        "(use ls)\n"
                        "4. Delete .scaffold_task.py (use bash: rm .scaffold_task.py)\n"
                        "5. Return the full scaffold result with file paths"
                    )
                    try:
                        output = run_subagent(sub_prompt)
                    except Exception as e:
                        output = f"Error in scaffold subagent: {e}"
                    print(f"\033[35m  {output[:300]}\033[0m")
                else:
                    output = f"Unknown tool: {name}"

                if output and len(output) > 300:
                    print(output[:300] + "...")
                else:
                    print(output or "(no output)")

                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        messages.append({"role": "user", "content": results})
