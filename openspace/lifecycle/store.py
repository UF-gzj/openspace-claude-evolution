from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
import tempfile
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
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except JSONDecodeError:
            # Preserve the broken snapshot for inspection, but do not let a
            # transient partial write take down dashboard reads.
            broken_path = self._path.with_name(f"{self._path.stem}.broken.json")
            try:
                if not broken_path.exists():
                    self._path.replace(broken_path)
                else:
                    self._path.unlink(missing_ok=True)
            except OSError:
                return {}
            return {}
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
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._root,
            prefix=f"{self._path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            temp_path = Path(handle.name)
        temp_path.replace(self._path)

    def get(self, subject_id: str) -> Optional[LifecycleEntry]:
        return self.load_all().get(subject_id)

    def upsert(self, entry: LifecycleEntry) -> None:
        entries = self.load_all()
        entries[entry.subject_id] = entry
        self.save_all(entries)

    def list_entries(self) -> List[LifecycleEntry]:
        return list(self.load_all().values())
