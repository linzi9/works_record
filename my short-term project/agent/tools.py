"""
tools.py -- Tool handlers and dispatch map for qing-agent.

Each tool = handler function + schema + dispatch map entry.
The agent loop never changes -- only this file grows.
"""

import glob as glob_module
import os
import re
import subprocess
from pathlib import Path

from anthropic import Anthropic

from config import MODEL, MAX_TOKENS, WORKDIR

# Subagent client (separate instance for isolated sub-tasks)
_subagent_client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))


# ============================================================
# Safe path (prevent workspace escape)
# ============================================================

def safe_path(p: str) -> Path:
    """Resolve a path relative to WORKDIR and prevent escape."""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


# ============================================================
# Tool: bash
# ============================================================

def run_bash(command: str) -> str:
    """Execute a shell command with safety guards."""
    blocked_patterns = [
        "rm -rf /", "rm -rf /*", "rm -rf / ", "rm -rf /--",
        "sudo", "shutdown", "reboot", "> /dev/",
        "mkfs.", "dd if=", "chmod 777 /",
    ]
    cmd_lower = command.lower()
    if any(p in cmd_lower for p in blocked_patterns):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or f"exit code {r.returncode}").strip()
            return f"Error: {msg[:50000]}"
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


# ============================================================
# Tool: read_file
# ============================================================

def run_read(path: str, limit: int = None) -> str:
    """Read file contents with optional line limit."""
    try:
        text = safe_path(path).read_text(encoding="utf-8")
        lines = text.splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Tool: write_file
# ============================================================

def run_write(path: str, content: str) -> str:
    """Write content to file, creating parent directories automatically."""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Tool: think
# ============================================================

def run_think(text: str) -> str:
    """Internal reasoning: return text as-is (no-op handler)."""
    return text


# ============================================================
# Tool: ls
# ============================================================

def run_ls(path: str = ".") -> str:
    """List directory contents."""
    try:
        p = safe_path(path)
        if not p.is_dir():
            return f"Error: Not a directory: {path}"
        entries = sorted(
            f"{e.name}{'/' if e.is_dir() else ''}" for e in p.iterdir()
        )
        return "\n".join(entries) if entries else "(empty)"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Tool: glob
# ============================================================

def run_glob(pattern: str) -> str:
    """Find files matching a glob pattern."""
    matches = sorted(glob_module.glob(pattern, root_dir=WORKDIR, recursive=True))
    return "\n".join(matches) if matches else "(no matches)"


# ============================================================
# Tool: grep
# ============================================================

def run_grep(pattern: str, path: str) -> str:
    """Search for pattern in a file, return matching lines."""
    try:
        fp = safe_path(path)
        if not fp.is_file():
            return f"Error: Not a file: {path}"
        text = fp.read_text(encoding="utf-8")
        lines = text.splitlines()
        results = [(i + 1, l) for i, l in enumerate(lines) if re.search(pattern, l)]
        if not results:
            return "(no matches)"
        out = "\n".join(f"{ln}:{line}" for ln, line in results)
        return out[:50000]
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Tool: edit_file
# ============================================================

def run_edit(path: str, old_text: str, new_text: str) -> str:
    """Replace the first occurrence of exact text in a file."""
    try:
        fp = safe_path(path)
        content = fp.read_text(encoding="utf-8")
        if old_text not in content:
            return f"Error: Text not found in {path}"
        fp.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# Knowledge Tools (Step 3: knowledge injection)
# ============================================================

def run_list_skills() -> str:
    """Show skills catalog -- list all available module skills."""
    try:
        from knowledge.skills_catalog import SkillsCatalog
        return SkillsCatalog().list_all()
    except Exception as e:
        return f"Error loading skills catalog: {e}"


def run_list_patterns() -> str:
    """Show all available architecture patterns."""
    try:
        from knowledge.patterns import PatternsDB
        return PatternsDB().list_patterns()
    except Exception as e:
        return f"Error loading patterns: {e}"


def run_load_pattern(pattern_id: str) -> str:
    """Load full content for a specific architecture pattern."""
    try:
        from knowledge.patterns import PatternsDB
        return PatternsDB().load_pattern(pattern_id)
    except Exception as e:
        return f"Error loading pattern: {e}"


def run_search_reference(skill_name: str, ref_file: str | None = None) -> str:
    """Read reference implementation code for a skill."""
    try:
        from knowledge.references import ReferencesDB
        return ReferencesDB().read_reference(skill_name, ref_file)
    except Exception as e:
        return f"Error reading reference: {e}"


# ============================================================
# Memory System (s08 pattern)
# ============================================================

MEMORY_DIR = WORKDIR / ".memory"
_memory_manager = None

def _get_memory():
    global _memory_manager
    if _memory_manager is None:
        from memory_manager import MemoryManager
        _memory_manager = MemoryManager(MEMORY_DIR)
    return _memory_manager


def run_save_memory(name: str, description: str, type: str, content: str) -> str:
    """Save a memory across sessions."""
    return _get_memory().save(name, description, type, content)


def run_recall_memory(name: str = "") -> str:
    """Recall saved memories."""
    return _get_memory().recall(name)


def run_delete_memory(name: str) -> str:
    """Delete a saved memory."""
    return _get_memory().delete(name)


# ============================================================
# Task System (s12 pattern)
# ============================================================

TASKS_DIR = WORKDIR / ".tasks"
_task_manager = None

def _get_tasks():
    global _task_manager
    if _task_manager is None:
        from task_manager import TaskManager
        _task_manager = TaskManager(TASKS_DIR)
    return _task_manager


def run_task_create(subject: str, description: str = "",
                    blocked_by: list = None, owner: str = "") -> str:
    """Create a persistent task with optional dependencies."""
    t = _get_tasks().create(subject, description, blocked_by, owner)
    return f"Created {t.id}: {t.subject} (status: {t.status})"


def run_task_update(task_id: str, status: str = None, owner: str = None) -> str:
    """Update task status or owner."""
    kwargs = {}
    if status: kwargs["status"] = status
    if owner: kwargs["owner"] = owner
    t = _get_tasks().update(task_id, **kwargs)
    if not t:
        return f"Task not found: {task_id}"
    # If completing, use complete() for auto-unlock
    if status == "completed":
        t = _get_tasks().complete(task_id)
    deps = f", blocked_by: {t.blocked_by}" if t.blocked_by else ""
    return f"Updated {t.id}: {t.subject} -> {t.status}{deps}"


def run_task_get(task_id: str) -> str:
    """Get details of a specific task."""
    t = _get_tasks().get(task_id)
    if not t:
        return f"Task not found: {task_id}"
    return (f"ID: {t.id}\nSubject: {t.subject}\nDescription: {t.description}\n"
            f"Status: {t.status}\nOwner: {t.owner}\n"
            f"Blocked by: {t.blocked_by or '(none)'}\nBlocks: {t.blocks or '(none)'}")


def run_task_list() -> str:
    """List all tasks with status and dependencies."""
    tm = _get_tasks()
    all_t = tm.list_all()
    if not all_t:
        return "(no tasks)"
    lines = []
    for t in all_t:
        ready = "READY" if t.id in {x.id for x in tm.ready_tasks()} else "BLOCKED" if t.status == "pending" else ""
        flag = f" [{ready}]" if ready else ""
        deps = f" (depends: {t.blocked_by})" if t.blocked_by else ""
        lines.append(f"  {t.id:12s} | {t.status:12s} | {t.subject}{deps}{flag}")
    return "\n".join(lines)


# ============================================================
# Background Task System (s13 pattern)
# ============================================================

RUNTIME_DIR = WORKDIR / ".runtime-tasks"
_background_manager = None

def _get_bg():
    global _background_manager
    if _background_manager is None:
        from bg_task import BackgroundManager
        _background_manager = BackgroundManager(RUNTIME_DIR)
    return _background_manager


def run_background_run(command: str, description: str = "", timeout: int = 300) -> str:
    """Run a command in the background, returns immediately."""
    tid = _get_bg().run(command, description=description, timeout=timeout)
    return f"Background task started: {tid}"


def run_background_check(task_id: str) -> str:
    """Check status of a background task."""
    rec = _get_bg().check(task_id)
    if not rec:
        return f"Task not found: {task_id}"
    status = rec.get("status", "unknown")
    preview = rec.get("result_preview", "")
    out = f"Task: {task_id} | Status: {status}"
    if preview:
        out += f"\nPreview: {preview[:300]}"
    return out


# ============================================================
# Subagent System (s04 pattern)
# ============================================================

SUBAGENT_SYSTEM = (
    "You are a research subagent. Complete the assigned task "
    "and return a concise summary of your findings.\n\n"
    "You can:\n"
    "- Read/write files and run shell commands\n"
    "- List directories and search file contents\n\n"
    "You CANNOT spawn other agents or modify system files.\n\n"
    "When done, return a clear, focused summary."
)


def run_subagent(prompt: str, max_turns: int = 30) -> str:
    """Spawn a subagent with isolated context for a subtask.

    Fresh messages, restricted tools, max_turns cap.
    Returns text summary only (sub-context discarded).
    """
    sub_messages = [{"role": "user", "content": prompt}]

    for turn in range(max_turns):
        try:
            response = _subagent_client.messages.create(
                model=MODEL,
                system=SUBAGENT_SYSTEM,
                messages=sub_messages,
                tools=SUBAGENT_TOOLS,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            return f"Error: Subagent failed at turn {turn}: {e}"

        sub_messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = SUBAGENT_HANDLERS.get(block.name)
                if handler:
                    try:
                        output = handler(**block.input)
                    except Exception as e:
                        output = f"Error executing {block.name}: {e}"
                else:
                    output = f"Unknown tool: {block.name}"
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output)[:50000],
                })

        sub_messages.append({"role": "user", "content": results})

    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"


# Subagent tool set -- no task/scaffold_agent to prevent recursion
SUBAGENT_TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command for exploration or setup.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read file contents. Paths relative to workspace root.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "limit": {"type": "integer", "description": "Optional: max lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates parent dirs automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "ls",
        "description": "List directory contents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path relative to workspace (default: current dir)"},
            },
            "required": [],
        },
    },
    {
        "name": "think",
        "description": "Internal reasoning step. Use to analyze or plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Your reasoning or analysis"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to match"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep",
        "description": "Search a file for lines matching a regex pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "File path relative to workspace"},
            },
            "required": ["pattern", "path"],
        },
    },
]

SUBAGENT_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "ls":         lambda **kw: run_ls(kw.get("path", ".")),
    "think":      lambda **kw: run_think(kw["text"]),
    "glob":       lambda **kw: run_glob(kw["pattern"]),
    "grep":       lambda **kw: run_grep(kw["pattern"], kw["path"]),
}

TASK_TOOL = {
    "name": "task",
    "description": (
        "[Step 4-5 -- Subagent Execution] Spawn a subagent with a clean, isolated context "
        "to handle a subtask. The subagent shares the filesystem but NOT the conversation "
        "history -- it starts fresh and returns only a summary. "
        "Use for code generation (especially scaffold_agent), research, or any self-contained "
        "subtask that should not pollute the main conversation context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed instructions for the subagent. Be specific about what to do and what to return.",
            },
            "description": {
                "type": "string",
                "description": "Short label (3-5 words) describing this subtask for progress display.",
            },
        },
        "required": ["prompt"],
    },
}


# ============================================================
# Scaffold Agent Tool
# ============================================================

def run_scaffold(name: str, description: str, tools: list[str] | None = None,
                 output_dir: str = ".", tier: str = "standard") -> str:
    """Generate a complete agent via builder/scaffold.py.

    Generates agent.py + tools.py, validates via AST, writes to disk.
    """
    try:
        from builder.scaffold import scaffold as _scaffold
        result = _scaffold(name, description, tools, output_dir, tier)
        if result["success"]:
            parts = [f"Scaffold complete: {name} (tier: {tier})"]
            for label, path in result["paths"].items():
                parts.append(f"  {label} -> {path}")
            return "\n".join(parts)
        else:
            return "Scaffold failed:\n" + "\n".join(result["errors"])
    except Exception as e:
        return f"Error: scaffold_agent failed: {e}"


SCAFFOLD_TOOL = {
    "name": "scaffold_agent",
    "description": (
        "[Step 5 -- Code Generation] CRITICAL: Only call this AFTER the user confirms "
        "the design proposal. Generate a complete, working AI agent from a description. "
        "Creates agent.py (agent loop + message normalization) and "
        "tools.py (requested tools + dispatch map) in the specified directory. "
        "Generated code is validated via AST before writing. "
        "Execution is automatically isolated through a subagent to prevent context pollution. "
        "Supports tier: lite (4 tools), standard (8 tools), full (all tools)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the generated agent (e.g., 'research-agent')",
            },
            "description": {
                "type": "string",
                "description": "What this agent does -- used in system prompt",
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tools to include. Options: bash, read_file, write_file, think, ls, glob, grep, edit_file. Default: determined by tier.",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory relative to workspace (default: current dir)",
            },
            "tier": {
                "type": "string",
                "enum": ["lite", "standard", "full"],
                "description": "Complexity tier. lite=4 tools, standard=8 tools, full=all tools (default: standard)",
            },
        },
        "required": ["name", "description"],
    },
}


# ============================================================
# Tool Schemas
# ============================================================

TOOLS = [
    {
        "name": "bash",
        "description": "[Steps 3-5 -- Execution] Run a shell command. Use for installing packages, creating dirs, running scripts, and any CLI operations. Output capped at 50000 chars. Timeout at 120 seconds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "[Steps 1-5 -- Investigation] Read file contents with optional line limit. All paths relative to workspace root. Use to inspect existing code, read requirements docs, or verify generated output.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "limit": {"type": "integer", "description": "Optional: max lines to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "[Step 5 -- Output] Write content to a file. Creates parent directories automatically. All paths relative to workspace root. Use for writing generated agent code or saving analysis results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace root"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "think",
        "description": "[Step 1 -- Requirements Analysis] Internal reasoning step. ALWAYS start here when you receive a new request. Use this to analyze requirements, decompose core vs optional capabilities, decide architecture complexity (flat/subagent/team/autonomous), compare options, and plan before calling any other tool. Does NOT trigger any external operation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Your reasoning or analysis"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "ls",
        "description": "[Steps 2-5 -- Exploration] List directory contents. Shows files and subdirectories with '/' suffix on dirs. Use to explore project structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path relative to workspace (default: current dir)"},
            },
            "required": [],
        },
    },
    {
        "name": "glob",
        "description": "[Steps 2-5 -- Exploration] Find files matching a glob pattern. Supports ** for recursive matching. Use to discover project files by pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to match (e.g., '*.py', 'src/**/*.ts')"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep",
        "description": "[Steps 2-5 -- Investigation] Search a file for lines matching a regex pattern. Returns matching lines with line numbers. Use to find specific code patterns or references.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "File path relative to workspace"},
            },
            "required": ["pattern", "path"],
        },
    },
    {
        "name": "edit_file",
        "description": "[Step 5 -- Refinement] Surgically replace the first occurrence of exact text in a file. Returns error if text not found. Use for small adjustments to generated code, NOT for creating new agents (use scaffold_agent for that).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace"},
                "old_text": {"type": "string", "description": "Exact text to find (first occurrence only)"},
                "new_text": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "list_skills",
        "description": "[Step 3 -- Module Selection] List all available module skills from the skills catalog (19 modules from s00-s19). Shows skill ID, name, and summary. Call this AFTER requirements analysis (Step 1) to discover what modules exist. After calling, use think to analyze options and recommend a combination to the user.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_patterns",
        "description": "[Step 3 -- Module Selection] List all available architecture patterns (18 reusable patterns with code skeletons). Shows pattern ID and title. Call this after selecting modules to find the right pattern for implementation.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "load_pattern",
        "description": "[Step 3-4 -- Reference] Load the full content of a specific architecture pattern by ID (e.g., 'pattern-1', 'pattern-5') or by title keyword. Returns pattern description and code skeleton. After loading, explain how the pattern applies to the user's needs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern_id": {
                    "type": "string",
                    "description": "Pattern ID (e.g., 'pattern-1') or title keyword to search for",
                },
            },
            "required": ["pattern_id"],
        },
    },
    {
        "name": "search_reference",
        "description": "[Step 4 -- Code Reference] Read reference implementation code for a specific skill. Use this when you need to see working code examples from the curriculum. After loading, extract key patterns and explain how to adapt them to the user's agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill (e.g., 'subagent-pattern', 'skill-system')",
                },
                "ref_file": {
                    "type": "string",
                    "description": "Optional: specific reference file name. If omitted, the first .py file is loaded.",
                },
            },
            "required": ["skill_name"],
        },
    },
    # ===== Memory Tools (s08) =====
    {
        "name": "save_memory",
        "description": "[Step 6 -- Memory] Save information across sessions. Types: user (preferences), feedback (corrections), project (context), reference (external). Only save what is valuable across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Short identifier (e.g., 'prefer_tabs')"},
                "description": {"type": "string", "description": "One-line summary"},
                "type": {"type": "string", "enum": ["user", "feedback", "project", "reference"]},
                "content": {"type": "string", "description": "The memory content"},
            },
            "required": ["name", "description", "type", "content"],
        },
    },
    {
        "name": "recall_memory",
        "description": "[Step 6 -- Memory] Retrieve saved memories. Use without name to list all via MEMORY.md index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Memory name (omit to list all)"},
            },
            "required": [],
        },
    },
    {
        "name": "delete_memory",
        "description": "[Step 6 -- Memory] Delete a saved memory by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Memory name to delete"},
            },
            "required": ["name"],
        },
    },
    # ===== Task Tools (s12) =====
    {
        "name": "task_create",
        "description": "[Step 6 -- Task System] Create a persistent task with optional dependencies. Use for multi-step work that spans across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Short task title"},
                "description": {"type": "string", "description": "Detailed description"},
                "blocked_by": {"type": "array", "items": {"type": "string"}, "description": "Task IDs that must complete first"},
                "owner": {"type": "string", "description": "Who is responsible"},
            },
            "required": ["subject"],
        },
    },
    {
        "name": "task_update",
        "description": "[Step 6 -- Task System] Update task status or owner. Set status='completed' to auto-unblock dependents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "deleted"]},
                "owner": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_get",
        "description": "[Step 6 -- Task System] Get detailed info about a specific task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_list",
        "description": "[Step 6 -- Task System] List all tasks with status, dependencies, and ready/blocked state.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    # ===== Background Task Tools (s13) =====
    {
        "name": "background_run",
        "description": "[Step 6 -- Background Tasks] Run a shell command in the background. Returns immediately with a task_id. Use background_check to poll.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "description": {"type": "string", "description": "Short label for display"},
                "timeout": {"type": "integer", "description": "Max execution time (seconds)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "background_check",
        "description": "[Step 6 -- Background Tasks] Check status of a background task by task_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
            },
            "required": ["task_id"],
        },
    },
    # task tool -- special: handled via if/elif in agent_loop, NOT in TOOL_HANDLERS
    TASK_TOOL,
    # scaffold_agent tool -- also special: handled via if/elif in agent_loop
    SCAFFOLD_TOOL,
]


# ============================================================
# Dispatch Map
# ============================================================

TOOL_HANDLERS = {
    "bash":              lambda **kw: run_bash(kw["command"]),
    "read_file":         lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file":        lambda **kw: run_write(kw["path"], kw["content"]),
    "think":             lambda **kw: run_think(kw["text"]),
    "ls":                lambda **kw: run_ls(kw.get("path", ".")),
    "glob":              lambda **kw: run_glob(kw["pattern"]),
    "grep":              lambda **kw: run_grep(kw["pattern"], kw["path"]),
    "edit_file":         lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    "list_skills":       lambda **kw: run_list_skills(),
    "list_patterns":     lambda **kw: run_list_patterns(),
    "load_pattern":      lambda **kw: run_load_pattern(kw["pattern_id"]),
    "search_reference":  lambda **kw: run_search_reference(kw["skill_name"], kw.get("ref_file")),
    "save_memory":       lambda **kw: run_save_memory(kw["name"], kw["description"], kw["type"], kw["content"]),
    "recall_memory":     lambda **kw: run_recall_memory(kw.get("name", "")),
    "delete_memory":     lambda **kw: run_delete_memory(kw["name"]),
    "task_create":       lambda **kw: run_task_create(kw["subject"], kw.get("description", ""), kw.get("blocked_by"), kw.get("owner", "")),
    "task_update":       lambda **kw: run_task_update(kw["task_id"], kw.get("status"), kw.get("owner")),
    "task_get":          lambda **kw: run_task_get(kw["task_id"]),
    "task_list":         lambda **kw: run_task_list(),
    "background_run":    lambda **kw: run_background_run(kw["command"], kw.get("description", ""), kw.get("timeout", 300)),
    "background_check":  lambda **kw: run_background_check(kw["task_id"]),
}
