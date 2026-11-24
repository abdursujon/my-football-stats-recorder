from footie.storage.database import calculate_career_totals_from_records

STATS_SECTION_START_MARKER = "<!-- footie-stats:start -->"
STATS_SECTION_END_MARKER = "<!-- footie-stats:end -->"
STATS_SECTION_HEADING = "## My Football Stats"
README_MATCH_DATE_FORMAT = "%d %b %Y %A"
STATS_TABLE_COLUMN_TITLES = ("Venue", "Date", "Goals", "Assists")


def format_match_date_for_readme(match_date):
    return match_date.strftime(README_MATCH_DATE_FORMAT)


def build_stats_table_rows(match_records):
    return [
        (
            match_record.venue,
            format_match_date_for_readme(match_record.match_date),
            str(match_record.goals),
            str(match_record.assists),
        )
        for match_record in match_records
    ]


def render_aligned_markdown_table(column_titles, table_rows):
    column_widths = [
        max([len(column_title)] + [len(table_row[column_index]) for table_row in table_rows])
        for column_index, column_title in enumerate(column_titles)
    ]

    def render_table_line(cell_values):
        padded_cells = [cell_value.ljust(column_width) for cell_value, column_width in zip(cell_values, column_widths)]
        return "| " + " | ".join(padded_cells) + " |"

    separator_line = "| " + " | ".join("-" * column_width for column_width in column_widths) + " |"
    return "\n".join([render_table_line(column_titles), separator_line] + [render_table_line(row) for row in table_rows])


def render_stats_section_markdown(match_records, profile_url=None):
    career_totals = calculate_career_totals_from_records(match_records)
    section_lines = []
    if profile_url:
        section_lines += [f"Footy Addicts profile: [{profile_url}]({profile_url})", ""]
    section_lines += [
        f"Total Match Played = {career_totals.matches_played} "
        f"| Total Goals = {career_totals.goals} "
        f"| Total Assists = {career_totals.assists}",
        "",
        render_aligned_markdown_table(STATS_TABLE_COLUMN_TITLES, build_stats_table_rows(match_records)),
    ]
    return "\n".join(section_lines)


def replace_stats_section_in_readme_text(readme_text, stats_section_markdown):
    marked_stats_block = f"{STATS_SECTION_START_MARKER}\n{stats_section_markdown}\n{STATS_SECTION_END_MARKER}"
    start_marker_index = readme_text.rfind(STATS_SECTION_START_MARKER)
    end_marker_index = readme_text.find(STATS_SECTION_END_MARKER, start_marker_index)

    if start_marker_index != -1 and end_marker_index > start_marker_index:
        text_after_end_marker = readme_text[end_marker_index + len(STATS_SECTION_END_MARKER):]
        return readme_text[:start_marker_index] + marked_stats_block + text_after_end_marker

    readme_text_with_trailing_newline = readme_text.rstrip("\n") + "\n\n" if readme_text.strip() else ""
    return f"{readme_text_with_trailing_newline}{STATS_SECTION_HEADING}\n\n{marked_stats_block}\n"


def write_stats_section_to_readme_file(readme_file_path, match_records, profile_url=None):
    existing_readme_text = readme_file_path.read_text(encoding="utf-8") if readme_file_path.exists() else ""
    updated_readme_text = replace_stats_section_in_readme_text(
        existing_readme_text, render_stats_section_markdown(match_records, profile_url)
    )
    readme_file_path.parent.mkdir(parents=True, exist_ok=True)
    readme_file_path.write_text(updated_readme_text, encoding="utf-8")
    return updated_readme_text != existing_readme_text
