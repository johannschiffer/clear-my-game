from pathlib import Path
from clear_my_game.plugins.base import Adapter


class PlainFolderAdapter(Adapter):
    def name(self) -> str:
        return "plain_folder"

    def can_handle(self, game_path: Path) -> bool:
        return Path(game_path).is_dir()

    def scan(self, game_path: Path) -> list[dict]:
        path = Path(game_path)
        items = []
        for p in path.rglob("*"):
            if p.is_file():
                items.append({
                    "path": str(p),
                    "relative_path": str(p.relative_to(path)),
                    "category": self.classify(p),
                    "size_bytes": p.stat().st_size
                })
        return items

    def classify(self, file_path: Path) -> str:
        ext = Path(file_path).suffix.lower()
        if ext in [".mp4", ".bk2", ".bik", ".webm", ".usm", ".wem", ".bnk"]:
            return "media"
        if ext in [".pak", ".assets", ".bundle", ".dat", ".bin"]:
            return "container"
        if ext in [".exe", ".dll", ".so"]:
            return "executable"
        return "other"

    def is_safe_to_move(self, file_path: Path) -> bool:
        return self.classify(file_path) == "media"
