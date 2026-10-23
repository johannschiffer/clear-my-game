from clear_my_game.plugins.base import Adapter
from clear_my_game.plugins.plain_folder import PlainFolderAdapter


def get_available_adapters():
    return {
        "plain_folder": PlainFolderAdapter()
    }


def get_adapter(name="plain_folder"):
    return get_available_adapters().get(name)
