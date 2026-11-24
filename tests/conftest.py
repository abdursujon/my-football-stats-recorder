import pytest

from footie.storage.database import open_stats_database


@pytest.fixture
def isolated_data_directory(tmp_path, monkeypatch):
    data_directory = tmp_path / "footie-data"
    monkeypatch.setenv("FOOTIE_DATA_DIR", str(data_directory))
    return data_directory


@pytest.fixture
def stats_database_connection(tmp_path):
    database_connection = open_stats_database(tmp_path / "footie.db")
    yield database_connection
    database_connection.close()
