import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from footie.validation.match_validation import UK_DATE_FORMAT_HINT, format_match_date_as_uk

WINDOW_TITLE = "Footie"
WINDOW_WIDTH_PIXELS = 1200
WINDOW_HEIGHT_PIXELS = 700
TITLE_FONT = ("Helvetica", 26, "bold")
LABEL_FONT = ("Helvetica", 20)
ENTRY_FONT = ("Helvetica", 22)
BUTTON_FONT = ("Helvetica", 18)
PROMPT_TEXT = "YO ANY GOALS TODAY? OR YOU WERE BEING LAZY?"


def prompt_for_match_entry_in_window(known_venues, default_venue, build_match_record, default_match_date=None):
    window = tk.Tk()
    window.title(WINDOW_TITLE)
    window.attributes("-topmost", True)
    window.geometry(f"{WINDOW_WIDTH_PIXELS}x{WINDOW_HEIGHT_PIXELS}")
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)
    for row_index in range(6):
        window.rowconfigure(row_index, weight=1)
    window.option_add("*TCombobox*Listbox.font", ENTRY_FONT)

    entered_match_record = {}

    tk.Label(window, text=PROMPT_TEXT, font=TITLE_FONT).grid(
        row=0, column=0, columnspan=2, padx=30, pady=(30, 10))

    tk.Label(window, text=f"Date ({UK_DATE_FORMAT_HINT})", font=LABEL_FONT).grid(
        row=1, column=0, padx=30, pady=12, sticky="e")
    date_field = tk.Entry(window, width=12, font=ENTRY_FONT, justify="center")
    date_field.grid(row=1, column=1, padx=30, pady=12, sticky="w")
    date_field.insert(0, format_match_date_as_uk(default_match_date or date.today()))

    tk.Label(window, text="Venue", font=LABEL_FONT).grid(row=2, column=0, padx=30, pady=12, sticky="e")
    venue_field = ttk.Combobox(window, values=list(known_venues), width=36, font=ENTRY_FONT)
    venue_field.grid(row=2, column=1, padx=30, pady=12, sticky="w")
    venue_field.set(default_venue or "")

    tk.Label(window, text="Goals scored", font=LABEL_FONT).grid(row=3, column=0, padx=30, pady=12, sticky="e")
    goals_field = tk.Entry(window, width=5, font=ENTRY_FONT, justify="center")
    goals_field.grid(row=3, column=1, padx=30, pady=12, sticky="w")
    goals_field.insert(0, "0")

    tk.Label(window, text="Assists", font=LABEL_FONT).grid(row=4, column=0, padx=30, pady=12, sticky="e")
    assists_field = tk.Entry(window, width=5, font=ENTRY_FONT, justify="center")
    assists_field.grid(row=4, column=1, padx=30, pady=12, sticky="w")
    assists_field.insert(0, "0")

    goals_field.focus_set()
    goals_field.select_range(0, tk.END)

    def validate_entered_values_and_close_window():
        try:
            entered_match_record["record"] = build_match_record(
                date_field.get(), venue_field.get(), goals_field.get(), assists_field.get()
            )
        except ValueError as validation_error:
            messagebox.showerror(WINDOW_TITLE, str(validation_error), parent=window)
            return
        window.destroy()

    tk.Button(window, text="Save", font=BUTTON_FONT, width=14, height=2,
              command=validate_entered_values_and_close_window).grid(row=5, column=0, padx=30, pady=(20, 35))
    tk.Button(window, text="Didn't play", font=BUTTON_FONT, width=14, height=2,
              command=window.destroy).grid(row=5, column=1, padx=30, pady=(20, 35))
    window.bind("<Return>", lambda event: validate_entered_values_and_close_window())
    window.bind("<Escape>", lambda event: window.destroy())
    window.mainloop()

    return entered_match_record.get("record")
