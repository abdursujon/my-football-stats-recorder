from datetime import date

import sqlite3

from footie.storage.database import (
    MatchRecord,
    calculate_career_totals_from_records,
    delete_match_record_by_id,
    fetch_all_match_records_ordered_by_date,
    fetch_match_record_by_id,
    has_identical_match_record,
    fetch_known_venues_ordered_by_frequency,
    fetch_most_recent_venue,
    has_match_record_for_date,
    insert_match_record,
    open_stats_database,
    read_setting_value,
    write_setting_value,
)


def test_new_database_starts_with_zero_matches_and_no_settings(tmp_path):
    database_connection = open_stats_database(tmp_path / "nested" / "footie.db")
    assert fetch_all_match_records_ordered_by_date(database_connection) == []
    assert read_setting_value(database_connection, "profile_url") is None
    database_connection.close()


def test_records_are_returned_in_date_order(stats_database_connection):
    later_match = MatchRecord(date(2026, 11, 23), "Ordsall Leisure Centre", 3, 0)
    earlier_match = MatchRecord(date(2026, 9, 13), "Platt Lane (ManCity Academy)", 1, 1)
    insert_match_record(stats_database_connection, later_match)
    insert_match_record(stats_database_connection, earlier_match)
    assert fetch_all_match_records_ordered_by_date(stats_database_connection) == [earlier_match, later_match]


def test_several_matches_on_same_date_are_kept_in_entry_order(stats_database_connection):
    match_date = date(2026, 11, 23)
    first_match = MatchRecord(match_date, "Ordsall Leisure Centre", 1, 0)
    second_match = MatchRecord(match_date, "Oasis Academy Media City", 2, 1)
    insert_match_record(stats_database_connection, first_match)
    insert_match_record(stats_database_connection, second_match)
    assert fetch_all_match_records_ordered_by_date(stats_database_connection) == [first_match, second_match]


def test_fetch_and_delete_match_by_id(stats_database_connection):
    match_date = date(2026, 11, 23)
    assert not has_match_record_for_date(stats_database_connection, match_date)
    match_id = insert_match_record(stats_database_connection, MatchRecord(match_date, "A", 0, 0))
    assert has_match_record_for_date(stats_database_connection, match_date)
    assert fetch_match_record_by_id(stats_database_connection, match_id).match_id == match_id
    assert delete_match_record_by_id(stats_database_connection, match_id)
    assert not delete_match_record_by_id(stats_database_connection, match_id)
    assert fetch_match_record_by_id(stats_database_connection, match_id) is None


def test_identical_match_detection_compares_every_field(stats_database_connection):
    insert_match_record(stats_database_connection, MatchRecord(date(2026, 11, 23), "A", 1, 0))
    assert has_identical_match_record(stats_database_connection, MatchRecord(date(2026, 11, 23), "A", 1, 0))
    assert not has_identical_match_record(stats_database_connection, MatchRecord(date(2026, 11, 23), "A", 2, 0))


def test_one_match_per_date_database_is_migrated_without_losing_rows(tmp_path):
    database_file_path = tmp_path / "footie.db"
    legacy_connection = sqlite3.connect(database_file_path)
    legacy_connection.executescript(
        "CREATE TABLE matches (match_date TEXT PRIMARY KEY, venue TEXT NOT NULL DEFAULT '', "
        "goals INTEGER NOT NULL, assists INTEGER NOT NULL);"
        "INSERT INTO matches VALUES ('2026-11-23', 'Ordsall', 3, 0), ('2026-08-11', 'Powerleague', 0, 0);"
    )
    legacy_connection.commit()
    legacy_connection.close()

    database_connection = open_stats_database(database_file_path)
    insert_match_record(database_connection, MatchRecord(date(2026, 11, 23), "Oasis", 1, 1))
    assert fetch_all_match_records_ordered_by_date(database_connection) == [
        MatchRecord(date(2026, 8, 11), "Powerleague", 0, 0),
        MatchRecord(date(2026, 11, 23), "Ordsall", 3, 0),
        MatchRecord(date(2026, 11, 23), "Oasis", 1, 1),
    ]
    database_connection.close()


def test_known_venues_are_ordered_by_frequency_and_skip_blank(stats_database_connection):
    for day, venue in [(1, "Powerleague"), (2, "Oasis"), (3, "Powerleague"), (4, ""), (5, "Trinity")]:
        insert_match_record(stats_database_connection, MatchRecord(date(2026, 9, day), venue, 0, 0))
    assert fetch_known_venues_ordered_by_frequency(stats_database_connection) == ["Powerleague", "Trinity", "Oasis"]
    assert fetch_most_recent_venue(stats_database_connection) == "Trinity"


def test_most_recent_venue_is_none_for_empty_database(stats_database_connection):
    assert fetch_most_recent_venue(stats_database_connection) is None


def test_career_totals_sum_goals_and_assists():
    match_records = [MatchRecord(date(2026, 9, 1), "A", 2, 1), MatchRecord(date(2026, 9, 2), "B", 1, 3)]
    career_totals = calculate_career_totals_from_records(match_records)
    assert (career_totals.matches_played, career_totals.goals, career_totals.assists) == (2, 3, 4)


def test_settings_are_stored_and_overwritten(stats_database_connection):
    write_setting_value(stats_database_connection, "profile_url", "https://example.com/a")
    write_setting_value(stats_database_connection, "profile_url", "https://example.com/b")
    assert read_setting_value(stats_database_connection, "profile_url") == "https://example.com/b"
