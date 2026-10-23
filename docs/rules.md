# Quarantine Rules Documentation

`clear-my-game` uses configuration rules to determine which files are safe to move into quarantine.

## Configuration Options

- `extensions_media`: List of file extensions that can be quarantined (e.g. video files, audio cutscenes).
- `extensions_ignore`: List of extensions that must never be moved under any circumstances (e.g. `.exe`, `.dll`, `.pak`).
- `min_size_mb`: Minimum file size in megabytes. Files smaller than this threshold are ignored.
- `exclude_dirs`: Directories that the scanner will skip completely.
- `allow_container_move`: Default is false. Even if set to true, clear-my-game will only report container files, not move them.

## Safety Invariants

1. Read-only by default: `scan`, `plan`, and `check` never modify any files in the game directory.
2. The `apply` command runs in dry-run mode by default, showing what would be moved without touching any files. Pass `--yes` to confirm and execute moves.
3. The `apply` command verifies that all files reside strictly inside the game path before performing any move.
4. If anti-cheat software or integrity signature files are detected, quarantine operations are blocked.
5. Moves are reversible: every move records the original path and sha256 checksum in `manifest.json`.
