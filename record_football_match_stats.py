"""
The script has four function doing a specific task.
1. promptForMatchEntry(): This shows th prompt dialogue, where we can entry our desired result 
2. readExistingMatchRows(statsFilePath): Read match record so we can count total assists and goals 
3. appendMatchRowAndRewriteTotals(statsFilePath, matchRow): rewrite entries when new data entry detected 
4. commitAndPushStatsFile(repoDirectory, statsFilePath): automate the git push 
"""

import re
import subprocess
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox


REPO_DIRECTORY = Path(__file__).resolve().parent
STATS_FILE_PATH = REPO_DIRECTORY / "STATS.md"
STATS_FILE_TEMPLATE = (
    "# Football Stats\n"
    "\n"
    "Total Goals = 0 | Total Assists = 0\n"
    "\n"
    "| Date | Goals | Assists |\n"
    "| --- | --- | --- |\n"
)
TOTALS_LINE_PATTERN = re.compile(r"^Total Goals = (\d+) \| Total Assists = (\d+)$")


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
    return (date.today().isoformat(), enteredValues["goals"], enteredValues["assists"])


def createStatsFileWithHeaderIfMissing(statsFilePath):
    if not statsFilePath.exists():
        statsFilePath.write_text(STATS_FILE_TEMPLATE)


def appendMatchRowAndUpdateTotalsLine(statsFilePath, matchRow):
    createStatsFileWithHeaderIfMissing(statsFilePath)
    matchDate, goals, assists = matchRow

    with statsFilePath.open("a") as statsFile:
        statsFile.write(f"| {matchDate} | {goals} | {assists} |\n")

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
    commitMessage = f"Record match stats for {date.today().isoformat()}"
    subprocess.run(["git", "push"], cwd=repoDirectory, check=True)


def main():
    matchRow = promptForMatchEntry()                                # 1. promptForMatchEntry()
    if matchRow is None:
        return
    appendMatchRowAndUpdateTotalsLine(STATS_FILE_PATH, matchRow)    # 3. appendMatchRowAndUpdateTotalsLine(statsFilePath, matchRow)
    commitAndPushStatsFile(REPO_DIRECTORY, STATS_FILE_PATH)         # 4. commitAndPushStatsFile(repoDirectory, statsFilePath)


if __name__ == "__main__":
    main()