from pathlib import Path


class Adapter:
    """
    Base adapter contract.
    Adapters are strictly read-only tools to classify files in a game folder.
    An adapter cannot sign, repack, or touch game executables or files.
    """

    def name(self) -> str:
        raise NotImplementedError

    def can_handle(self, game_path: Path) -> bool:
        raise NotImplementedError

    def scan(self, game_path: Path) -> list[dict]:
        raise NotImplementedError

    def classify(self, file_path: Path) -> str:
        raise NotImplementedError

    def is_safe_to_move(self, file_path: Path) -> bool:
        raise NotImplementedError
