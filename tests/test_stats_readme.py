from datetime import date

from footie.publishing.stats_readme import (
    STATS_SECTION_END_MARKER,
    STATS_SECTION_START_MARKER,
    render_stats_section_markdown,
    replace_stats_section_in_readme_text,
    write_stats_section_to_readme_file,
)
from footie.storage.database import MatchRecord

SAMPLE_MATCH_RECORDS = [
    MatchRecord(date(2026, 9, 13), "Platt Lane (ManCity Academy)", 1, 1),
    MatchRecord(date(2026, 11, 23), "Ordsall Leisure Centre", 3, 0),
]


def test_section_shows_totals_and_venue_date_goals_assists_columns():
    rendered_section = render_stats_section_markdown(SAMPLE_MATCH_RECORDS)
    rendered_lines = rendered_section.splitlines()
    assert (
        rendered_lines[0]
        == "Total Match Played = 2 | Total Goals = 4 | Total Assists = 1"
    )
    assert [
        column_title.strip() for column_title in rendered_lines[2].split("|")[1:5]
    ] == ["Venue", "Date", "Goals", "Assists"]
    assert (
        "| Ordsall Leisure Centre       | 23 Nov 2026 Monday | 3     | 0       |"
        in rendered_lines
    )


def test_empty_database_renders_zero_totals_and_header_only():
    rendered_lines = render_stats_section_markdown([]).splitlines()
    assert (
        rendered_lines[0]
        == "Total Match Played = 0 | Total Goals = 0 | Total Assists = 0"
    )
    assert rendered_lines[2:] == [
        "| Venue | Date | Goals | Assists |",
        "| ----- | ---- | ----- | ------- |",
    ]


def test_profile_link_is_shown_when_set():
    rendered_section = render_stats_section_markdown(
        [], "https://footyaddicts.com/players/someone"
    )
    assert rendered_section.startswith(
        "Footy Addicts profile: [https://footyaddicts.com/players/someone](https://footyaddicts.com/players/someone)"
    )


def test_replace_keeps_text_outside_markers():
    original_readme_text = f"# Guide\nInstall with pipx.\n\n{STATS_SECTION_START_MARKER}\nold stats\n{STATS_SECTION_END_MARKER}\n\nFooter\n"
    updated_readme_text = replace_stats_section_in_readme_text(
        original_readme_text, "new stats"
    )
    assert updated_readme_text == (
        f"# Guide\nInstall with pipx.\n\n{STATS_SECTION_START_MARKER}\nnew stats\n{STATS_SECTION_END_MARKER}\n\nFooter\n"
    )


def test_markers_quoted_earlier_in_guide_are_left_alone():
    quoted_markers_example = (
        f"```\n{STATS_SECTION_START_MARKER}\n{STATS_SECTION_END_MARKER}\n```\n"
    )
    original_readme_text = f"# Guide\n{quoted_markers_example}\n## Stats\n{STATS_SECTION_START_MARKER}\nold\n{STATS_SECTION_END_MARKER}\n"
    updated_readme_text = replace_stats_section_in_readme_text(
        original_readme_text, "new"
    )
    assert updated_readme_text == (
        f"# Guide\n{quoted_markers_example}\n## Stats\n{STATS_SECTION_START_MARKER}\nnew\n{STATS_SECTION_END_MARKER}\n"
    )


def test_section_is_appended_when_markers_are_missing():
    updated_readme_text = replace_stats_section_in_readme_text("# My repo\n", "stats")
    assert updated_readme_text == (
        f"# My repo\n\n## My Football Stats\n\n{STATS_SECTION_START_MARKER}\nstats\n{STATS_SECTION_END_MARKER}\n"
    )


def test_write_creates_missing_readme_and_reports_changes(tmp_path):
    readme_file_path = tmp_path / "README.md"
    assert write_stats_section_to_readme_file(readme_file_path, SAMPLE_MATCH_RECORDS)
    assert "Ordsall Leisure Centre" in readme_file_path.read_text()
    assert not write_stats_section_to_readme_file(
        readme_file_path, SAMPLE_MATCH_RECORDS
    )
