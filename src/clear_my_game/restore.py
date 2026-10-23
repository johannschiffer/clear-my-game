import json
import shutil
from pathlib import Path
from clear_my_game.utils import calculate_sha256


def restore_quarantine(manifest_path, force=False):
    m_path = Path(manifest_path)
    if not m_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(m_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files = manifest.get("files", [])
    restored_count = 0

    # verification pass
    for item in files:
        if item.get("status") != "quarantined":
            continue

        q_path = Path(item["quarantine_path"])
        orig_path = Path(item["original_path"])

        if not q_path.is_file():
            raise FileNotFoundError(f"Quarantined file missing from disk: {q_path}")

        # Check sha256
        current_hash = calculate_sha256(q_path)
        expected_hash = item.get("sha256")
        if current_hash != expected_hash and not force:
            raise ValueError(
                f"Checksum mismatch for {q_path.name}! Expected {expected_hash}, got {current_hash}. Use --force to restore anyway."
            )

        # Check if original directory exists
        if not orig_path.parent.exists() and not force:
            raise FileNotFoundError(
                f"Original directory missing: {orig_path.parent}. Use --force to recreate it and restore."
            )

        # Check if original file is already there
        if orig_path.exists() and not force:
            raise FileExistsError(
                f"File already exists at target location: {orig_path}. Use --force to overwrite."
            )

    # restore pass
    for item in files:
        if item.get("status") != "quarantined":
            continue

        q_path = Path(item["quarantine_path"])
        orig_path = Path(item["original_path"])

        if not orig_path.parent.exists():
            orig_path.parent.mkdir(parents=True, exist_ok=True)

        if orig_path.exists() and force:
            orig_path.unlink()

        shutil.move(str(q_path), str(orig_path))
        restored_count += 1

    print(f"Successfully restored {restored_count} files from quarantine.")
    return {"restored_count": restored_count}
