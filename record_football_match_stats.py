import re
import subprocess
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox


REPO_DIRECTORY = Path(__file__).resolve().parent
MATCH_DATE_FORMAT = "%d %b %Y %A"
DATE_COLUMN_WIDTH = 21
GOALS_COLUMN_WIDTH = 5
ASSISTS_COLUMN_WIDTH = 7
STATS_FILE_PATH = REPO_DIRECTORY / "README.md"

STATS_FILE_TEMPLATE = (
    "# My Football Stats (Footy Addicts)\n"
    "\n"
    "*Auto-recorded after every match by a script in this repo.*\n"
    "\n"
    "Total Match Played = 0 | Total Goals = 0 | Total Assists = 0\n"
    "\n"
    f"| {'Date':<{DATE_COLUMN_WIDTH}} | {'Goals':<{GOALS_COLUMN_WIDTH}} | {'Assists':<{ASSISTS_COLUMN_WIDTH}} |\n"
    f"| {'-' * DATE_COLUMN_WIDTH} | {'-' * GOALS_COLUMN_WIDTH} | {'-' * ASSISTS_COLUMN_WIDTH} |\n"
)

TOTALS_LINE_PATTERN = re.compile(
    r"^Total Match Played = (\d+) \| Total Goals = (\d+) \| Total Assists = (\d+)$"
)

WINDOW_WIDTH_PIXELS = 1920
WINDOW_HEIGHT_PIXELS = 800
TITLE_FONT = ("Helvetica", 26, "bold")
LABEL_FONT = ("Helvetica", 20)
ENTRY_FONT = ("Helvetica", 24)
BUTTON_FONT = ("Helvetica", 18)


def prompt_for_match_entry():
    window = tk.Tk()
    window.title("Footy Addict")
    window.attributes("-topmost", True)
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)
    window.rowconfigure(0, weight=1)
    window.rowconfigure(1, weight=1)
    window.rowconfigure(2, weight=1)
    window.rowconfigure(3, weight=1)
    window.geometry(f"{WINDOW_WIDTH_PIXELS}x{WINDOW_HEIGHT_PIXELS}")
    window.minsize(WINDOW_WIDTH_PIXELS, WINDOW_HEIGHT_PIXELS)
    entered_values = {}

    tk.Label(window, text="YO ANY GOALS TODAY? OR YOU WERE BEING LAZY?", font=TITLE_FONT).grid(
        row=0, column=0, columnspan=2, padx=30, pady=(30, 10))

    tk.Label(window, text="Goals scored", font=LABEL_FONT).grid(row=1, column=0, padx=30, pady=12, sticky="e")
    goals_field = tk.Entry(window, width=5, font=ENTRY_FONT, justify="center")
    goals_field.grid(row=1, column=1, padx=30, pady=12, sticky="w")
    goals_field.insert(0, "0")
    goals_field.focus_set()
    goals_field.select_range(0, tk.END)

    tk.Label(window, text="Assists", font=LABEL_FONT).grid(row=2, column=0, padx=30, pady=12, sticky="e")
    assists_field = tk.Entry(window, width=5, font=ENTRY_FONT, justify="center")
    assists_field.grid(row=2, column=1, padx=30, pady=12, sticky="w")
    assists_field.insert(0, "0")

    def save_entered_values_and_close_window():
        try:
            entered_values["goals"] = int(goals_field.get())
            entered_values["assists"] = int(assists_field.get())
        except ValueError:
            messagebox.showerror("Football stats", "Goals and assists must be whole numbers.")
            return
        window.destroy()

    tk.Button(window, text="Save", font=BUTTON_FONT, width=14, height=2,
              command=save_entered_values_and_close_window).grid(row=3, column=0, padx=30, pady=(20, 35))
    tk.Button(window, text="Didn't play", font=BUTTON_FONT, width=14, height=2,
              command=window.destroy).grid(row=3, column=1, padx=30, pady=(20, 35))
    window.bind("<Return>", lambda event: save_entered_values_and_close_window())
    window.mainloop()

    if not entered_values:
        return None
    return (date.today().strftime(MATCH_DATE_FORMAT), entered_values["goals"], entered_values["assists"])


def create_stats_file_with_header_if_missing(stats_file_path):
    if not stats_file_path.exists():
        stats_file_path.write_text(STATS_FILE_TEMPLATE)


def append_match_row_and_update_totals_line(stats_file_path, match_row):
    create_stats_file_with_header_if_missing(stats_file_path)
    match_date, goals, assists = match_row

    with stats_file_path.open("a") as stats_file:
        stats_file.write(
            f"| {match_date:<{DATE_COLUMN_WIDTH}} "
            f"| {goals:<{GOALS_COLUMN_WIDTH}} "
            f"| {assists:<{ASSISTS_COLUMN_WIDTH}} |\n"
        )

    stats_file_lines = stats_file_path.read_text().splitlines()
    for line_index, line in enumerate(stats_file_lines):
        matched_totals = TOTALS_LINE_PATTERN.match(line)
        if matched_totals:
            stats_file_lines[line_index] = (
                f"Total Match Played = {int(matched_totals.group(1)) + 1} "
                f"| Total Goals = {int(matched_totals.group(2)) + goals} "
                f"| Total Assists = {int(matched_totals.group(3)) + assists}"
            )
            break
    else:
        raise ValueError(f"No totals line matching TOTALS_LINE_PATTERN found in {stats_file_path}")

    stats_file_path.write_text("\n".join(stats_file_lines) + "\n")


def commit_and_push_stats_file(repo_directory, stats_file_path):
    commit_message = f"Record match stats for {date.today().strftime(MATCH_DATE_FORMAT)}"
    subprocess.run(["git", "add", stats_file_path.name], cwd=repo_directory, check=True)
    subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_directory, check=True)
    subprocess.run(["git", "push"], cwd=repo_directory, check=True)


def main():
    match_row = prompt_for_match_entry()
    if match_row is None:
        return
    append_match_row_and_update_totals_line(STATS_FILE_PATH, match_row)
    commit_and_push_stats_file(REPO_DIRECTORY, STATS_FILE_PATH)


if __name__ == "__main__":
    main()
