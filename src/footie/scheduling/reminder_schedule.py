import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

SCHEDULE_BACKEND_LINUX_SYSTEMD = "linux"
SCHEDULE_BACKEND_LINUX_CRON = "linux-cron"
SCHEDULE_BACKEND_MAC = "mac"
SCHEDULE_BACKEND_WINDOWS = "windows"
SUPPORTED_SCHEDULE_BACKENDS = (
    SCHEDULE_BACKEND_LINUX_SYSTEMD,
    SCHEDULE_BACKEND_LINUX_CRON,
    SCHEDULE_BACKEND_MAC,
    SCHEDULE_BACKEND_WINDOWS,
)
DEFAULT_REMINDER_TIME = "22:00"

REMINDER_MODULE_ARGUMENTS = ("-m", "footie", "--if-no-record-today")
SYSTEMD_UNIT_NAME = "footie-reminder"
CRON_LINE_MARKER = "# footie-reminder"
LAUNCHD_LABEL = "com.footie.reminder"
WINDOWS_TASK_NAME = "FootieDailyReminder"


class ScheduleError(Exception):
    pass


@dataclass
class ScheduleEnvironment:
    home_directory: Path = field(default_factory=Path.home)
    python_executable: str = sys.executable
    run_command: object = subprocess.run


def detect_default_schedule_backend(operating_system_name=None):
    operating_system_name = operating_system_name or platform.system()
    if operating_system_name == "Darwin":
        return SCHEDULE_BACKEND_MAC
    if operating_system_name == "Windows":
        return SCHEDULE_BACKEND_WINDOWS
    return SCHEDULE_BACKEND_LINUX_SYSTEMD


def parse_reminder_time_to_hour_and_minute(reminder_time_text):
    matched_time = re.fullmatch(r"(\d{1,2}):(\d{2})", reminder_time_text.strip())
    if not matched_time:
        raise ScheduleError("Time must be in HH:MM 24-hour format, for example 22:00.")
    hour, minute = int(matched_time.group(1)), int(matched_time.group(2))
    if hour > 23 or minute > 59:
        raise ScheduleError("Time must be between 00:00 and 23:59.")
    return hour, minute


def run_scheduler_command_and_raise_on_failure(
    schedule_environment, command_arguments, input_text=None
):
    completed_process = schedule_environment.run_command(
        command_arguments, input=input_text, capture_output=True, text=True, check=False
    )
    if completed_process.returncode != 0:
        raise ScheduleError(
            f"{' '.join(command_arguments)} failed: {(completed_process.stderr or completed_process.stdout).strip()}"
        )
    return completed_process


def build_reminder_command_line(python_executable):
    return " ".join(
        [
            f'"{python_executable}"' if " " in python_executable else python_executable,
            *REMINDER_MODULE_ARGUMENTS,
        ]
    )


def resolve_systemd_user_unit_directory(home_directory):
    return Path(home_directory) / ".config" / "systemd" / "user"


def build_systemd_service_unit_text(python_executable):
    return (
        "[Unit]\n"
        "Description=Footie daily match stats reminder\n"
        "\n"
        "[Service]\n"
        "Type=oneshot\n"
        f"ExecStart={build_reminder_command_line(python_executable)}\n"
    )


def build_systemd_timer_unit_text(hour, minute):
    return (
        "[Unit]\n"
        "Description=Footie daily match stats reminder timer\n"
        "\n"
        "[Timer]\n"
        f"OnCalendar=*-*-* {hour:02d}:{minute:02d}:00\n"
        "Persistent=false\n"
        f"Unit={SYSTEMD_UNIT_NAME}.service\n"
        "\n"
        "[Install]\n"
        "WantedBy=timers.target\n"
    )


def install_systemd_timer_for_daily_reminder(schedule_environment, hour, minute):
    unit_directory = resolve_systemd_user_unit_directory(
        schedule_environment.home_directory
    )
    unit_directory.mkdir(parents=True, exist_ok=True)
    (unit_directory / f"{SYSTEMD_UNIT_NAME}.service").write_text(
        build_systemd_service_unit_text(schedule_environment.python_executable)
    )
    (unit_directory / f"{SYSTEMD_UNIT_NAME}.timer").write_text(
        build_systemd_timer_unit_text(hour, minute)
    )
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["systemctl", "--user", "daemon-reload"]
    )
    run_scheduler_command_and_raise_on_failure(
        schedule_environment,
        ["systemctl", "--user", "enable", "--now", f"{SYSTEMD_UNIT_NAME}.timer"],
    )
    return f"systemd user timer {SYSTEMD_UNIT_NAME}.timer in {unit_directory}"


def remove_systemd_timer_for_daily_reminder(schedule_environment):
    schedule_environment.run_command(
        ["systemctl", "--user", "disable", "--now", f"{SYSTEMD_UNIT_NAME}.timer"],
        capture_output=True,
        text=True,
        check=False,
    )
    unit_directory = resolve_systemd_user_unit_directory(
        schedule_environment.home_directory
    )
    for unit_suffix in ("service", "timer"):
        (unit_directory / f"{SYSTEMD_UNIT_NAME}.{unit_suffix}").unlink(missing_ok=True)
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["systemctl", "--user", "daemon-reload"]
    )
    return f"systemd user timer {SYSTEMD_UNIT_NAME}.timer"


def remove_reminder_line_from_crontab_text(existing_crontab_text):
    kept_lines = [
        line
        for line in existing_crontab_text.splitlines()
        if not line.rstrip().endswith(CRON_LINE_MARKER)
    ]
    return "\n".join(kept_lines) + ("\n" if kept_lines else "")


def build_crontab_text_with_reminder_line(
    existing_crontab_text, python_executable, hour, minute
):
    reminder_cron_line = f"{minute} {hour} * * * DISPLAY=:0 {build_reminder_command_line(python_executable)} {CRON_LINE_MARKER}"
    return (
        remove_reminder_line_from_crontab_text(existing_crontab_text)
        + reminder_cron_line
        + "\n"
    )


def read_current_crontab_text(schedule_environment):
    completed_process = schedule_environment.run_command(
        ["crontab", "-l"], capture_output=True, text=True, check=False
    )
    return completed_process.stdout if completed_process.returncode == 0 else ""


def install_cron_job_for_daily_reminder(schedule_environment, hour, minute):
    updated_crontab_text = build_crontab_text_with_reminder_line(
        read_current_crontab_text(schedule_environment),
        schedule_environment.python_executable,
        hour,
        minute,
    )
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["crontab", "-"], input_text=updated_crontab_text
    )
    return "crontab entry"


def remove_cron_job_for_daily_reminder(schedule_environment):
    updated_crontab_text = remove_reminder_line_from_crontab_text(
        read_current_crontab_text(schedule_environment)
    )
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["crontab", "-"], input_text=updated_crontab_text
    )
    return "crontab entry"


def resolve_launchd_plist_path(home_directory):
    return Path(home_directory) / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def build_launchd_plist_text(python_executable, hour, minute):
    program_argument_lines = "\n".join(
        f"        <string>{escape(argument)}</string>"
        for argument in (python_executable, *REMINDER_MODULE_ARGUMENTS)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{LAUNCHD_LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{program_argument_lines}\n"
        "    </array>\n"
        "    <key>StartCalendarInterval</key>\n"
        "    <dict>\n"
        "        <key>Hour</key>\n"
        f"        <integer>{hour}</integer>\n"
        "        <key>Minute</key>\n"
        f"        <integer>{minute}</integer>\n"
        "    </dict>\n"
        "</dict>\n"
        "</plist>\n"
    )


def install_launchd_agent_for_daily_reminder(schedule_environment, hour, minute):
    plist_path = resolve_launchd_plist_path(schedule_environment.home_directory)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    schedule_environment.run_command(
        ["launchctl", "unload", str(plist_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    plist_path.write_text(
        build_launchd_plist_text(schedule_environment.python_executable, hour, minute)
    )
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["launchctl", "load", "-w", str(plist_path)]
    )
    return f"launchd agent {plist_path}"


def remove_launchd_agent_for_daily_reminder(schedule_environment):
    plist_path = resolve_launchd_plist_path(schedule_environment.home_directory)
    schedule_environment.run_command(
        ["launchctl", "unload", "-w", str(plist_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    plist_path.unlink(missing_ok=True)
    return f"launchd agent {plist_path}"


def resolve_windowless_python_executable(python_executable):
    python_executable_path = Path(python_executable)
    windowless_python_path = python_executable_path.with_name("pythonw.exe")
    return (
        str(windowless_python_path)
        if windowless_python_path.exists()
        else python_executable
    )


def build_windows_scheduled_task_create_command(python_executable, hour, minute):
    task_command_line = " ".join([f'"{python_executable}"', *REMINDER_MODULE_ARGUMENTS])
    return [
        "schtasks",
        "/Create",
        "/F",
        "/SC",
        "DAILY",
        "/TN",
        WINDOWS_TASK_NAME,
        "/ST",
        f"{hour:02d}:{minute:02d}",
        "/TR",
        task_command_line,
    ]


def install_windows_scheduled_task_for_daily_reminder(
    schedule_environment, hour, minute
):
    run_scheduler_command_and_raise_on_failure(
        schedule_environment,
        build_windows_scheduled_task_create_command(
            resolve_windowless_python_executable(
                schedule_environment.python_executable
            ),
            hour,
            minute,
        ),
    )
    return f"Windows scheduled task {WINDOWS_TASK_NAME}"


def remove_windows_scheduled_task_for_daily_reminder(schedule_environment):
    run_scheduler_command_and_raise_on_failure(
        schedule_environment, ["schtasks", "/Delete", "/F", "/TN", WINDOWS_TASK_NAME]
    )
    return f"Windows scheduled task {WINDOWS_TASK_NAME}"


SCHEDULE_INSTALLERS_BY_BACKEND = {
    SCHEDULE_BACKEND_LINUX_SYSTEMD: install_systemd_timer_for_daily_reminder,
    SCHEDULE_BACKEND_LINUX_CRON: install_cron_job_for_daily_reminder,
    SCHEDULE_BACKEND_MAC: install_launchd_agent_for_daily_reminder,
    SCHEDULE_BACKEND_WINDOWS: install_windows_scheduled_task_for_daily_reminder,
}

SCHEDULE_REMOVERS_BY_BACKEND = {
    SCHEDULE_BACKEND_LINUX_SYSTEMD: remove_systemd_timer_for_daily_reminder,
    SCHEDULE_BACKEND_LINUX_CRON: remove_cron_job_for_daily_reminder,
    SCHEDULE_BACKEND_MAC: remove_launchd_agent_for_daily_reminder,
    SCHEDULE_BACKEND_WINDOWS: remove_windows_scheduled_task_for_daily_reminder,
}


def install_daily_reminder_schedule(
    schedule_backend, reminder_time_text, schedule_environment=None
):
    if schedule_backend not in SCHEDULE_INSTALLERS_BY_BACKEND:
        raise ScheduleError(f"Unknown schedule backend {schedule_backend!r}")
    hour, minute = parse_reminder_time_to_hour_and_minute(reminder_time_text)
    return SCHEDULE_INSTALLERS_BY_BACKEND[schedule_backend](
        schedule_environment or ScheduleEnvironment(), hour, minute
    )


def remove_daily_reminder_schedule(schedule_backend, schedule_environment=None):
    if schedule_backend not in SCHEDULE_REMOVERS_BY_BACKEND:
        raise ScheduleError(f"Unknown schedule backend {schedule_backend!r}")
    return SCHEDULE_REMOVERS_BY_BACKEND[schedule_backend](
        schedule_environment or ScheduleEnvironment()
    )
