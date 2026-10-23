import json
import shutil
import time
from pathlib import Path
from clear_my_game.scanner import check_integrity
from clear_my_game.rules import load_rules
from clear_my_game.utils import calculate_sha256, format_size


def apply_quarantine(plan_path, quarantine_dir, yes=False):
    p_path = Path(plan_path)
    if not p_path.is_file():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")

    with open(p_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    game_path = Path(plan.get("game_path", "")).resolve()
    if not game_path.is_dir():
        raise ValueError(f"Invalid game path in plan: {game_path}")

    # Security rule 1: Refuse if integrity check failed
    if not plan.get("safe_for_quarantine", True):
        raise RuntimeError("Refusing to apply plan: Game has anti-cheat or integrity files.")

    # Re-check integrity of game_path just in case
    live_integrity = check_integrity(game_path)
    if not live_integrity["safe_for_quarantine"]:
        raise RuntimeError("Refusing to apply plan: Live check detected anti-cheat or integrity files.")

    rules = load_rules()
    ignore_exts = set(rules.get("extensions_ignore", []))

    q_dir = Path(quarantine_dir).resolve()
    if yes:
        q_dir.mkdir(parents=True, exist_ok=True)

    candidates = plan.get("candidates", [])

    # First pass: validation
    for cand in candidates:
        rel_path = cand["relative_path"]
        orig_file = (game_path / rel_path).resolve()

        # Security rule 2: Refuse paths outside game_path
        try:
            orig_file.relative_to(game_path)
        except ValueError:
            raise ValueError(f"Security violation: path escapes game directory: {rel_path}")

        # Security rule 3: Refuse ignored extensions
        ext = orig_file.suffix.lower()
        if ext in ignore_exts:
            raise ValueError(f"Security violation: attempt to quarantine ignored extension {ext}: {rel_path}")

        # Destination collision check
        dest_file = q_dir / rel_path
        if not cand.get("is_container", False) and dest_file.exists():
            raise FileExistsError(f"Target already exists in quarantine: {dest_file}")

    if not yes:
        # Dry-run by default
        movable = [c for c in candidates if not c.get("is_container", False)]
        total_bytes = sum(c.get("size_bytes", 0) for c in movable)
        print("=== DRY RUN (use --yes to execute) ===")
        print(f"Quarantine destination: {q_dir}")
        print(f"Candidates to move ({len(movable)} files, {format_size(total_bytes)}):")
        for c in movable:
            dest_file = q_dir / c["relative_path"]
            print(f"  - {c['relative_path']} ({c.get('size_formatted', format_size(c.get('size_bytes', 0)))}) -> {dest_file}")
        containers = [c for c in candidates if c.get("is_container", False)]
        if containers:
            print(f"Containers skipped (requires adapter) ({len(containers)} files):")
            for c in containers:
                print(f"  - {c['relative_path']}")
        print("No files were moved. Run with --yes to execute quarantine.")
        return {"dry_run": True, "count": len(movable), "reclaimable_bytes": total_bytes}

    # Second pass: apply moves
    manifest_records = []
    moved_count = 0

    for cand in candidates:
        rel_path = cand["relative_path"]
        orig_file = (game_path / rel_path).resolve()
        is_container = cand.get("is_container", False)

        if is_container:
            # Containers are never moved in base version
            manifest_records.append({
                "relative_path": rel_path,
                "original_path": str(orig_file),
                "quarantine_path": None,
                "sha256": None,
                "size_bytes": cand.get("size_bytes", 0),
                "status": "requires_adapter",
                "reason": "Container archive requires adapter"
            })
            continue

        if not orig_file.is_file():
            print(f"Warning: candidate file missing on disk: {orig_file}")
            continue

        file_hash = calculate_sha256(orig_file)
        dest_file = q_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(orig_file), str(dest_file))
        moved_count += 1

        manifest_records.append({
            "relative_path": rel_path,
            "original_path": str(orig_file),
            "quarantine_path": str(dest_file),
            "sha256": file_hash,
            "size_bytes": cand.get("size_bytes", 0),
            "status": "quarantined"
        })

    manifest = {
        "version": "0.1.0",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "game_path": str(game_path),
        "quarantine_dir": str(q_dir),
        "total_quarantined": moved_count,
        "files": manifest_records
    }

    manifest_file = q_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Moved {moved_count} files to quarantine at {q_dir}")
    print(f"Manifest saved to {manifest_file}")
    return manifest
