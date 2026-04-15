from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .types import LifecycleEntry


class LifecycleStore:
    """Sidecar JSON store for deprecation governance.

    This store is intentionally separated from OpenSpace's native SQLite skill
    ledger so deprecation experiments cannot corrupt the original evolution
    pipeline.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._path = self._root / "lifecycle.json"

    @property
    def path(self) -> Path:
        return self._path

    def load_all(self) -> Dict[str, LifecycleEntry]:
        if not self._path.is_file():
            return {}
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return {
            key: LifecycleEntry.from_dict(value)
            for key, value in data.get("entries", {}).items()
        }

    def save_all(self, entries: Dict[str, LifecycleEntry]) -> None:
        payload = {
            "entries": {
                key: value.to_dict()
                for key, value in sorted(entries.items(), key=lambda item: item[0])
            }
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get(self, subject_id: str) -> Optional[LifecycleEntry]:
        return self.load_all().get(subject_id)

    def upsert(self, entry: LifecycleEntry) -> None:
        entries = self.load_all()
        entries[entry.subject_id] = entry
        self.save_all(entries)

    def list_entries(self) -> List[LifecycleEntry]:
        return list(self.load_all().values())
