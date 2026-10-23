import json
import tempfile
from pathlib import Path
import pytest
from clear_my_game.planner import make_plan
from clear_my_game.quarantine import apply_quarantine
from clear_my_game.restore import restore_quarantine


def test_quarantine_and_restore():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        game_dir = root / "fake_game"
        game_dir.mkdir()
        q_dir = root / "quarantine"

        # files
        video = game_dir / "cutscene.mp4"
        video.write_bytes(b"VIDEO" * 12 * 1024 * 1024)  # ~60MB
        exe = game_dir / "game.exe"
        exe.write_bytes(b"EXECUTABLE")

        plan_file = root / "plan.json"
        plan = make_plan(game_dir, out_path=plan_file)
        assert plan["total_candidates"] == 1
        assert plan["candidates"][0]["relative_path"] == "cutscene.mp4"

        # apply
        manifest = apply_quarantine(plan_file, q_dir, yes=True)
        assert not video.exists()
        assert exe.exists()
        assert (q_dir / "cutscene.mp4").exists()
        assert (q_dir / "manifest.json").exists()
        assert len(manifest["files"]) == 1
        assert manifest["files"][0]["sha256"] is not None

        # restore
        restore_quarantine(q_dir / "manifest.json")
        assert video.exists()
        assert not (q_dir / "cutscene.mp4").exists()


def test_apply_dry_run_by_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        game_dir = root / "fake_game"
        game_dir.mkdir()
        q_dir = root / "quarantine"

        video = game_dir / "intro.mp4"
        video.write_bytes(b"VIDEO" * 12 * 1024 * 1024)

        plan_file = root / "plan.json"
        make_plan(game_dir, out_path=plan_file)

        # apply without yes flag (dry run by default)
        res = apply_quarantine(plan_file, q_dir, yes=False)
        assert res.get("dry_run") is True
        assert video.exists()
        assert not (q_dir / "intro.mp4").exists()
        assert not (q_dir / "manifest.json").exists()


def test_apply_security_checks():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        game_dir = root / "fake_game"
        game_dir.mkdir()
        q_dir = root / "quarantine"

        exe = game_dir / "game.exe"
        exe.write_bytes(b"EXE")

        # fake plan trying to move game.exe
        bad_plan = {
            "game_path": str(game_dir),
            "safe_for_quarantine": True,
            "candidates": [
                {
                    "relative_path": "game.exe",
                    "full_path": str(exe),
                    "size_bytes": 100,
                    "category": "executable",
                    "reason": "Test bad plan",
                    "is_container": False
                }
            ]
        }
        plan_file = root / "bad_plan.json"
        with open(plan_file, "w") as f:
            json.dump(bad_plan, f)

        with pytest.raises(ValueError, match="Security violation"):
            apply_quarantine(plan_file, q_dir)
