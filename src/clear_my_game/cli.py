import argparse
import json
import sys
from pathlib import Path

from clear_my_game.scanner import scan_game, check_integrity
from clear_my_game.planner import make_plan
from clear_my_game.quarantine import apply_quarantine
from clear_my_game.restore import restore_quarantine
from clear_my_game.plugins import get_available_adapters
from clear_my_game.utils import format_size


def build_parser():
    parser = argparse.ArgumentParser(
        prog="clear-my-game",
        description="Audit game folders and safely quarantine non-essential files"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan a game directory for files and space usage")
    p_scan.add_argument("--path", required=True, help="Path to the installed game directory")
    p_scan.add_argument("--config", help="Path to config.toml file")
    p_scan.add_argument("--json", dest="json_out", help="Save scan results to a JSON file")

    # plan
    p_plan = subparsers.add_parser("plan", help="Generate a quarantine plan")
    p_plan.add_argument("--path", required=True, help="Path to the installed game directory")
    p_plan.add_argument("--config", help="Path to config.toml file")
    p_plan.add_argument("--out", default="plan.json", help="Path to output plan JSON (default: plan.json)")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply a quarantine plan by moving candidate files")
    p_apply.add_argument("--plan", required=True, help="Path to plan JSON file")
    p_apply.add_argument("--quarantine-dir", required=True, help="Target quarantine directory")
    p_apply.add_argument("--yes", action="store_true", help="Execute quarantine moves (default is dry-run)")

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore quarantined files to original paths")
    p_restore.add_argument("--manifest", required=True, help="Path to quarantine manifest.json")
    p_restore.add_argument("--force", action="store_true", help="Force restore despite missing folders or hash mismatches")

    # plugins
    p_plugins = subparsers.add_parser("plugins", help="Manage plugins and adapters")
    p_plugins_sub = p_plugins.add_subparsers(dest="subcommand", help="Plugin action")
    p_plugins_sub.add_parser("list", help="List available adapters")

    # check
    p_check = subparsers.add_parser("check", help="Check directory for anti-cheat or integrity signatures")
    p_check.add_argument("--path", required=True, help="Path to game directory")

    return parser


def handle_scan(args):
    game_path = Path(args.path)
    if not game_path.is_dir():
        print(f"Error: Game path not found: {args.path}")
        return 1

    print(f"Scanning directory: {game_path} ...")
    results = scan_game(game_path, args.config)

    print("\n--- Scan Summary ---")
    print(f"Game Path: {results['game_path']}")
    print(f"Total Files: {results['total_files']}")
    print(f"Total Size: {results['total_size_formatted']}")

    print("\nTop file types by size:")
    sorted_exts = sorted(results["by_extension"].items(), key=lambda x: x[1]["size_bytes"], reverse=True)
    for ext, data in sorted_exts[:10]:
        print(f"  {ext:<15} {data['count']:<6} files ({format_size(data['size_bytes'])})")

    if results["containers"]:
        print(f"\nDetected Container / Archive files ({len(results['containers'])}):")
        for c in results["containers"][:10]:
            print(f"  {c['relative_path']} ({c['size_formatted']})")
        if len(results["containers"]) > 10:
            print(f"  ... and {len(results['containers']) - 10} more.")

    if not results["integrity"]["safe_for_quarantine"]:
        print("\n[WARNING] Integrity / Anti-cheat signatures detected:")
        for det in results["integrity"]["detected"]:
            print(f"  - {det}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nFull scan saved to {args.json_out}")

    return 0


def handle_plan(args):
    try:
        plan = make_plan(args.path, args.config, args.out)
    except Exception as e:
        print(f"Error creating plan: {e}")
        return 1

    print(f"Plan created successfully: {args.out}")
    print(f"Safe for quarantine: {plan['safe_for_quarantine']}")
    if not plan["safe_for_quarantine"]:
        print("Warnings detected:")
        for w in plan["integrity_warnings"]:
            print(f"  - {w}")

    print(f"Candidates found: {plan['total_candidates']}")
    print(f"Reclaimable space: {plan['total_reclaimable_formatted']}")
    for c in plan["candidates"]:
        print(f"  [{c['category']}] {c['relative_path']} ({c['size_formatted']}) - {c['reason']}")

    return 0


def handle_apply(args):
    try:
        apply_quarantine(args.plan, args.quarantine_dir, yes=args.yes)
    except Exception as e:
        print(f"Error during apply: {e}")
        return 1
    return 0


def handle_restore(args):
    try:
        restore_quarantine(args.manifest, force=args.force)
    except Exception as e:
        print(f"Error restoring files: {e}")
        return 1
    return 0


def handle_plugins(args):
    if args.subcommand == "list" or not args.subcommand:
        adapters = get_available_adapters()
        print("Available adapters:")
        for name, ad in adapters.items():
            print(f"  - {name}: {ad.__class__.__name__}")
        return 0
    print("Unknown plugins command. Use: clear-my-game plugins list")
    return 1


def handle_check(args):
    game_path = Path(args.path)
    res = check_integrity(game_path)
    if res["safe_for_quarantine"]:
        print(f"Check passed for {game_path}: No anti-cheat or integrity signatures found.")
        return 0
    else:
        print(f"Check failed for {game_path}: Game is NOT suitable for quarantine.")
        for item in res["detected"]:
            print(f"  - {item}")
        return 1


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "scan":
        return handle_scan(args)
    elif args.command == "plan":
        return handle_plan(args)
    elif args.command == "apply":
        return handle_apply(args)
    elif args.command == "restore":
        return handle_restore(args)
    elif args.command == "plugins":
        return handle_plugins(args)
    elif args.command == "check":
        return handle_check(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
