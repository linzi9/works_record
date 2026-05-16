"""TaskManager -- persistent task system with dependency tracking."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class TaskRecord:
    id: str = ""
    subject: str = ""
    description: str = ""
    status: str = "pending"  # pending | in_progress | completed | deleted
    blocked_by: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    owner: str = ""


def is_ready(task: TaskRecord, all_tasks: dict) -> bool:
    if task.status != "pending":
        return False
    for bid in task.blocked_by:
        blocker = all_tasks.get(bid)
        if blocker and blocker.status != "completed":
            return False
    return True


class TaskManager:
    """One task = one JSON file in tasks_dir."""

    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create(self, subject: str, description: str = "",
               blocked_by: list = None, owner: str = "") -> TaskRecord:
        tid = f"task_{self._next_id()}"
        record = TaskRecord(
            id=tid, subject=subject, description=description,
            status="pending", blocked_by=blocked_by or [],
            blocks=[], owner=owner,
        )
        for dep_id in record.blocked_by:
            dep = self.get(dep_id)
            if dep and tid not in dep.blocks:
                dep.blocks.append(tid)
                self._save(dep)
            elif dep is None:
                record.blocked_by.remove(dep_id)
        self._save(record)
        return record

    def get(self, task_id: str) -> TaskRecord | None:
        fp = self._path(task_id)
        if not fp.exists():
            return None
        try:
            return TaskRecord(**json.loads(fp.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, TypeError):
            return None

    def update(self, task_id: str, **kwargs) -> TaskRecord | None:
        task = self.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        self._save(task)
        return task

    def complete(self, task_id: str) -> TaskRecord | None:
        task = self.get(task_id)
        if not task:
            return None
        task.status = "completed"
        for t in self.list_all():
            if task_id in t.blocked_by:
                t.blocked_by.remove(task_id)
                self._save(t)
        self._save(task)
        return task

    def delete(self, task_id: str) -> bool:
        fp = self._path(task_id)
        if not fp.exists():
            return False
        fp.unlink()
        for t in self.list_all():
            changed = False
            if task_id in t.blocked_by:
                t.blocked_by.remove(task_id); changed = True
            if task_id in t.blocks:
                t.blocks.remove(task_id); changed = True
            if changed:
                self._save(t)
        return True

    def list_all(self) -> list[TaskRecord]:
        tasks = []
        for fp in sorted(self.tasks_dir.glob("task_*.json")):
            try:
                tasks.append(TaskRecord(**json.loads(fp.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, TypeError):
                continue
        return tasks

    def ready_tasks(self) -> list[TaskRecord]:
        all_t = {t.id: t for t in self.list_all()}
        return [t for t in all_t.values() if is_ready(t, all_t)]

    def blocked_tasks(self) -> list[TaskRecord]:
        all_t = {t.id: t for t in self.list_all()}
        return [t for t in all_t.values() if t.status == "pending" and not is_ready(t, all_t)]

    def _path(self, task_id: str) -> Path:
        return self.tasks_dir / f"{task_id}.json"

    def _next_id(self) -> int:
        ids = []
        for fp in self.tasks_dir.glob("task_*.json"):
            try:
                ids.append(int(fp.stem.split("_")[1]))
            except (IndexError, ValueError):
                continue
        return max(ids) + 1 if ids else 1

    def _save(self, task: TaskRecord):
        fp = self._path(task.id)
        fp.write_text(json.dumps(asdict(task), ensure_ascii=False, indent=2), encoding="utf-8")
