from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


class ConfigRegistry:
    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir

    def _read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def get_workflows(self) -> dict[str, dict[str, Any]]:
        workflows: dict[str, dict[str, Any]] = {}
        wf_dir = self.config_dir / "workflows"
        for file in sorted(wf_dir.glob("*.json")):
            workflows[file.stem] = self._read_json(file)
        return workflows

    def get_workflow(self, process: str) -> dict[str, Any] | None:
        path = self.config_dir / "workflows" / f"{process}.json"
        if not path.exists():
            return None
        return self._read_json(path)

    def get_business_rules(self) -> dict[str, Any]:
        return self._read_json(self.config_dir / "rules" / "business_rules.json")

    def get_sla_profiles(self) -> dict[str, Any]:
        return self._read_json(self.config_dir / "sla_profiles.json")

    def get_doa_matrix(self) -> dict[str, Any]:
        return self._read_json(self.config_dir / "security" / "doa_matrix.json")

    def get_sod_matrix(self) -> dict[str, Any]:
        return self._read_json(self.config_dir / "security" / "sod_matrix.json")


@lru_cache
def get_registry() -> ConfigRegistry:
    return ConfigRegistry(settings.config_dir)
