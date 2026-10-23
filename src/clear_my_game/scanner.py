import os
from pathlib import Path
from clear_my_game.rules import load_rules
from clear_my_game.utils import format_size

CONTAINER_EXTENSIONS = {".pak", ".assets", ".usm", ".mp4", ".bk2", ".bik", ".webm", ".wem", ".bnk"}
INTEGRITY_EXTENSIONS = {".sig", ".sha256", ".md5"}
ANTI_CHEAT_KEYWORDS = ["easyanticheat", "battleye", "beservice", "bedaisy", "vanguard", "anticheat"]


def check_integrity(game_path: Path):
    path = Path(game_path)
    if not path.exists():
        return {"safe_for_quarantine": False, "detected": ["Path does not exist"]}

    detected = []
    # scan for integrity signatures or anti-cheat references
    for root, dirs, files in os.walk(path):
        # check folder names
        for d in dirs:
            dl = d.lower()
            for kw in ANTI_CHEAT_KEYWORDS:
                if kw in dl:
                    detected.append(f"Anti-cheat directory: {os.path.relpath(os.path.join(root, d), path)}")
                    break

        # check file names and extensions
        for f in files:
            fl = f.lower()
            p = Path(f)
            if p.suffix.lower() in INTEGRITY_EXTENSIONS:
                detected.append(f"Integrity signature file: {os.path.relpath(os.path.join(root, f), path)}")
            for kw in ANTI_CHEAT_KEYWORDS:
                if kw in fl:
                    detected.append(f"Anti-cheat file: {os.path.relpath(os.path.join(root, f), path)}")
                    break

    return {
        "safe_for_quarantine": len(detected) == 0,
        "detected": detected
    }


def scan_game(game_path, config_path=None):
    path = Path(game_path).resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Directory not found: {game_path}")

    rules = load_rules(config_path)
    min_bytes = rules.get("min_size_mb", 50) * 1024 * 1024
    exclude_dirs = set(rules.get("exclude_dirs", []))

    total_files = 0
    total_size = 0
    by_ext = {}
    containers = []
    large_candidates = []

    for root, dirs, files in os.walk(path):
        # filter out excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file_name in files:
            file_path = Path(root) / file_name
            try:
                st = file_path.stat()
                size = st.st_size
            except OSError:
                continue

            total_files += 1
            total_size += size
            ext = file_path.suffix.lower() or "no_extension"

            if ext not in by_ext:
                by_ext[ext] = {"count": 0, "size_bytes": 0}
            by_ext[ext]["count"] += 1
            by_ext[ext]["size_bytes"] += size

            rel_str = str(file_path.relative_to(path))

            if ext in CONTAINER_EXTENSIONS:
                containers.append({
                    "relative_path": rel_str,
                    "extension": ext,
                    "size_bytes": size,
                    "size_formatted": format_size(size)
                })

            if size >= min_bytes:
                large_candidates.append({
                    "relative_path": rel_str,
                    "extension": ext,
                    "size_bytes": size,
                    "size_formatted": format_size(size)
                })

    integrity_check = check_integrity(path)

    return {
        "game_path": str(path),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_formatted": format_size(total_size),
        "by_extension": by_ext,
        "containers": containers,
        "large_files": large_candidates,
        "integrity": integrity_check
    }
