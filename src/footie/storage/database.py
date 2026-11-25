import sqlite3
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

MATCHES_AND_SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    match_date TEXT    NOT NULL,
    venue      TEXT    NOT NULL DEFAULT '',
    goals      INTEGER NOT NULL CHECK (goals >= 0),
    assists    INTEGER NOT NULL CHECK (assists >= 0)
);
CREATE INDEX IF NOT EXISTS matches_by_date ON matches (match_date);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

SETTING_PROFILE_URL = "profile_url"
SETTING_STATS_README_PATH = "stats_readme_path"
SETTING_GIT_PUBLISHING = "git_publishing"
SETTING_SCHEDULE_BACKEND = "schedule_backend"
SETTING_SCHEDULE_TIME = "schedule_time"


@dataclass(frozen=True)
class MatchRecord:
    match_date: date
    venue: str
    goals: int
    assists: int
    match_id: Optional[int] = field(default=None, compare=False)


@dataclass(frozen=True)
class CareerTotals:
    matches_played: int
    goals: int
    assists: int


def read_matches_table_column_names(database_connection):
    return [
        column_row[1]
        for column_row in database_connection.execute(
            "PRAGMA table_info(matches)"
        ).fetchall()
    ]


def migrate_one_match_per_date_table_to_match_id_table(database_connection):
    existing_column_names = read_matches_table_column_names(database_connection)
    if not existing_column_names or "match_id" in existing_column_names:
        return
    with database_connection:
        database_connection.execute(
            "ALTER TABLE matches RENAME TO matches_one_per_date"
        )
        database_connection.executescript(MATCHES_AND_SETTINGS_SCHEMA)
        database_connection.execute(
            "INSERT INTO matches (match_date, venue, goals, assists) "
            "SELECT match_date, venue, goals, assists FROM matches_one_per_date ORDER BY match_date"
        )
        database_connection.execute("DROP TABLE matches_one_per_date")


def open_stats_database(database_file_path):
    database_file_path.parent.mkdir(parents=True, exist_ok=True)
    database_connection = sqlite3.connect(database_file_path)
    migrate_one_match_per_date_table_to_match_id_table(database_connection)
    database_connection.executescript(MATCHES_AND_SETTINGS_SCHEMA)
    return database_connection


def insert_match_record(database_connection, match_record):
    with database_connection:
        inserted_row_cursor = database_connection.execute(
            "INSERT INTO matches (match_date, venue, goals, assists) VALUES (?, ?, ?, ?)",
            (
                match_record.match_date.isoformat(),
                match_record.venue,
                match_record.goals,
                match_record.assists,
            ),
        )
    return inserted_row_cursor.lastrowid


def convert_row_to_match_record(match_row):
    match_id, match_date_text, venue, goals, assists = match_row
    return MatchRecord(
        date.fromisoformat(match_date_text), venue, goals, assists, match_id
    )


def fetch_match_record_by_id(database_connection, match_id):
    match_row = database_connection.execute(
        "SELECT match_id, match_date, venue, goals, assists FROM matches WHERE match_id = ?",
        (match_id,),
    ).fetchone()
    return convert_row_to_match_record(match_row) if match_row else None


def delete_match_record_by_id(database_connection, match_id):
    with database_connection:
        deleted_rows_cursor = database_connection.execute(
            "DELETE FROM matches WHERE match_id = ?", (match_id,)
        )
    return deleted_rows_cursor.rowcount > 0


def has_match_record_for_date(database_connection, match_date):
    matching_row = database_connection.execute(
        "SELECT 1 FROM matches WHERE match_date = ?", (match_date.isoformat(),)
    ).fetchone()
    return matching_row is not None


def has_identical_match_record(database_connection, match_record):
    matching_row = database_connection.execute(
        "SELECT 1 FROM matches WHERE match_date = ? AND venue = ? AND goals = ? AND assists = ?",
        (
            match_record.match_date.isoformat(),
            match_record.venue,
            match_record.goals,
            match_record.assists,
        ),
    ).fetchone()
    return matching_row is not None


def fetch_all_match_records_ordered_by_date(database_connection):
    stored_rows = database_connection.execute(
        "SELECT match_id, match_date, venue, goals, assists FROM matches ORDER BY match_date, match_id"
    ).fetchall()
    return [convert_row_to_match_record(match_row) for match_row in stored_rows]


def fetch_known_venues_ordered_by_frequency(database_connection):
    venue_rows = database_connection.execute(
        "SELECT venue FROM matches WHERE venue != '' "
        "GROUP BY venue ORDER BY COUNT(*) DESC, MAX(match_date) DESC"
    ).fetchall()
    return [venue for (venue,) in venue_rows]


def fetch_most_recent_venue(database_connection):
    most_recent_venue_row = database_connection.execute(
        "SELECT venue FROM matches WHERE venue != '' ORDER BY match_date DESC, match_id DESC LIMIT 1"
    ).fetchone()
    return most_recent_venue_row[0] if most_recent_venue_row else None


def calculate_career_totals_from_records(match_records):
    return CareerTotals(
        matches_played=len(match_records),
        goals=sum(match_record.goals for match_record in match_records),
        assists=sum(match_record.assists for match_record in match_records),
    )


def read_setting_value(database_connection, setting_key, default_value=None):
    setting_row = database_connection.execute(
        "SELECT value FROM settings WHERE key = ?", (setting_key,)
    ).fetchone()
    return setting_row[0] if setting_row else default_value


def write_setting_value(database_connection, setting_key, setting_value):
    with database_connection:
        database_connection.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (setting_key, setting_value),
        )


def delete_setting_value(database_connection, setting_key):
    with database_connection:
        database_connection.execute(
            "DELETE FROM settings WHERE key = ?", (setting_key,)
        )
