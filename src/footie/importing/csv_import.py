import csv

from footie.storage.database import has_identical_match_record, insert_match_record
from footie.validation.match_validation import build_validated_match_record

REQUIRED_CSV_COLUMNS = ("date", "venue", "goals", "assists")


def read_match_records_from_csv_file(csv_file_path):
    with csv_file_path.open(newline="", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        missing_columns = [column for column in REQUIRED_CSV_COLUMNS if column not in (csv_reader.fieldnames or [])]
        if missing_columns:
            raise ValueError(f"CSV is missing columns: {', '.join(missing_columns)}")
        parsed_match_records = []
        for line_number, csv_row in enumerate(csv_reader, start=2):
            try:
                parsed_match_records.append(
                    build_validated_match_record(csv_row["date"], csv_row["venue"], csv_row["goals"], csv_row["assists"])
                )
            except ValueError as validation_error:
                raise ValueError(f"Line {line_number}: {validation_error}") from None
    return parsed_match_records


def import_match_records_into_database(database_connection, match_records, skip_identical_matches=True):
    imported_count = 0
    skipped_count = 0
    for match_record in match_records:
        if skip_identical_matches and has_identical_match_record(database_connection, match_record):
            skipped_count += 1
            continue
        insert_match_record(database_connection, match_record)
        imported_count += 1
    return imported_count, skipped_count
