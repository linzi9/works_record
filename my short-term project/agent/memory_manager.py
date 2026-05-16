"""MemoryManager -- cross-session memory with file-backed .md storage."""

import re
from pathlib import Path

MEMORY_TYPES = ("user", "feedback", "project", "reference")


class MemoryManager:
    """Persist key information across sessions. Each memory is one .md file."""

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, description: str, mem_type: str, content: str) -> str:
        if mem_type not in MEMORY_TYPES:
            return f"Error: Invalid type '{mem_type}'. Choose: {', '.join(MEMORY_TYPES)}"
        safe = self._safe_name(name)
        fp = self.memory_dir / f"{safe}.md"
        frontmatter = (
            "---\n"
            f"name: {safe}\n"
            f"description: {description}\n"
            f"type: {mem_type}\n"
            "---\n\n"
        )
        fp.write_text(frontmatter + content, encoding="utf-8")
        self._rebuild_index()
        return f"Saved memory '{safe}' (type: {mem_type})"

    def recall(self, name: str = "") -> str:
        if name:
            safe = self._safe_name(name)
            fp = self.memory_dir / f"{safe}.md"
            return fp.read_text(encoding="utf-8") if fp.exists() else f"Memory '{safe}' not found"
        return self._load_index()

    def delete(self, name: str) -> str:
        safe = self._safe_name(name)
        fp = self.memory_dir / f"{safe}.md"
        if not fp.exists():
            return f"Memory '{safe}' not found"
        fp.unlink()
        self._rebuild_index()
        return f"Deleted memory '{safe}'"

    def session_context(self) -> str:
        parts = ["<memory_context>"]
        for f in sorted(self.memory_dir.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            parts.append(f.read_text(encoding="utf-8"))
        parts.append("</memory_context>")
        return "\n\n".join(parts)

    def _safe_name(self, name: str) -> str:
        return name.lower().strip().replace(" ", "_").replace("-", "_")

    def _rebuild_index(self):
        memories = []
        for f in sorted(self.memory_dir.glob("*.md")):
            if f.name == "MEMORY.md":
                continue
            meta = self._parse_frontmatter(f.read_text(encoding="utf-8"))
            if meta:
                mt = meta.get("type", "?")
                desc = meta.get("description", "(no description)")
                memories.append(f"- [{meta['name']}]({f.name}) -- [{mt}] {desc}")
        (self.memory_dir / "MEMORY.md").write_text("\n".join(memories), encoding="utf-8")

    def _load_index(self) -> str:
        idx = self.memory_dir / "MEMORY.md"
        return idx.read_text(encoding="utf-8") if idx.exists() else "(no memories saved yet)"

    def _parse_frontmatter(self, text: str) -> dict:
        meta = {}
        m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
        return meta
