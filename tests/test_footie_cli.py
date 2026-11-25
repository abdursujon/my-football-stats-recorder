from datetime import date

import pytest

from footie.cli import command_line
from footie.cli.command_line import run_footie_command_line
from footie.storage.database import MatchRecord


def test_fresh_install_has_empty_stats(isolated_data_directory, capsys):
    assert run_footie_command_line(["stats"]) == 0
    assert (
        "Total Match Played = 0 | Total Goals = 0 | Total Assists = 0"
        in capsys.readouterr().out
    )
    assert (isolated_data_directory / "footie.db").exists()


def test_add_then_stats_and_venues(isolated_data_directory, capsys):
    assert (
        run_footie_command_line(
            [
                "add",
                "--date",
                "23/11/2026",
                "--venue",
                "Ordsall Leisure Centre",
                "--goals",
                "3",
                "--assists",
                "1",
            ]
        )
        == 0
    )
    assert (
        run_footie_command_line(
            ["add", "--date", "21/11/2026", "--venue", "Oasis Academy Media City"]
        )
        == 0
    )
    capsys.readouterr()
    run_footie_command_line(["stats"])
    assert (
        "Total Match Played = 2 | Total Goals = 3 | Total Assists = 1"
        in capsys.readouterr().out
    )
    run_footie_command_line(["venues"])
    assert capsys.readouterr().out.splitlines() == [
        "Ordsall Leisure Centre",
        "Oasis Academy Media City",
    ]


def test_two_matches_on_same_day_are_both_counted(isolated_data_directory, capsys):
    assert (
        run_footie_command_line(
            ["add", "--date", "23/11/2026", "--venue", "A", "--goals", "1"]
        )
        == 0
    )
    assert (
        run_footie_command_line(
            ["add", "--date", "23/11/2026", "--venue", "B", "--goals", "2"]
        )
        == 0
    )
    capsys.readouterr()
    run_footie_command_line(["stats"])
    assert (
        "Total Match Played = 2 | Total Goals = 3 | Total Assists = 0"
        in capsys.readouterr().out
    )


def test_add_rejects_invalid_goals(isolated_data_directory, capsys):
    assert run_footie_command_line(["add", "--goals", "lots"]) == 1
    assert "Goals must be a whole number" in capsys.readouterr().err


def test_stats_readme_is_written_with_profile_link(isolated_data_directory, tmp_path):
    readme_file_path = tmp_path / "stats" / "README.md"
    run_footie_command_line(["set-stats-readme", str(readme_file_path), "--git", "off"])
    run_footie_command_line(
        ["change-profile", "https://footyaddicts.com/players/someone"]
    )
    run_footie_command_line(
        [
            "add",
            "--date",
            "23/11/2026",
            "--venue",
            "Ordsall Leisure Centre",
            "--goals",
            "2",
        ]
    )
    readme_text = readme_file_path.read_text()
    assert "https://footyaddicts.com/players/someone" in readme_text
    assert (
        "| Ordsall Leisure Centre | 23 Nov 2026 Monday | 2     | 0       |"
        in readme_text
    )


def test_change_profile_rejects_non_url(isolated_data_directory):
    assert run_footie_command_line(["change-profile", "someone"]) == 1


def test_list_shows_ids_and_delete_removes_only_that_match(
    isolated_data_directory, capsys
):
    run_footie_command_line(["add", "--date", "23/11/2026", "--venue", "Ordsall"])
    run_footie_command_line(["add", "--date", "23/11/2026", "--venue", "Oasis"])
    capsys.readouterr()
    run_footie_command_line(["list"])
    listed_lines = capsys.readouterr().out.splitlines()
    assert listed_lines[1].split()[:2] == ["1", "23/11/2026"] and listed_lines[
        1
    ].endswith("Ordsall")
    assert listed_lines[2].split()[:2] == ["2", "23/11/2026"] and listed_lines[
        2
    ].endswith("Oasis")

    assert run_footie_command_line(["delete", "1"]) == 0
    assert run_footie_command_line(["delete", "1"]) == 1
    capsys.readouterr()
    run_footie_command_line(["venues"])
    assert capsys.readouterr().out.splitlines() == ["Oasis"]


def test_iso_date_is_rejected_in_favour_of_uk_format(isolated_data_directory, capsys):
    assert run_footie_command_line(["add", "--date", "2026-11-23", "--venue", "A"]) == 1
    assert "DD/MM/YYYY" in capsys.readouterr().err


def test_import_csv_command(isolated_data_directory, tmp_path, capsys):
    csv_file_path = tmp_path / "matches.csv"
    csv_file_path.write_text(
        "date,venue,goals,assists\n11/08/2026,Powerleague,0,0\n18/08/2026,Powerleague,1,0\n"
    )
    assert run_footie_command_line(["import-csv", str(csv_file_path)]) == 0
    assert "Imported 2 matches" in capsys.readouterr().out


def test_reminder_skips_window_when_today_is_recorded(
    isolated_data_directory, monkeypatch
):
    opened_windows = []
    monkeypatch.setattr(
        command_line,
        "open_match_entry_window_and_save",
        lambda database_connection: opened_windows.append(True) or 0,
    )
    run_footie_command_line(["--if-no-record-today"])
    assert opened_windows == [True]
    run_footie_command_line(["add", "--venue", "A"])
    run_footie_command_line(["--if-no-record-today"])
    assert opened_windows == [True]


def test_plain_footie_shows_stats_without_opening_window(
    isolated_data_directory, monkeypatch, capsys
):
    monkeypatch.setattr(
        command_line,
        "open_match_entry_window_and_save",
        lambda database_connection: pytest.fail("window must not open"),
    )
    run_footie_command_line(["add", "--venue", "Ordsall", "--goals", "2"])
    capsys.readouterr()
    assert run_footie_command_line([]) == 0
    assert (
        "Total Match Played = 1 | Total Goals = 2 | Total Assists = 0"
        in capsys.readouterr().out
    )


def test_add_without_options_opens_window_and_saves_entry(
    isolated_data_directory, monkeypatch, capsys
):
    import footie.gui.match_entry_window as match_entry_window

    monkeypatch.setattr(
        match_entry_window,
        "prompt_for_match_entry_in_window",
        lambda **keyword_arguments: MatchRecord(date(2026, 11, 23), "Ordsall", 1, 2),
    )
    assert run_footie_command_line(["add"]) == 0
    run_footie_command_line([])
    assert (
        "Total Match Played = 1 | Total Goals = 1 | Total Assists = 2"
        in capsys.readouterr().out
    )


def test_closing_window_without_saving_records_nothing(
    isolated_data_directory, monkeypatch, capsys
):
    import footie.gui.match_entry_window as match_entry_window

    monkeypatch.setattr(
        match_entry_window,
        "prompt_for_match_entry_in_window",
        lambda **keyword_arguments: None,
    )
    assert run_footie_command_line(["add"]) == 0
    run_footie_command_line([])
    assert "Total Match Played = 0" in capsys.readouterr().out


def test_install_schedule_saves_choice(isolated_data_directory, monkeypatch, capsys):
    installed_requests = []
    monkeypatch.setattr(
        command_line,
        "install_daily_reminder_schedule",
        lambda backend, time_text: (
            installed_requests.append((backend, time_text)) or "fake"
        ),
    )
    assert (
        run_footie_command_line(
            ["install-schedule", "--os", "linux-cron", "--time", "21:30"]
        )
        == 0
    )
    assert installed_requests == [("linux-cron", "21:30")]
    capsys.readouterr()
    run_footie_command_line(["show-schedule"])
    assert capsys.readouterr().out.strip() == "Daily reminder at 21:30 via linux-cron"


def test_install_schedule_rejects_unknown_os(isolated_data_directory):
    with pytest.raises(SystemExit):
        run_footie_command_line(["install-schedule", "--os", "amiga"])
