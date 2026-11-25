from datetime import date

import pytest

from footie.storage.database import MatchRecord
from footie.validation.match_validation import (
    build_validated_match_record,
    format_match_date_as_uk,
)


def test_valid_input_builds_trimmed_record():
    assert build_validated_match_record(
        "23/11/2026", "  Ordsall  ", " 3 ", "0"
    ) == MatchRecord(date(2026, 11, 23), "Ordsall", 3, 0)


def test_day_comes_before_month():
    assert build_validated_match_record("01/11/2026", "A", "0", "0").match_date == date(
        2026, 11, 1
    )


def test_date_is_formatted_as_uk():
    assert format_match_date_as_uk(date(2026, 11, 1)) == "01/11/2026"


@pytest.mark.parametrize(
    "match_date_text, goals_text, assists_text, expected_message",
    [
        ("2026-11-23", "1", "0", "DD/MM/YYYY"),
        ("11/23/2026", "1", "0", "DD/MM/YYYY"),
        ("23/11/2026", "two", "0", "Goals must be a whole number"),
        ("23/11/2026", "1", "-1", "Assists cannot be negative"),
    ],
)
def test_invalid_input_raises_readable_error(
    match_date_text, goals_text, assists_text, expected_message
):
    with pytest.raises(ValueError, match=expected_message):
        build_validated_match_record(match_date_text, "Venue", goals_text, assists_text)
