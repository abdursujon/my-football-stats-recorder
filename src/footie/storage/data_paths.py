import os
import platform
from pathlib import Path

APPLICATION_DIRECTORY_NAME = "footie"
DATABASE_FILE_NAME = "footie.db"
DATA_DIRECTORY_OVERRIDE_VARIABLE = "FOOTIE_DATA_DIR"


def resolve_user_data_directory(operating_system_name=None, home_directory=None, environment=None):
    environment = os.environ if environment is None else environment
    overridden_data_directory = environment.get(DATA_DIRECTORY_OVERRIDE_VARIABLE)
    if overridden_data_directory:
        return Path(overridden_data_directory)

    operating_system_name = operating_system_name or platform.system()
    home_directory = Path(home_directory) if home_directory else Path.home()

    if operating_system_name == "Windows":
        roaming_application_data = environment.get("APPDATA")
        base_directory = (
            Path(roaming_application_data) if roaming_application_data
            else home_directory / "AppData" / "Roaming"
        )
    elif operating_system_name == "Darwin":
        base_directory = home_directory / "Library" / "Application Support"
    else:
        xdg_data_home = environment.get("XDG_DATA_HOME")
        base_directory = Path(xdg_data_home) if xdg_data_home else home_directory / ".local" / "share"

    return base_directory / APPLICATION_DIRECTORY_NAME


def resolve_database_file_path(operating_system_name=None, home_directory=None, environment=None):
    return resolve_user_data_directory(operating_system_name, home_directory, environment) / DATABASE_FILE_NAME
