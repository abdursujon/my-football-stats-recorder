from pathlib import Path

from footie.storage.data_paths import (
    resolve_database_file_path,
    resolve_user_data_directory,
)


def test_linux_uses_local_share_by_default():
    assert resolve_user_data_directory("Linux", "/home/player", {}) == Path(
        "/home/player/.local/share/footie"
    )


def test_linux_respects_xdg_data_home():
    assert resolve_user_data_directory(
        "Linux", "/home/player", {"XDG_DATA_HOME": "/data"}
    ) == Path("/data/footie")


def test_mac_uses_application_support():
    assert resolve_user_data_directory("Darwin", "/Users/player", {}) == Path(
        "/Users/player/Library/Application Support/footie"
    )


def test_windows_uses_appdata():
    assert resolve_user_data_directory(
        "Windows", "C:/Users/player", {"APPDATA": "C:/Roaming"}
    ) == Path("C:/Roaming/footie")


def test_override_variable_wins_over_platform():
    assert resolve_user_data_directory(
        "Linux", "/home/player", {"FOOTIE_DATA_DIR": "/custom"}
    ) == Path("/custom")


def test_database_file_lives_in_data_directory():
    assert resolve_database_file_path("Linux", "/home/player", {}) == Path(
        "/home/player/.local/share/footie/footie.db"
    )
