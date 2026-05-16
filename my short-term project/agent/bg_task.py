"""BackgroundManager -- thread-level background task execution."""

import json
import subprocess
import threading
import time
from pathlib import Path
from uuid import uuid4


class BackgroundManager:
    """Run shell commands in daemon threads with status polling."""

    def __init__(self, runtime_dir: str | Path = ".runtime-tasks"):
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.tasks: dict[str, dict] = {}
        self.notifications: list[dict] = []
        self.lock = threading.Lock()
        self._recover()

    def run(self, command: str, cwd: str = None,
            description: str = "", timeout: int = 300) -> str:
        tid = f"bg_{uuid4().hex[:8]}"
        out_file = self.runtime_dir / f"{tid}.log"
        record = {
            "id": tid, "command": command, "description": description or command[:60],
            "status": "running", "started_at": time.time(),
            "result_preview": "", "output_file": str(out_file),
        }
        with self.lock:
            self.tasks[tid] = record
        self._save_record(record)
        t = threading.Thread(target=self._execute, args=(tid, command, cwd or str(Path.cwd()), timeout), daemon=True)
        t.start()
        return tid

    def check(self, task_id: str) -> dict | None:
        with self.lock:
            rec = self.tasks.get(task_id)
        return rec if rec else self._load_record(task_id)

    def list_tasks(self) -> list[dict]:
        with self.lock:
            return list(self.tasks.values())

    def drain_notifications(self) -> list[dict]:
        with self.lock:
            results = list(self.notifications)
            self.notifications.clear()
        return results

    def get_output(self, task_id: str, max_chars: int = 50000) -> str:
        rec = self.check(task_id)
        if not rec:
            return f"Task {task_id} not found"
        of = rec.get("output_file", "")
        if not of or not Path(of).exists():
            return "(no output file)"
        try:
            text = Path(of).read_text(encoding="utf-8")
            return text[:max_chars] + (f"\n... (truncated, {len(text)} total chars)" if len(text) > max_chars else "")
        except Exception as e:
            return f"Error reading output: {e}"

    def _execute(self, tid: str, command: str, cwd: str, timeout: int):
        try:
            r = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            output = (r.stdout + r.stderr).strip()
            status = "completed" if r.returncode == 0 else "failed"
            preview = output[:500]
        except subprocess.TimeoutExpired:
            status = "timeout"; output = ""; preview = f"Command timed out after {timeout}s"
        except FileNotFoundError as e:
            status = "failed"; output = str(e); preview = str(e)[:200]
        if output:
            try:
                Path(self.tasks.get(tid, {}).get("output_file", "")).write_text(output, encoding="utf-8")
            except Exception:
                pass
        with self.lock:
            if tid in self.tasks:
                self.tasks[tid]["status"] = status
                self.tasks[tid]["result_preview"] = preview
                self.notifications.append({"type": "background_completed", "task_id": tid, "status": status, "preview": preview})
        if tid in self.tasks:
            self._save_record(self.tasks[tid])

    def _save_record(self, record: dict):
        fp = self.runtime_dir / f"{record['id']}.json"
        try:
            fp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_record(self, tid: str) -> dict | None:
        fp = self.runtime_dir / f"{tid}.json"
        if not fp.exists():
            return None
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _recover(self):
        for fp in sorted(self.runtime_dir.glob("bg_*.json")):
            try:
                rec = json.loads(fp.read_text(encoding="utf-8"))
                if rec.get("status") == "running":
                    rec["status"] = "failed"
                    rec["result_preview"] = "Recovery: process terminated"
                    fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                self.tasks[rec["id"]] = rec
            except (json.JSONDecodeError, OSError):
                continue
