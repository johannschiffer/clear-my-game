from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

DEFAULT_RULES = {
    "extensions_media": [".mp4", ".bk2", ".bik", ".webm", ".usm", ".wem", ".bnk"],
    "extensions_ignore": [".exe", ".dll", ".so", ".pak", ".assets", ".bundle", ".dat", ".bin"],
    "min_size_mb": 50,
    "exclude_dirs": [".git", "EasyAntiCheat", "BattlEye"],
    "allow_container_move": False,
}


def load_rules(config_path=None):
    rules = dict(DEFAULT_RULES)
    if not config_path:
        return rules

    cfg_file = Path(config_path)
    if not cfg_file.is_file():
        print(f"Warning: config file {config_path} not found, using default rules")
        return rules

    try:
        with open(cfg_file, "rb") as f:
            data = tomllib.load(f)
        for key in rules:
            if key in data:
                rules[key] = data[key]
    except Exception as e:
        print(f"Error parsing {config_path}: {e}")

    # normalize extensions
    rules["extensions_media"] = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in rules["extensions_media"]]
    rules["extensions_ignore"] = [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in rules["extensions_ignore"]]
    return rules
