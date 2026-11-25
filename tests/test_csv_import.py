from datetime import date

import pytest

from footie.importing.csv_import import (
    import_match_records_into_database,
    read_match_records_from_csv_file,
)
from footie.storage.database import (
    MatchRecord,
    fetch_all_match_records_ordered_by_date,
    insert_match_record,
)


def test_csv_rows_become_match_records(tmp_path):
    csv_file_path = tmp_path / "matches.csv"
    csv_file_path.write_text(
        'date,venue,goals,assists\n23/11/2026,"Denmark Road Sports Centre, Manchester",3,0\n'
    )
    assert read_match_records_from_csv_file(csv_file_path) == [
        MatchRecord(date(2026, 11, 23), "Denmark Road Sports Centre, Manchester", 3, 0)
    ]


def test_missing_columns_are_reported(tmp_path):
    csv_file_path = tmp_path / "matches.csv"
    csv_file_path.write_text("date,goals\n23/11/2026,1\n")
    with pytest.raises(ValueError, match="venue, assists"):
        read_match_records_from_csv_file(csv_file_path)


def test_invalid_row_reports_line_number(tmp_path):
    csv_file_path = tmp_path / "matches.csv"
    csv_file_path.write_text(
        "date,venue,goals,assists\n23/11/2026,A,1,0\n24/11/2026,B,x,0\n"
    )
    with pytest.raises(ValueError, match="Line 3"):
        read_match_records_from_csv_file(csv_file_path)


def test_identical_rows_are_skipped_but_same_day_matches_are_imported(
    stats_database_connection,
):
    insert_match_record(
        stats_database_connection, MatchRecord(date(2026, 9, 1), "Old", 1, 1)
    )
    incoming_records = [
        MatchRecord(date(2026, 9, 1), "Old", 1, 1),
        MatchRecord(date(2026, 9, 1), "New", 2, 0),
    ]
    assert import_match_records_into_database(
        stats_database_connection, incoming_records
    ) == (1, 1)
    assert len(fetch_all_match_records_ordered_by_date(stats_database_connection)) == 2


def test_identical_rows_can_be_kept_on_request(stats_database_connection):
    insert_match_record(
        stats_database_connection, MatchRecord(date(2026, 9, 1), "Old", 1, 1)
    )
    incoming_records = [MatchRecord(date(2026, 9, 1), "Old", 1, 1)]
    assert import_match_records_into_database(
        stats_database_connection, incoming_records, skip_identical_matches=False
    ) == (1, 0)
