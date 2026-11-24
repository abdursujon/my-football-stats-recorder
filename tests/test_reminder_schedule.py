import subprocess
from pathlib import Path

import pytest

from footie.scheduling.reminder_schedule import (
    CRON_LINE_MARKER,
    ScheduleEnvironment,
    ScheduleError,
    build_crontab_text_with_reminder_line,
    build_launchd_plist_text,
    build_systemd_timer_unit_text,
    build_windows_scheduled_task_create_command,
    detect_default_schedule_backend,
    install_daily_reminder_schedule,
    parse_reminder_time_to_hour_and_minute,
    remove_daily_reminder_schedule,
    remove_reminder_line_from_crontab_text,
)

PYTHON_EXECUTABLE = "/opt/footie/bin/python"


class RecordingCommandRunner:
    def __init__(self, stdout_by_command=None):
        self.recorded_commands = []
        self.stdout_by_command = stdout_by_command or {}

    def __call__(self, command_arguments, input=None, **keyword_arguments):
        self.recorded_commands.append((list(command_arguments), input))
        return subprocess.CompletedProcess(
            command_arguments, 0, stdout=self.stdout_by_command.get(tuple(command_arguments), ""), stderr=""
        )


def build_schedule_environment(home_directory, command_runner):
    return ScheduleEnvironment(home_directory=home_directory, python_executable=PYTHON_EXECUTABLE,
                               run_command=command_runner)


@pytest.mark.parametrize("operating_system_name, expected_backend",
                         [("Linux", "linux"), ("Darwin", "mac"), ("Windows", "windows")])
def test_default_backend_follows_operating_system(operating_system_name, expected_backend):
    assert detect_default_schedule_backend(operating_system_name) == expected_backend


@pytest.mark.parametrize("reminder_time_text, expected", [("22:00", (22, 0)), ("7:05", (7, 5))])
def test_valid_reminder_times_parse(reminder_time_text, expected):
    assert parse_reminder_time_to_hour_and_minute(reminder_time_text) == expected


@pytest.mark.parametrize("reminder_time_text", ["24:00", "22:60", "10pm", ""])
def test_invalid_reminder_times_are_rejected(reminder_time_text):
    with pytest.raises(ScheduleError):
        parse_reminder_time_to_hour_and_minute(reminder_time_text)


def test_systemd_timer_runs_at_requested_time():
    assert "OnCalendar=*-*-* 21:30:00" in build_systemd_timer_unit_text(21, 30)


def test_systemd_install_writes_units_and_enables_timer(tmp_path):
    command_runner = RecordingCommandRunner()
    install_daily_reminder_schedule("linux", "22:00", build_schedule_environment(tmp_path, command_runner))
    unit_directory = tmp_path / ".config" / "systemd" / "user"
    assert f"ExecStart={PYTHON_EXECUTABLE} -m footie --if-no-record-today" in (
        unit_directory / "footie-reminder.service").read_text()
    assert (unit_directory / "footie-reminder.timer").exists()
    assert ["systemctl", "--user", "enable", "--now", "footie-reminder.timer"] in [
        command for command, _ in command_runner.recorded_commands]

    remove_daily_reminder_schedule("linux", build_schedule_environment(tmp_path, command_runner))
    assert not (unit_directory / "footie-reminder.timer").exists()


def test_crontab_line_replaces_previous_reminder_and_keeps_other_jobs():
    existing_crontab_text = f"0 1 * * * backup\n0 22 * * * old {CRON_LINE_MARKER}\n"
    updated_crontab_text = build_crontab_text_with_reminder_line(existing_crontab_text, PYTHON_EXECUTABLE, 21, 30)
    assert updated_crontab_text == (
        f"0 1 * * * backup\n30 21 * * * DISPLAY=:0 {PYTHON_EXECUTABLE} -m footie --if-no-record-today {CRON_LINE_MARKER}\n"
    )
    assert remove_reminder_line_from_crontab_text(updated_crontab_text) == "0 1 * * * backup\n"


def test_cron_install_pipes_new_crontab(tmp_path):
    command_runner = RecordingCommandRunner({("crontab", "-l"): "0 1 * * * backup\n"})
    install_daily_reminder_schedule("linux-cron", "22:00", build_schedule_environment(tmp_path, command_runner))
    written_command, written_crontab_text = command_runner.recorded_commands[-1]
    assert written_command == ["crontab", "-"]
    assert written_crontab_text.startswith("0 1 * * * backup\n0 22 * * * DISPLAY=:0")


def test_launchd_plist_contains_program_and_time():
    plist_text = build_launchd_plist_text(PYTHON_EXECUTABLE, 22, 15)
    assert f"<string>{PYTHON_EXECUTABLE}</string>" in plist_text
    assert "<string>--if-no-record-today</string>" in plist_text
    assert "<key>Hour</key>\n        <integer>22</integer>" in plist_text
    assert "<key>Minute</key>\n        <integer>15</integer>" in plist_text


def test_mac_install_writes_plist_and_loads_it(tmp_path):
    command_runner = RecordingCommandRunner()
    install_daily_reminder_schedule("mac", "22:00", build_schedule_environment(tmp_path, command_runner))
    plist_path = tmp_path / "Library" / "LaunchAgents" / "com.footie.reminder.plist"
    assert plist_path.exists()
    assert command_runner.recorded_commands[-1][0] == ["launchctl", "load", "-w", str(plist_path)]


def test_windows_task_command_runs_daily_at_requested_time():
    assert build_windows_scheduled_task_create_command(r"C:\Python\python.exe", 22, 0) == [
        "schtasks", "/Create", "/F", "/SC", "DAILY", "/TN", "FootieDailyReminder", "/ST", "22:00",
        "/TR", r'"C:\Python\python.exe" -m footie --if-no-record-today',
    ]


def test_windows_install_and_remove_call_schtasks(tmp_path):
    command_runner = RecordingCommandRunner()
    schedule_environment = build_schedule_environment(tmp_path, command_runner)
    install_daily_reminder_schedule("windows", "22:00", schedule_environment)
    remove_daily_reminder_schedule("windows", schedule_environment)
    assert [command[:2] for command, _ in command_runner.recorded_commands] == [
        ["schtasks", "/Create"], ["schtasks", "/Delete"]]


def test_unknown_backend_is_rejected(tmp_path):
    with pytest.raises(ScheduleError):
        install_daily_reminder_schedule("amiga", "22:00", build_schedule_environment(tmp_path, RecordingCommandRunner()))


def test_failed_scheduler_command_raises(tmp_path):
    def failing_command_runner(command_arguments, **keyword_arguments):
        return subprocess.CompletedProcess(command_arguments, 1, stdout="", stderr="not allowed")

    with pytest.raises(ScheduleError, match="not allowed"):
        install_daily_reminder_schedule("windows", "22:00", build_schedule_environment(Path(tmp_path), failing_command_runner))
