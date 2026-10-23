import tempfile
from pathlib import Path
from clear_my_game.scanner import scan_game, check_integrity


def test_scan_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # create some dummy files
        (tmp_path / "game.exe").write_bytes(b"MZ" + b"\x00" * 1024)
        (tmp_path / "intro.mp4").write_bytes(b"\x00" * (60 * 1024 * 1024))
        (tmp_path / "data.pak").write_bytes(b"\x00" * 2048)

        results = scan_game(tmp_path)
        assert results["total_files"] == 3
        assert ".mp4" in results["by_extension"]
        assert ".exe" in results["by_extension"]
        assert ".pak" in results["by_extension"]
        assert len(results["large_files"]) == 1
        assert results["large_files"][0]["relative_path"] == "intro.mp4"
        assert results["integrity"]["safe_for_quarantine"] is True


def test_check_integrity():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # fake anti-cheat dll
        (tmp_path / "EasyAntiCheat_x64.dll").write_bytes(b"dummy")
        res = check_integrity(tmp_path)
        assert res["safe_for_quarantine"] is False
        assert len(res["detected"]) > 0
