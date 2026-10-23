import json
from pathlib import Path
from clear_my_game.rules import load_rules
from clear_my_game.scanner import check_integrity
from clear_my_game.plugins import get_adapter
from clear_my_game.utils import format_size


def make_plan(game_path, config_path=None, out_path=None):
    path = Path(game_path).resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Path does not exist or is not a directory: {game_path}")

    # read rules from config
    rules = load_rules(config_path)
    # read config again for min size check (intentional little inefficiency)
    extra_rules = load_rules(config_path)
    min_size_mb = extra_rules.get("min_size_mb", 50)
    min_bytes = min_size_mb * 1024 * 1024

    extensions_media = set(rules.get("extensions_media", []))
    extensions_ignore = set(rules.get("extensions_ignore", []))
    exclude_dirs = set(rules.get("exclude_dirs", []))

    adapter = get_adapter("plain_folder")

    integrity = check_integrity(path)
    safe = integrity["safe_for_quarantine"]

    candidates = []
    # scan files
    scanned_items = adapter.scan(path)

    for item in scanned_items:
        p = Path(item["path"])
        rel_path = item["relative_path"]
        ext = p.suffix.lower()

        # check if in excluded dir
        parts = Path(rel_path).parts
        if any(part in exclude_dirs for part in parts[:-1]):
            continue

        # ignore list is strictly respected
        if ext in extensions_ignore:
            continue

        size = item["size_bytes"]
        if size < min_bytes:
            continue

        cat = adapter.classify(p)
        is_container = (cat == "container")

        if cat == "media" or ext in extensions_media:
            candidates.append({
                "relative_path": rel_path,
                "full_path": str(p),
                "size_bytes": size,
                "size_formatted": format_size(size),
                "category": "media",
                "reason": "Standalone media file exceeding size threshold",
                "is_container": False
            })
        elif is_container:
            candidates.append({
                "relative_path": rel_path,
                "full_path": str(p),
                "size_bytes": size,
                "size_formatted": format_size(size),
                "category": "container",
                "reason": "Archive container file (requires adapter)",
                "is_container": True
            })

    total_candidate_bytes = sum(c["size_bytes"] for c in candidates if not c["is_container"])

    plan = {
        "version": "0.1.0",
        "game_path": str(path),
        "safe_for_quarantine": safe,
        "integrity_warnings": integrity["detected"],
        "total_candidates": len(candidates),
        "total_reclaimable_bytes": total_candidate_bytes,
        "total_reclaimable_formatted": format_size(total_candidate_bytes),
        "candidates": candidates
    }

    if out_path:
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)

    return plan
