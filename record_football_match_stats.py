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
STATS_FILE_PATH = REPO_DIRECTORY / "FOOTBALL_STATS.md"
STATS_FILE_TEMPLATE = (
    "# Football Stats\n"
    "\n"
    "Total Goals = 0 | Total Assists = 0\n"
    "\n"
    f"| {'Date':<{DATE_COLUMN_WIDTH}} | {'Goals':<{GOALS_COLUMN_WIDTH}} | {'Assists':<{ASSISTS_COLUMN_WIDTH}} |\n"
    f"| {'-' * DATE_COLUMN_WIDTH} | {'-' * GOALS_COLUMN_WIDTH} | {'-' * ASSISTS_COLUMN_WIDTH} |\n"
)
TOTALS_LINE_PATTERN = re.compile(r"^Total Goals = (\d+) \| Total Assists = (\d+)$")

ASSISTS_COLUMN_WIDTH = 7
def promptForMatchEntry():
    window = tk.Tk()
    window.title("Football stats")
    window.attributes("-topmost", True)
    enteredValues = {}

    tk.Label(window, text="Goals scored").grid(row=0, column=0, padx=8, pady=4)
    goalsField = tk.Entry(window, width=6)
    goalsField.grid(row=0, column=1, padx=8, pady=4)
    goalsField.insert(0, "0")
    goalsField.focus_set()

    tk.Label(window, text="Assists").grid(row=1, column=0, padx=8, pady=4)
    assistsField = tk.Entry(window, width=6)
    assistsField.grid(row=1, column=1, padx=8, pady=4)
    assistsField.insert(0, "0")

    def saveEnteredValuesAndCloseWindow():
        try:
            enteredValues["goals"] = int(goalsField.get())
            enteredValues["assists"] = int(assistsField.get())
        except ValueError:
            messagebox.showerror("Football stats", "Goals and assists must be whole numbers.")
            return
        window.destroy()

    tk.Button(window, text="Save", command=saveEnteredValuesAndCloseWindow).grid(row=2, column=0, pady=8)
    tk.Button(window, text="Didn't play", command=window.destroy).grid(row=2, column=1, pady=8)
    window.bind("<Return>", lambda event: saveEnteredValuesAndCloseWindow())
    window.mainloop()

    if not enteredValues:
        return None
    return (date.today().strftime(MATCH_DATE_FORMAT), enteredValues["goals"], enteredValues["assists"])


def createStatsFileWithHeaderIfMissing(statsFilePath):
    if not statsFilePath.exists():
        statsFilePath.write_text(STATS_FILE_TEMPLATE)


def appendMatchRowAndUpdateTotalsLine(statsFilePath, matchRow):
    createStatsFileWithHeaderIfMissing(statsFilePath)
    matchDate, goals, assists = matchRow

    with statsFilePath.open("a") as statsFile:
        statsFile.write(
            f"| {matchDate:<{DATE_COLUMN_WIDTH}} "
            f"| {goals:<{GOALS_COLUMN_WIDTH}} "
            f"| {assists:<{ASSISTS_COLUMN_WIDTH}} |\n"
        )

    statsFileLines = statsFilePath.read_text().splitlines()
    for lineIndex, line in enumerate(statsFileLines):
        matchedTotals = TOTALS_LINE_PATTERN.match(line)
        if matchedTotals:
            statsFileLines[lineIndex] = (
                f"Total Goals = {int(matchedTotals.group(1)) + goals} "
                f"| Total Assists = {int(matchedTotals.group(2)) + assists}"
            )
            break
    statsFilePath.write_text("\n".join(statsFileLines) + "\n")


def commitAndPushStatsFile(repoDirectory, statsFilePath):
    commitMessage = f"Record match stats for {date.today().strftime(MATCH_DATE_FORMAT)}"
    subprocess.run(["git", "add", statsFilePath.name], cwd=repoDirectory, check=True)
    subprocess.run(["git", "commit", "-m", commitMessage], cwd=repoDirectory, check=True)
    subprocess.run(["git", "push"], cwd=repoDirectory, check=True)


def main():
    matchRow = promptForMatchEntry()                                # 1. promptForMatchEntry()
    if matchRow is None:
        return
    appendMatchRowAndUpdateTotalsLine(STATS_FILE_PATH, matchRow)    # 3. appendMatchRowAndUpdateTotalsLine(statsFilePath, matchRow)
    commitAndPushStatsFile(REPO_DIRECTORY, STATS_FILE_PATH)         # 4. commitAndPushStatsFile(repoDirectory, statsFilePath)


if __name__ == "__main__":
    main()