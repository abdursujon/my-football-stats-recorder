import math
import tkinter as tk
from datetime import date
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from footie.validation.match_validation import UK_DATE_FORMAT_HINT, format_match_date_as_uk

WINDOW_TITLE = "Footie"
PROMPT_TEXT = "YO ANY GOALS TODAY?"
BASE_FONT_SIZE = 11
CONTENT_MARGIN_PIXELS = 50
ROW_SPACING = 8
LABEL_COLUMN_GAP = 24
FOOTBALL_ICON_SIZE = 30
PREFERRED_SERIF_FONT_FAMILIES = ("Georgia", "DejaVu Serif", "Liberation Serif", "Noto Serif", "Times New Roman")

PAPER_BACKGROUND_COLOUR = "#efe4cc"
CARD_BACKGROUND_COLOUR = "#f8f1e0"
CARD_BORDER_COLOUR = "#6b5338"
FIELD_BACKGROUND_COLOUR = "#fffaf0"
FIELD_BORDER_COLOUR = "#b39b78"
INK_TEXT_COLOUR = "#2b2118"
FADED_INK_TEXT_COLOUR = "#6b5338"
PITCH_GREEN_COLOUR = "#2f5233"
PITCH_GREEN_HOVER_COLOUR = "#3c6a42"
BUTTON_HOVER_COLOUR = "#eadcbd"
FOOTBALL_LIGHT_PANEL_COLOUR = "#fffaf0"
FOOTBALL_DARK_PANEL_COLOUR = "#2b2118"


def choose_available_serif_font_family():
    installed_font_families = set(tkfont.families())
    for font_family in PREFERRED_SERIF_FONT_FAMILIES:
        if font_family in installed_font_families:
            return font_family
    return "Times"


def create_consistent_vintage_fonts(window):
    serif_font_family = choose_available_serif_font_family()
    for named_font in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        tkfont.nametofont(named_font).configure(family=serif_font_family, size=BASE_FONT_SIZE)
    base_font = tkfont.nametofont("TkDefaultFont")
    title_font = tkfont.Font(window, family=serif_font_family, size=BASE_FONT_SIZE + 5, weight="bold")
    return base_font, title_font


def apply_vintage_theme_styles(window, base_font, title_font):
    window_style = ttk.Style(window)
    window_style.theme_use("clam")
    window.configure(background=PAPER_BACKGROUND_COLOUR)

    window_style.configure(".", background=CARD_BACKGROUND_COLOUR, foreground=INK_TEXT_COLOUR, font=base_font)
    window_style.configure("Paper.TFrame", background=PAPER_BACKGROUND_COLOUR)
    window_style.configure("Card.TFrame", background=CARD_BACKGROUND_COLOUR, bordercolor=CARD_BORDER_COLOUR,
                           relief="solid", borderwidth=2)
    window_style.configure("TFrame", background=CARD_BACKGROUND_COLOUR)
    window_style.configure("TLabel", background=CARD_BACKGROUND_COLOUR, foreground=FADED_INK_TEXT_COLOUR)
    window_style.configure("Title.TLabel", foreground=PITCH_GREEN_COLOUR, font=title_font)

    field_options = dict(
        fieldbackground=FIELD_BACKGROUND_COLOUR, foreground=INK_TEXT_COLOUR,
        bordercolor=FIELD_BORDER_COLOUR, lightcolor=FIELD_BACKGROUND_COLOUR, darkcolor=FIELD_BACKGROUND_COLOUR,
        insertcolor=INK_TEXT_COLOUR, selectbackground=PITCH_GREEN_COLOUR,
        selectforeground=CARD_BACKGROUND_COLOUR, padding=6,
    )
    focused_border_map = dict(bordercolor=[("focus", PITCH_GREEN_COLOUR)])
    window_style.configure("TEntry", **field_options)
    window_style.map("TEntry", **focused_border_map)
    window_style.configure("TCombobox", **field_options, background=FIELD_BACKGROUND_COLOUR,
                           arrowcolor=FADED_INK_TEXT_COLOUR)
    window_style.map("TCombobox", **focused_border_map,
                     fieldbackground=[("readonly", FIELD_BACKGROUND_COLOUR)],
                     background=[("active", BUTTON_HOVER_COLOUR)],
                     arrowcolor=[("active", INK_TEXT_COLOUR)])
    window.option_add("*TCombobox*Listbox.background", FIELD_BACKGROUND_COLOUR)
    window.option_add("*TCombobox*Listbox.foreground", INK_TEXT_COLOUR)
    window.option_add("*TCombobox*Listbox.selectBackground", PITCH_GREEN_COLOUR)
    window.option_add("*TCombobox*Listbox.selectForeground", CARD_BACKGROUND_COLOUR)
    window.option_add("*TCombobox*Listbox.font", base_font)

    button_options = dict(font=base_font, padding=(20, 7), borderwidth=2, focusthickness=0)
    window_style.configure("TButton", **button_options, background=CARD_BACKGROUND_COLOUR,
                           foreground=FADED_INK_TEXT_COLOUR, bordercolor=CARD_BORDER_COLOUR,
                           lightcolor=CARD_BACKGROUND_COLOUR, darkcolor=CARD_BACKGROUND_COLOUR)
    window_style.map("TButton", background=[("active", BUTTON_HOVER_COLOUR)],
                     lightcolor=[("active", BUTTON_HOVER_COLOUR)], darkcolor=[("active", BUTTON_HOVER_COLOUR)])
    window_style.configure("Accent.TButton", **button_options, background=PITCH_GREEN_COLOUR,
                           foreground=CARD_BACKGROUND_COLOUR, bordercolor=PITCH_GREEN_COLOUR,
                           lightcolor=PITCH_GREEN_COLOUR, darkcolor=PITCH_GREEN_COLOUR)
    window_style.map("Accent.TButton", background=[("active", PITCH_GREEN_HOVER_COLOUR)],
                     lightcolor=[("active", PITCH_GREEN_HOVER_COLOUR)],
                     darkcolor=[("active", PITCH_GREEN_HOVER_COLOUR)])


def calculate_pentagon_corner_points(centre_x, centre_y, corner_radius, rotation_degrees):
    corner_points = []
    for corner_index in range(5):
        corner_angle = math.radians(rotation_degrees + corner_index * 72)
        corner_points.append((centre_x + corner_radius * math.cos(corner_angle),
                              centre_y + corner_radius * math.sin(corner_angle)))
    return corner_points


def create_panelled_football_icon(parent_widget, icon_size=FOOTBALL_ICON_SIZE):
    football_canvas = tk.Canvas(parent_widget, width=icon_size, height=icon_size, highlightthickness=0,
                                background=CARD_BACKGROUND_COLOUR)
    centre = icon_size / 2
    ball_radius = icon_size / 2 - 2
    football_canvas.create_oval(centre - ball_radius, centre - ball_radius, centre + ball_radius,
                                centre + ball_radius, fill=FOOTBALL_LIGHT_PANEL_COLOUR, outline="")

    pointing_up_degrees = -90
    centre_pentagon_corners = calculate_pentagon_corner_points(centre, centre, ball_radius * 0.36,
                                                               pointing_up_degrees)
    football_canvas.create_polygon(centre_pentagon_corners, fill=FOOTBALL_DARK_PANEL_COLOUR,
                                   outline=FOOTBALL_DARK_PANEL_COLOUR)

    for corner_index, (corner_x, corner_y) in enumerate(centre_pentagon_corners):
        outward_angle = math.radians(pointing_up_degrees + corner_index * 72)
        edge_pentagon_centre_x = centre + ball_radius * 1.02 * math.cos(outward_angle)
        edge_pentagon_centre_y = centre + ball_radius * 1.02 * math.sin(outward_angle)
        edge_pentagon_corners = calculate_pentagon_corner_points(
            edge_pentagon_centre_x, edge_pentagon_centre_y, ball_radius * 0.36,
            pointing_up_degrees + corner_index * 72 + 180,
        )
        football_canvas.create_polygon(edge_pentagon_corners, fill=FOOTBALL_DARK_PANEL_COLOUR,
                                       outline=FOOTBALL_DARK_PANEL_COLOUR)
        football_canvas.create_line(corner_x, corner_y, *edge_pentagon_corners[0],
                                    fill=FOOTBALL_DARK_PANEL_COLOUR, width=max(1, icon_size // 24))

    outside_mask_width = icon_size
    football_canvas.create_oval(centre - ball_radius - outside_mask_width / 2,
                                centre - ball_radius - outside_mask_width / 2,
                                centre + ball_radius + outside_mask_width / 2,
                                centre + ball_radius + outside_mask_width / 2,
                                outline=CARD_BACKGROUND_COLOUR, width=outside_mask_width)
    football_canvas.create_oval(centre - ball_radius, centre - ball_radius, centre + ball_radius,
                                centre + ball_radius, outline=FOOTBALL_DARK_PANEL_COLOUR,
                                width=max(2, icon_size // 18))
    return football_canvas


def centre_window_on_screen(window):
    window.update_idletasks()
    window_width, window_height = window.winfo_reqwidth(), window.winfo_reqheight()
    horizontal_offset = (window.winfo_screenwidth() - window_width) // 2
    vertical_offset = (window.winfo_screenheight() - window_height) // 3
    window.geometry(f"+{horizontal_offset}+{vertical_offset}")


def prompt_for_match_entry_in_window(known_venues, default_venue, build_match_record, default_match_date=None):
    window = tk.Tk()
    window.title(WINDOW_TITLE)
    window.attributes("-topmost", True)
    window.resizable(False, False)
    base_font, title_font = create_consistent_vintage_fonts(window)
    apply_vintage_theme_styles(window, base_font, title_font)

    paper_frame = ttk.Frame(window, style="Paper.TFrame", padding=CONTENT_MARGIN_PIXELS // 2)
    paper_frame.grid(row=0, column=0, sticky="nsew")
    card_frame = ttk.Frame(paper_frame, style="Card.TFrame", padding=CONTENT_MARGIN_PIXELS)
    card_frame.grid(row=0, column=0, sticky="nsew")
    card_frame.columnconfigure(1, weight=1)

    entered_match_record = {}

    title_row = ttk.Frame(card_frame)
    title_row.grid(row=0, column=0, columnspan=2, pady=(0, CONTENT_MARGIN_PIXELS // 2))
    football_icon_size = int(title_font.metrics("linespace") * 1.2)
    create_panelled_football_icon(title_row, football_icon_size).grid(row=0, column=0, padx=(0, 16))
    ttk.Label(title_row, text=PROMPT_TEXT, style="Title.TLabel").grid(row=0, column=1)
    create_panelled_football_icon(title_row, football_icon_size).grid(row=0, column=2, padx=(16, 0))

    ttk.Label(card_frame, text=f"Date ({UK_DATE_FORMAT_HINT})").grid(
        row=1, column=0, sticky="w", padx=(0, LABEL_COLUMN_GAP), pady=ROW_SPACING)
    date_field = ttk.Entry(card_frame, width=12)
    date_field.grid(row=1, column=1, sticky="w", pady=ROW_SPACING)
    date_field.insert(0, format_match_date_as_uk(default_match_date or date.today()))

    ttk.Label(card_frame, text="Venue").grid(
        row=2, column=0, sticky="w", padx=(0, LABEL_COLUMN_GAP), pady=ROW_SPACING)
    venue_field = ttk.Combobox(card_frame, values=list(known_venues), width=34)
    venue_field.grid(row=2, column=1, sticky="ew", pady=ROW_SPACING)
    venue_field.set(default_venue or "")

    ttk.Label(card_frame, text="Goals scored").grid(
        row=3, column=0, sticky="w", padx=(0, LABEL_COLUMN_GAP), pady=ROW_SPACING)
    goals_field = ttk.Entry(card_frame, width=5, justify="center")
    goals_field.grid(row=3, column=1, sticky="w", pady=ROW_SPACING)
    goals_field.insert(0, "0")

    ttk.Label(card_frame, text="Assists").grid(
        row=4, column=0, sticky="w", padx=(0, LABEL_COLUMN_GAP), pady=ROW_SPACING)
    assists_field = ttk.Entry(card_frame, width=5, justify="center")
    assists_field.grid(row=4, column=1, sticky="w", pady=ROW_SPACING)
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

    button_row = ttk.Frame(card_frame)
    button_row.grid(row=5, column=0, columnspan=2, pady=(CONTENT_MARGIN_PIXELS // 2, 0))
    ttk.Button(button_row, text="Didn't play", command=window.destroy).grid(row=0, column=0, padx=(0, 12))
    ttk.Button(button_row, text="Save", style="Accent.TButton",
               command=validate_entered_values_and_close_window).grid(row=0, column=1)

    window.bind("<Return>", lambda _event: validate_entered_values_and_close_window())
    window.bind("<Escape>", lambda _event: window.destroy())
    centre_window_on_screen(window)
    window.mainloop()

    return entered_match_record.get("record")
