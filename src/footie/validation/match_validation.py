from datetime import datetime

from footie.storage.database import MatchRecord

UK_DATE_FORMAT = "%d/%m/%Y"
UK_DATE_FORMAT_HINT = "DD/MM/YYYY"


def format_match_date_as_uk(match_date):
    return match_date.strftime(UK_DATE_FORMAT)


def parse_non_negative_whole_number(field_label, raw_text):
    try:
        parsed_number = int(str(raw_text).strip())
    except ValueError:
        raise ValueError(f"{field_label} must be a whole number.") from None
    if parsed_number < 0:
        raise ValueError(f"{field_label} cannot be negative.")
    return parsed_number


def parse_uk_match_date(raw_text):
    try:
        return datetime.strptime(str(raw_text).strip(), UK_DATE_FORMAT).date()
    except ValueError:
        raise ValueError(f"Date must be in {UK_DATE_FORMAT_HINT} format, for example 23/11/2026.") from None


def build_validated_match_record(match_date_text, venue_text, goals_text, assists_text):
    return MatchRecord(
        match_date=parse_uk_match_date(match_date_text),
        venue=str(venue_text).strip(),
        goals=parse_non_negative_whole_number("Goals", goals_text),
        assists=parse_non_negative_whole_number("Assists", assists_text),
    )
