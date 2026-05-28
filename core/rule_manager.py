import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any


def _load_json_file(path: Path) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def compute_version(data: List[Dict[str, Any]]) -> str:
    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def get_active_rules(rules_path: Path = Path("config/injection_rules.json")):
    data = _load_json_file(rules_path)
    return {
        "path": str(rules_path),
        "version": compute_version(data) if data else "",
        "count": len(data),
        "rules": data,
    }


def get_staged_rules(staging_path: Path = Path("config/injection_rules_staging.json")):
    data = _load_json_file(staging_path)
    return {
        "path": str(staging_path),
        "version": compute_version(data) if data else "",
        "count": len(data),
        "rules": data,
    }


def promote_staged_to_active(staging_path: Path = Path("config/injection_rules_staging.json"),
                            active_path: Path = Path("config/injection_rules.json")) -> bool:
    staged = _load_json_file(staging_path)
    if not staged:
        return False
    try:
        # append staged rules to active, avoiding duplicates by pattern+id
        active = _load_json_file(active_path)
        existing = {(r.get("pattern"), r.get("pattern_id")) for r in active}
        added = 0
        for r in staged:
            key = (r.get("pattern"), r.get("pattern_id"))
            if key in existing:
                continue
            active.append(r)
            added += 1
        with open(active_path, "w", encoding="utf-8") as f:
            json.dump(active, f, indent=2)
        # clear staging
        with open(staging_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return True
    except Exception:
        return False
