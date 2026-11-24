import argparse
import sys
from datetime import date
from pathlib import Path

from footie import __version__
from footie.importing.csv_import import import_match_records_into_database, read_match_records_from_csv_file
from footie.publishing.git_publisher import GitPublishingError, commit_and_push_stats_readme
from footie.publishing.stats_readme import (
    format_match_date_for_readme,
    render_stats_section_markdown,
    write_stats_section_to_readme_file,
)
from footie.scheduling.reminder_schedule import (
    DEFAULT_REMINDER_TIME,
    SUPPORTED_SCHEDULE_BACKENDS,
    ScheduleError,
    detect_default_schedule_backend,
    install_daily_reminder_schedule,
    parse_reminder_time_to_hour_and_minute,
    remove_daily_reminder_schedule,
)
from footie.storage.data_paths import resolve_database_file_path
from footie.storage.database import (
    SETTING_GIT_PUBLISHING,
    SETTING_PROFILE_URL,
    SETTING_SCHEDULE_BACKEND,
    SETTING_SCHEDULE_TIME,
    SETTING_STATS_README_PATH,
    delete_match_record_by_id,
    delete_setting_value,
    fetch_all_match_records_ordered_by_date,
    fetch_match_record_by_id,
    fetch_known_venues_ordered_by_frequency,
    fetch_most_recent_venue,
    has_match_record_for_date,
    insert_match_record,
    open_stats_database,
    read_setting_value,
    write_setting_value,
)
from footie.validation.match_validation import (
    UK_DATE_FORMAT_HINT,
    build_validated_match_record,
    format_match_date_as_uk,
)

GIT_PUBLISHING_PUSH = "push"
GIT_PUBLISHING_COMMIT = "commit"
GIT_PUBLISHING_OFF = "off"
GIT_PUBLISHING_MODES = (GIT_PUBLISHING_PUSH, GIT_PUBLISHING_COMMIT, GIT_PUBLISHING_OFF)


def print_error_message(message):
    print(f"footie: {message}", file=sys.stderr)


def write_stats_readme_if_configured(database_connection):
    configured_readme_path = read_setting_value(database_connection, SETTING_STATS_README_PATH)
    if not configured_readme_path:
        return None
    readme_file_path = Path(configured_readme_path)
    write_stats_section_to_readme_file(
        readme_file_path,
        fetch_all_match_records_ordered_by_date(database_connection),
        read_setting_value(database_connection, SETTING_PROFILE_URL),
    )
    return readme_file_path


def publish_stats_readme_with_git(database_connection, commit_message):
    readme_file_path = write_stats_readme_if_configured(database_connection)
    if readme_file_path is None:
        print("Saved. Run 'footie set-stats-readme PATH' to publish your stats to a README.")
        return 0
    print(f"Updated {readme_file_path}")

    git_publishing_mode = read_setting_value(database_connection, SETTING_GIT_PUBLISHING, GIT_PUBLISHING_PUSH)
    if git_publishing_mode == GIT_PUBLISHING_OFF:
        return 0
    try:
        committed = commit_and_push_stats_readme(
            readme_file_path, commit_message, push_to_remote=git_publishing_mode == GIT_PUBLISHING_PUSH
        )
    except GitPublishingError as publishing_error:
        print_error_message(f"stats saved, but git publishing failed: {publishing_error}")
        return 1
    if committed:
        print("Committed and pushed." if git_publishing_mode == GIT_PUBLISHING_PUSH else "Committed.")
    return 0


def save_match_record_and_publish(database_connection, match_record):
    match_id = insert_match_record(database_connection, match_record)
    print(
        f"Recorded match {match_id}: {format_match_date_as_uk(match_record.match_date)} at "
        f"{match_record.venue or 'unknown venue'}, {match_record.goals} goals, {match_record.assists} assists."
    )
    commit_message = f"Record match stats for {format_match_date_for_readme(match_record.match_date)}"
    return publish_stats_readme_with_git(database_connection, commit_message)


def open_match_entry_window_and_save(database_connection):
    from footie.gui.match_entry_window import prompt_for_match_entry_in_window

    entered_match_record = prompt_for_match_entry_in_window(
        known_venues=fetch_known_venues_ordered_by_frequency(database_connection),
        default_venue=fetch_most_recent_venue(database_connection),
        build_match_record=build_validated_match_record,
    )
    if entered_match_record is None:
        return 0
    return save_match_record_and_publish(database_connection, entered_match_record)


def run_default_command(database_connection, parsed_arguments):
    if not parsed_arguments.if_no_record_today:
        return run_stats_command(database_connection, parsed_arguments)
    if has_match_record_for_date(database_connection, date.today()):
        return 0
    return open_match_entry_window_and_save(database_connection)


def run_add_command(database_connection, parsed_arguments):
    entered_field_values = (parsed_arguments.date, parsed_arguments.venue, parsed_arguments.goals,
                            parsed_arguments.assists)
    if all(field_value is None for field_value in entered_field_values):
        return open_match_entry_window_and_save(database_connection)
    try:
        match_record = build_validated_match_record(
            parsed_arguments.date or format_match_date_as_uk(date.today()),
            parsed_arguments.venue or "",
            parsed_arguments.goals or "0",
            parsed_arguments.assists or "0",
        )
    except ValueError as validation_error:
        print_error_message(str(validation_error))
        return 1
    return save_match_record_and_publish(database_connection, match_record)


def format_match_record_as_list_line(match_record):
    return (
        f"{match_record.match_id:>4}  {format_match_date_as_uk(match_record.match_date)}  "
        f"{match_record.goals:>2} G  {match_record.assists:>2} A  {match_record.venue}"
    )


def run_list_command(database_connection, parsed_arguments):
    match_records = fetch_all_match_records_ordered_by_date(database_connection)
    if not match_records:
        print("No matches recorded yet.")
        return 0
    print("  ID  Date         Goals Assists Venue")
    for match_record in match_records:
        print(format_match_record_as_list_line(match_record))
    return 0


def run_delete_command(database_connection, parsed_arguments):
    match_record = fetch_match_record_by_id(database_connection, parsed_arguments.match_id)
    if match_record is None:
        print_error_message(f"no match with ID {parsed_arguments.match_id}. Run 'footie list' to see IDs.")
        return 1
    delete_match_record_by_id(database_connection, match_record.match_id)
    print(f"Deleted match {match_record.match_id}: {format_match_record_as_list_line(match_record).strip()}")
    return publish_stats_readme_with_git(
        database_connection, f"Remove match stats for {format_match_date_for_readme(match_record.match_date)}"
    )


def run_stats_command(database_connection, parsed_arguments):
    print(render_stats_section_markdown(
        fetch_all_match_records_ordered_by_date(database_connection),
        read_setting_value(database_connection, SETTING_PROFILE_URL),
    ))
    return 0


def run_venues_command(database_connection, parsed_arguments):
    for venue in fetch_known_venues_ordered_by_frequency(database_connection):
        print(venue)
    return 0


def run_change_profile_command(database_connection, parsed_arguments):
    profile_url = parsed_arguments.url.strip()
    if not profile_url.startswith(("http://", "https://")):
        print_error_message("profile URL must start with http:// or https://")
        return 1
    write_setting_value(database_connection, SETTING_PROFILE_URL, profile_url)
    print(f"Profile set to {profile_url}")
    write_stats_readme_if_configured(database_connection)
    return 0


def run_profile_command(database_connection, parsed_arguments):
    print(read_setting_value(database_connection, SETTING_PROFILE_URL) or "No profile set. Use 'footie change-profile URL'.")
    return 0


def run_set_stats_readme_command(database_connection, parsed_arguments):
    readme_file_path = Path(parsed_arguments.path).expanduser().resolve()
    write_setting_value(database_connection, SETTING_STATS_README_PATH, str(readme_file_path))
    write_setting_value(database_connection, SETTING_GIT_PUBLISHING, parsed_arguments.git)
    write_stats_readme_if_configured(database_connection)
    print(f"Stats README set to {readme_file_path} (git: {parsed_arguments.git})")
    return 0


def run_publish_command(database_connection, parsed_arguments):
    return publish_stats_readme_with_git(database_connection, "Update match stats")


def run_import_csv_command(database_connection, parsed_arguments):
    try:
        match_records = read_match_records_from_csv_file(Path(parsed_arguments.file))
    except (OSError, ValueError) as import_error:
        print_error_message(str(import_error))
        return 1
    imported_count, skipped_count = import_match_records_into_database(
        database_connection, match_records, skip_identical_matches=not parsed_arguments.keep_duplicates
    )
    print(f"Imported {imported_count} matches, skipped {skipped_count} identical to ones already recorded.")
    readme_file_path = write_stats_readme_if_configured(database_connection)
    if readme_file_path:
        print(f"Updated {readme_file_path}. Run 'footie publish' to commit and push it.")
    return 0


def run_install_schedule_command(database_connection, parsed_arguments):
    schedule_backend = parsed_arguments.os or detect_default_schedule_backend()
    try:
        installed_description = install_daily_reminder_schedule(schedule_backend, parsed_arguments.time)
    except (ScheduleError, OSError) as schedule_error:
        print_error_message(str(schedule_error))
        return 1
    hour, minute = parse_reminder_time_to_hour_and_minute(parsed_arguments.time)
    write_setting_value(database_connection, SETTING_SCHEDULE_BACKEND, schedule_backend)
    write_setting_value(database_connection, SETTING_SCHEDULE_TIME, f"{hour:02d}:{minute:02d}")
    print(f"Daily reminder at {hour:02d}:{minute:02d} installed: {installed_description}")
    return 0


def run_remove_schedule_command(database_connection, parsed_arguments):
    schedule_backend = (
        parsed_arguments.os
        or read_setting_value(database_connection, SETTING_SCHEDULE_BACKEND)
        or detect_default_schedule_backend()
    )
    try:
        removed_description = remove_daily_reminder_schedule(schedule_backend)
    except (ScheduleError, OSError) as schedule_error:
        print_error_message(str(schedule_error))
        return 1
    delete_setting_value(database_connection, SETTING_SCHEDULE_BACKEND)
    delete_setting_value(database_connection, SETTING_SCHEDULE_TIME)
    print(f"Removed {removed_description}")
    return 0


def run_show_schedule_command(database_connection, parsed_arguments):
    schedule_backend = read_setting_value(database_connection, SETTING_SCHEDULE_BACKEND)
    if not schedule_backend:
        print("No reminder installed. Use 'footie install-schedule'.")
        return 0
    print(f"Daily reminder at {read_setting_value(database_connection, SETTING_SCHEDULE_TIME)} via {schedule_backend}")
    return 0


def run_where_command(database_connection, parsed_arguments):
    print(f"Database:     {parsed_arguments.database_file_path}")
    print(f"Stats README: {read_setting_value(database_connection, SETTING_STATS_README_PATH) or 'not set'}")
    print(f"Git:          {read_setting_value(database_connection, SETTING_GIT_PUBLISHING) or 'not set'}")
    print(f"Profile:      {read_setting_value(database_connection, SETTING_PROFILE_URL) or 'not set'}")
    return 0


def build_argument_parser():
    argument_parser = argparse.ArgumentParser(
        prog="footie", description="Record football match stats. Run with no command to show your stats."
    )
    argument_parser.add_argument("--version", action="version", version=f"footie {__version__}")
    argument_parser.add_argument(
        "--if-no-record-today", action="store_true",
        help="open the entry window only if no match is recorded for today (used by the daily reminder)",
    )
    argument_parser.set_defaults(command_handler=run_default_command)
    subcommand_parsers = argument_parser.add_subparsers(title="commands", metavar="COMMAND")

    add_parser = subcommand_parsers.add_parser(
        "add", help="open the match entry window, or record directly when any option is given"
    )
    add_parser.add_argument("--venue", help="venue name")
    add_parser.add_argument("--goals", help="goals scored (default 0)")
    add_parser.add_argument("--assists", help="assists (default 0)")
    add_parser.add_argument("--date", help=f"match date {UK_DATE_FORMAT_HINT} (default today)")
    add_parser.set_defaults(command_handler=run_add_command)

    list_parser = subcommand_parsers.add_parser("list", help="list every match with its ID")
    list_parser.set_defaults(command_handler=run_list_command)

    delete_parser = subcommand_parsers.add_parser("delete", help="delete a match by ID (see 'footie list')")
    delete_parser.add_argument("match_id", type=int, help="match ID")
    delete_parser.set_defaults(command_handler=run_delete_command)

    stats_parser = subcommand_parsers.add_parser("stats", help="print totals and the match table")
    stats_parser.set_defaults(command_handler=run_stats_command)

    venues_parser = subcommand_parsers.add_parser("venues", help="list known venues, most played first")
    venues_parser.set_defaults(command_handler=run_venues_command)

    change_profile_parser = subcommand_parsers.add_parser("change-profile", help="set your Footy Addicts profile URL")
    change_profile_parser.add_argument("url", help="for example https://footyaddicts.com/players/<name>")
    change_profile_parser.set_defaults(command_handler=run_change_profile_command)

    profile_parser = subcommand_parsers.add_parser("profile", help="show the saved profile URL")
    profile_parser.set_defaults(command_handler=run_profile_command)

    set_stats_readme_parser = subcommand_parsers.add_parser(
        "set-stats-readme", help="choose the README file your stats are written to"
    )
    set_stats_readme_parser.add_argument("path", help="path to a README.md, usually inside a git repository")
    set_stats_readme_parser.add_argument(
        "--git", choices=GIT_PUBLISHING_MODES, default=GIT_PUBLISHING_PUSH,
        help="after each save: commit and push (default), commit only, or no git",
    )
    set_stats_readme_parser.set_defaults(command_handler=run_set_stats_readme_command)

    publish_parser = subcommand_parsers.add_parser("publish", help="rewrite the stats README and commit/push it")
    publish_parser.set_defaults(command_handler=run_publish_command)

    import_csv_parser = subcommand_parsers.add_parser(
        "import-csv", help=f"import matches from a CSV with columns date ({UK_DATE_FORMAT_HINT}),venue,goals,assists"
    )
    import_csv_parser.add_argument("file", help="CSV file path")
    import_csv_parser.add_argument(
        "--keep-duplicates", action="store_true",
        help="also import rows identical to a match already recorded (same date, venue, goals and assists)",
    )
    import_csv_parser.set_defaults(command_handler=run_import_csv_command)

    install_schedule_parser = subcommand_parsers.add_parser(
        "install-schedule", help="install the daily reminder for this operating system"
    )
    install_schedule_parser.add_argument(
        "--os", choices=SUPPORTED_SCHEDULE_BACKENDS, help="scheduler to use (default: detected from this system)"
    )
    install_schedule_parser.add_argument(
        "--time", default=DEFAULT_REMINDER_TIME, help=f"reminder time HH:MM (default {DEFAULT_REMINDER_TIME})"
    )
    install_schedule_parser.set_defaults(command_handler=run_install_schedule_command)

    remove_schedule_parser = subcommand_parsers.add_parser("remove-schedule", help="remove the daily reminder")
    remove_schedule_parser.add_argument("--os", choices=SUPPORTED_SCHEDULE_BACKENDS, help="scheduler to remove from")
    remove_schedule_parser.set_defaults(command_handler=run_remove_schedule_command)

    show_schedule_parser = subcommand_parsers.add_parser("show-schedule", help="show the installed reminder")
    show_schedule_parser.set_defaults(command_handler=run_show_schedule_command)

    where_parser = subcommand_parsers.add_parser("where", help="show where data and settings are stored")
    where_parser.set_defaults(command_handler=run_where_command)

    return argument_parser


def run_footie_command_line(argument_list=None):
    parsed_arguments = build_argument_parser().parse_args(argument_list)
    parsed_arguments.database_file_path = resolve_database_file_path()
    database_connection = open_stats_database(parsed_arguments.database_file_path)
    try:
        return parsed_arguments.command_handler(database_connection, parsed_arguments)
    finally:
        database_connection.close()
