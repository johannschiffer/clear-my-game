# clear-my-game

A simple CLI utility to audit game directories and reclaim disk space by safely quarantining non-essential media files (like intro movies or cutscenes). It allows restoring everything back with a single command.

Works on Linux, Windows 10/11, and Steam Proton setups.

## What it does NOT do

This tool is strictly read-only and non-destructive:
- It never touches game executables or libraries (.exe, .dll, .so).
- It never interacts with anti-cheat software.
- It never modifies, unpacks, or edits archive files (.pak, .assets).
- It only operates on standalone files located directly in the game folder.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/johannschiffer/clear-my-game.git
cd clear-my-game
pip install .
```

## Quick Start

Scan a game directory to check space usage:
```bash
clear-my-game scan --path /path/to/game
```

Check if the directory contains anti-cheat or integrity files:
```bash
clear-my-game check --path /path/to/game
```

Generate a quarantine plan using configuration:
```bash
clear-my-game plan --path /path/to/game --config config.example.toml --out plan.json
```

Preview moves without touching files (dry-run by default):
```bash
clear-my-game apply --plan plan.json --quarantine-dir /path/to/quarantine
```

Execute moves to quarantine:
```bash
clear-my-game apply --plan plan.json --quarantine-dir /path/to/quarantine --yes
```

Restore all quarantined files back to their original locations:
```bash
clear-my-game restore --manifest /path/to/quarantine/manifest.json
```

## Adding Adapters

The tool supports adapters to recognize different layouts. To add one, inherit from `Adapter` in `src/clear_my_game/plugins/base.py` and implement the required methods. Adapters are strictly read-only and must never modify game files.
