import math
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

import pandas as pd
import joblib

# ---------------------------------------------------------
# Load the trained model bundle (keep the .pkl beside this file)
# ---------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movie_rating_model.pkl")

try:
    data = joblib.load(MODEL_PATH)
    model = data["model"]
    encoder = data["encoder"]
    feature_columns = data["feature_columns"]
except FileNotFoundError:
    raise SystemExit(
        "movie_rating_model.pkl was not found.\n"
        "Place it in the same folder as desktop_app.py."
    )

# ---------------------------------------------------------
# Theme
# ---------------------------------------------------------
BG = "#F7F7F5"          # page background
CARD = "#FFFFFF"        # light card
FIELD = "#FAFAF8"       # input background
INK = "#0F1115"         # primary text / dark surfaces
INK_HOVER = "#2A2E36"
MUTED = "#8A8F98"
SUBTLE = "#5B616B"
LINE = "#E8E8E4"
LINE_STRONG = "#D6D6D0"
CHIP_HOVER = "#F3F3F0"

DARK_TRACK = "#23262D"
DARK_MUTED = "#8A8F98"
GAUGE = "#A5B4FC"

MAX_CONTENT_WIDTH = 980
STACK_BREAKPOINT = 900   # below this width the result card moves under the form

root = tk.Tk()
root.title("CineRate")
root.configure(bg=BG)

# Size the window relative to the screen so it always fits, and let it resize
screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
win_w = min(1000, int(screen_w * 0.9))
win_h = min(780, int(screen_h * 0.85))
pos_x = (screen_w - win_w) // 2
pos_y = max(0, (screen_h - win_h) // 2 - 20)
root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
root.minsize(520, 480)

_available = set(tkfont.families())
FONT = next(
    (f for f in ("Inter", "SF Pro Display", "Segoe UI Variable", "Segoe UI", "Helvetica Neue", "Helvetica")
     if f in _available),
    "Helvetica",
)

def F(size, weight="normal"):
    return (FONT, size, weight)

# ---------------------------------------------------------
# Drawing helpers & custom widgets
# ---------------------------------------------------------
def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def card(parent, bg=CARD, border=LINE):
    """A flat card with a hairline border."""
    outer = tk.Frame(parent, bg=border)
    inner = tk.Frame(outer, bg=bg)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


class PillButton(tk.Canvas):
    """Rounded, flat button with hover + press feedback."""

    def __init__(self, parent, text, command, fill=INK, hover=INK_HOVER,
                 fg="#FFFFFF", height=52, radius=14, parent_bg=CARD):
        super().__init__(parent, height=height, bg=parent_bg,
                         highlightthickness=0, cursor="hand2")
        self._text, self._command = text, command
        self._fill, self._hover, self._fg, self._radius = fill, hover, fg, radius
        self._current = fill
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Enter>", lambda _e: self._set(self._hover))
        self.bind("<Leave>", lambda _e: self._set(self._fill))
        self.bind("<ButtonPress-1>", lambda _e: self._set(self._fill))
        self.bind("<ButtonRelease-1>", self._release)

    def _set(self, color):
        self._current = color
        self._draw()

    def _release(self, event):
        self._set(self._hover)
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self._command()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        round_rect(self, 1, 1, w - 1, h - 1, self._radius, fill=self._current, outline="")
        self.create_text(w / 2, h / 2, text=self._text, fill=self._fg, font=F(11, "bold"))


class Chip(tk.Canvas):
    """Toggleable pill used for genre selection."""

    HEIGHT = 34

    def __init__(self, parent, text, on_change):
        font = tkfont.Font(family=FONT, size=10)
        width = font.measure(text) + 32
        super().__init__(parent, width=width, height=self.HEIGHT, bg=CARD,
                         highlightthickness=0, cursor="hand2")
        self.text, self.selected, self._hovering = text, False, False
        self._on_change, self._cw = on_change, width
        self.bind("<Enter>", lambda _e: self._hover(True))
        self.bind("<Leave>", lambda _e: self._hover(False))
        self.bind("<Button-1>", lambda _e: self.toggle())
        self._draw()

    def _hover(self, state):
        self._hovering = state
        self._draw()

    def toggle(self):
        self.set(not self.selected)
        self._on_change()

    def set(self, value):
        self.selected = value
        self._draw()

    def _draw(self):
        self.delete("all")
        if self.selected:
            fill, outline, fg = INK, INK, "#FFFFFF"
        else:
            fill = CHIP_HOVER if self._hovering else CARD
            outline, fg = LINE_STRONG, SUBTLE
        round_rect(self, 1, 1, self._cw - 1, self.HEIGHT - 1, 16, fill=fill, outline=outline)
        self.create_text(self._cw / 2, self.HEIGHT / 2, text=self.text, fill=fg, font=F(10))


class Flow(tk.Frame):
    """Wraps child widgets onto new rows to fit the available width."""

    def __init__(self, parent, gap=8, bg=CARD):
        super().__init__(parent, bg=bg)
        self.items, self.gap, self._last_w = [], gap, 0
        self.bind("<Configure>", self._on_configure)

    def add(self, widget):
        self.items.append(widget)

    def _on_configure(self, event):
        if event.width != self._last_w:
            self._last_w = event.width
            self.arrange(event.width)

    def arrange(self, width):
        x = y = row_h = 0
        for w in self.items:
            iw, ih = int(w["width"]), int(w["height"])
            if x + iw > width and x > 0:
                x, y, row_h = 0, y + row_h + self.gap, 0
            w.place(x=x, y=y)
            x += iw + self.gap
            row_h = max(row_h, ih)
        self.configure(height=y + row_h)


def label(parent, text, size=10, color=INK, weight="normal", bg=CARD, **kw):
    return tk.Label(parent, text=text, font=F(size, weight), fg=color, bg=bg, **kw)

# ---------------------------------------------------------
# Scrollable page (fixes the "can't scroll to the result" problem)
# ---------------------------------------------------------
style = ttk.Style()
style.theme_use("clam")
style.layout("Minimal.Vertical.TScrollbar", [
    ("Vertical.Scrollbar.trough", {
        "sticky": "ns",
        "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],
    })
])
style.configure("Minimal.Vertical.TScrollbar", troughcolor=BG, background=LINE_STRONG,
                bordercolor=BG, lightcolor=LINE_STRONG, darkcolor=LINE_STRONG,
                gripcount=0, width=8)
style.map("Minimal.Vertical.TScrollbar", background=[("active", MUTED)])

shell = tk.Frame(root, bg=BG)
shell.pack(fill="both", expand=True)

canvas = tk.Canvas(shell, bg=BG, highlightthickness=0, yscrollincrement=24)
vbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview,
                     style="Minimal.Vertical.TScrollbar")
canvas.configure(yscrollcommand=vbar.set)
vbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

page = tk.Frame(canvas, bg=BG)
page.columnconfigure(0, weight=1)
page_window = canvas.create_window((0, 0), window=page, anchor="nw")

container = tk.Frame(page, bg=BG)
container.grid(row=0, column=0, sticky="ew", padx=40)

def _on_mousewheel(event):
    lo, hi = canvas.yview()
    if lo <= 0.0 and hi >= 1.0:
        return  # nothing to scroll
    if event.num == 4:
        step = -2
    elif event.num == 5:
        step = 2
    elif sys.platform == "darwin":
        step = -int(event.delta)
    else:
        step = -2 if event.delta > 0 else 2
    canvas.yview_scroll(step, "units")

root.bind_all("<MouseWheel>", _on_mousewheel)
root.bind_all("<Button-4>", _on_mousewheel)   # Linux
root.bind_all("<Button-5>", _on_mousewheel)

page.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
header = tk.Frame(container, bg=BG)
header.pack(fill="x", pady=(44, 30))

brand = tk.Frame(header, bg=BG)
brand.pack(anchor="w")
dot = tk.Canvas(brand, width=10, height=10, bg=BG, highlightthickness=0)
dot.create_oval(1, 1, 9, 9, fill=INK, outline="")
dot.pack(side="left", padx=(0, 8))
label(brand, "CineRate", 11, INK, "bold", BG).pack(side="left")

label(header, "Predict a movie's rating.", 30, INK, "bold", BG).pack(anchor="w", pady=(24, 6))
label(header, "A machine-learning estimate from genre, release year and runtime.",
      11, MUTED, "normal", BG).pack(anchor="w")

# ---------------------------------------------------------
# Two-column area (form + result)
# ---------------------------------------------------------
main = tk.Frame(container, bg=BG)
main.pack(fill="x")

# ---- Left: form card -------------------------------------
form_outer, form = card(main)
form_pad = tk.Frame(form, bg=CARD)
form_pad.pack(fill="both", expand=True, padx=30, pady=30)

label(form_pad, "Movie details", 16, INK, "bold").pack(anchor="w")
label(form_pad, "Choose one or more genres, then add the year and runtime.",
      10, MUTED).pack(anchor="w", pady=(4, 24))

genre_head = tk.Frame(form_pad, bg=CARD)
genre_head.pack(fill="x", pady=(0, 12))
label(genre_head, "GENRES", 9, SUBTLE, "bold").pack(side="left")
selected_count = label(genre_head, "None selected", 9, MUTED)
selected_count.pack(side="left", padx=(10, 0))
clear_btn = label(genre_head, "Clear", 9, SUBTLE, "bold")
clear_btn.configure(cursor="hand2")
clear_btn.pack(side="right")
clear_btn.bind("<Enter>", lambda _e: clear_btn.configure(fg=INK))
clear_btn.bind("<Leave>", lambda _e: clear_btn.configure(fg=SUBTLE))

chips = []

def on_genres_changed():
    n = sum(c.selected for c in chips)
    selected_count.configure(text=f"{n} selected" if n else "None selected")

def clear_genres(_event=None):
    for c in chips:
        c.set(False)
    on_genres_changed()

clear_btn.bind("<Button-1>", clear_genres)

flow = Flow(form_pad, gap=8)
flow.pack(fill="x")
for g in encoder.classes_:
    chip = Chip(flow, str(g), on_genres_changed)
    chips.append(chip)
    flow.add(chip)

# Numeric inputs
inputs = tk.Frame(form_pad, bg=CARD)
inputs.pack(fill="x", pady=(28, 0))
inputs.columnconfigure(0, weight=1, uniform="inp")
inputs.columnconfigure(1, weight=1, uniform="inp")

def create_input(title, default, suffix, column):
    wrap = tk.Frame(inputs, bg=CARD)
    wrap.grid(row=0, column=column, sticky="ew",
              padx=(0, 10) if column == 0 else (10, 0))
    label(wrap, title.upper(), 9, SUBTLE, "bold").pack(anchor="w", pady=(0, 8))

    box = tk.Frame(wrap, bg=FIELD, highlightthickness=1,
                   highlightbackground=LINE, highlightcolor=INK)
    box.pack(fill="x")
    entry = tk.Entry(box, font=F(12), bg=FIELD, fg=INK, relief="flat", bd=0,
                     insertbackground=INK, highlightthickness=0)
    entry.pack(side="left", fill="x", expand=True, padx=(14, 6), ipady=11)
    entry.insert(0, default)
    if suffix:
        label(box, suffix, 10, MUTED, bg=FIELD).pack(side="right", padx=(0, 14))

    entry.bind("<FocusIn>", lambda _e: box.configure(highlightbackground=INK))
    entry.bind("<FocusOut>", lambda _e: box.configure(highlightbackground=LINE))
    return entry

year_entry = create_input("Release year", "2022", None, 0)
runtime_entry = create_input("Runtime", "120", "min", 1)

predict_btn = PillButton(form_pad, "Predict rating", lambda: predict_rating())
predict_btn.pack(fill="x", pady=(28, 0))

# ---- Right: result card (dark) ---------------------------
result_outer, result = card(main, bg=INK, border=INK)
result_pad = tk.Frame(result, bg=INK)
result_pad.pack(fill="both", expand=True, padx=30, pady=30)

top = tk.Frame(result_pad, bg=INK)
top.pack(fill="x")
label(top, "PREDICTED RATING", 9, DARK_MUTED, "bold", INK).pack(side="left")
label(top, "OUT OF 10", 9, DARK_MUTED, "bold", INK).pack(side="right")

# Everything below the header is centred vertically inside the dark card
center = tk.Frame(result_pad, bg=INK)
center.pack(expand=True)

GAUGE_SIZE = 240
G_CX = G_CY = GAUGE_SIZE / 2
G_R = 92            # ring radius
G_W = 8             # ring thickness
CAP = G_W / 2       # radius of the rounded end-caps
RING_TRACK = "#2A2E36"

gauge = tk.Canvas(center, width=GAUGE_SIZE, height=GAUGE_SIZE, bg=INK, highlightthickness=0)
gauge.pack()
ring = (G_CX - G_R, G_CY - G_R, G_CX + G_R, G_CY + G_R)
gauge.create_oval(*ring, outline=RING_TRACK, width=G_W)
gauge.create_arc(*ring, start=90, extent=-1, style="arc", outline=GAUGE, width=G_W,
                 tags="prog", state="hidden")
gauge.create_oval(0, 0, 0, 0, fill=GAUGE, outline="", tags="cap_start", state="hidden")
gauge.create_oval(0, 0, 0, 0, fill=GAUGE, outline="", tags="cap_end", state="hidden")
gauge.create_text(G_CX, G_CY - 6, text="—", fill="#FFFFFF", font=F(46, "bold"), tags="val")
gauge.create_text(G_CX, G_CY + 36, text="/ 10", fill=DARK_MUTED, font=F(11))

def set_gauge(value):
    """Draw the ring for a score between 0 and 10 (starts at 12 o'clock, clockwise)."""
    value = max(0.0, min(value, 10.0))
    gauge.itemconfigure("val", text=f"{value:.1f}")
    sweep = min(359.9, 360 * value / 10)
    if sweep < 1:
        for tag in ("prog", "cap_start", "cap_end"):
            gauge.itemconfigure(tag, state="hidden")
        return
    theta = math.radians(90 - sweep)
    ex = G_CX + G_R * math.cos(theta)
    ey = G_CY - G_R * math.sin(theta)
    gauge.itemconfigure("prog", extent=-sweep, state="normal")
    gauge.coords("cap_start", G_CX - CAP, G_CY - G_R - CAP, G_CX + CAP, G_CY - G_R + CAP)
    gauge.coords("cap_end", ex - CAP, ey - CAP, ex + CAP, ey + CAP)
    gauge.itemconfigure("cap_start", state="normal")
    gauge.itemconfigure("cap_end", state="normal")

verdict = label(center, "Awaiting input", 15, "#FFFFFF", "bold", INK)
verdict.pack(pady=(8, 6))
result_hint = tk.Label(
    center, text="Select genres and press Predict\nto see your result.",
    font=F(10), fg=DARK_MUTED, bg=INK, wraplength=280, justify="center",
)
result_hint.pack()

# ---------------------------------------------------------
# Responsive column layout
# ---------------------------------------------------------
_layout_mode = {"stacked": None}

def layout_columns(width):
    stacked = width < STACK_BREAKPOINT
    if _layout_mode["stacked"] == stacked:
        return
    _layout_mode["stacked"] = stacked
    if stacked:
        main.columnconfigure(0, weight=1, uniform="")
        main.columnconfigure(1, weight=0, uniform="")
        form_outer.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        result_outer.grid(row=1, column=0, sticky="nsew", padx=0, pady=(20, 0))
    else:
        main.columnconfigure(0, weight=3, uniform="cols")
        main.columnconfigure(1, weight=2, uniform="cols")
        form_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        result_outer.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

def on_canvas_configure(event):
    canvas.itemconfigure(page_window, width=event.width)
    container.grid_configure(padx=max(24, (event.width - MAX_CONTENT_WIDTH) // 2))
    layout_columns(event.width)

canvas.bind("<Configure>", on_canvas_configure)

# ---------------------------------------------------------
# Result animation
# ---------------------------------------------------------
_anim = {"job": None, "value": 0.0}

def verdict_for(score):
    if score >= 7.5:
        return "Highly rated"
    if score >= 6.5:
        return "Well received"
    if score >= 5.0:
        return "Mixed reception"
    return "Below average"

def animate_to(target, steps=42):
    if _anim["job"] is not None:
        root.after_cancel(_anim["job"])
    start = _anim["value"]

    def tick(i):
        t = i / steps
        eased = 1 - (1 - t) ** 3
        value = start + (target - start) * eased
        set_gauge(value)
        _anim["value"] = value
        if i < steps:
            _anim["job"] = root.after(16, lambda: tick(i + 1))
        else:
            _anim["job"] = None

    tick(0)

# ---------------------------------------------------------
# Prediction
# ---------------------------------------------------------
def predict_rating():
    selected_genres = [c.text for c in chips if c.selected]

    if not selected_genres:
        messagebox.showwarning("Select a genre", "Please select at least one movie genre.")
        return

    try:
        year = int(year_entry.get().strip())
        runtime = int(runtime_entry.get().strip())
    except ValueError:
        messagebox.showerror("Check your inputs", "Year and runtime must be whole numbers.")
        return

    if not 1900 <= year <= 2035:
        messagebox.showerror("Invalid year", "Enter a year between 1900 and 2035.")
        return

    if not 30 <= runtime <= 300:
        messagebox.showerror("Invalid runtime", "Enter a runtime between 30 and 300 minutes.")
        return

    try:
        # Use the exact fitted encoder saved with the trained model
        genre_values = encoder.transform([selected_genres])

        # Match the exact training feature order
        input_data = pd.DataFrame(0, index=[0], columns=feature_columns)
        input_data["Year"] = year
        input_data["Runtime (Minutes)"] = runtime

        for i, genre in enumerate(encoder.classes_):
            if genre in feature_columns:
                input_data[genre] = genre_values[0][i]

        prediction = float(model.predict(input_data)[0])
        shown = max(0.0, min(prediction, 10.0))

        verdict.configure(text=verdict_for(shown))
        result_hint.configure(
            text=f"{' · '.join(selected_genres)}\n{year}  ·  {runtime} min"
        )
        animate_to(shown)

        # In the stacked (narrow) layout, bring the result into view
        if _layout_mode["stacked"]:
            root.update_idletasks()
            canvas.yview_moveto(1.0)

    except Exception as error:
        messagebox.showerror("Prediction error", f"Could not make a prediction:\n{error}")

root.bind("<Return>", lambda _e: predict_rating())

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
label(
    container,
    "CineRate uses a machine-learning model. This estimate is not an official IMDb rating.",
    9, MUTED, "normal", BG,
).pack(anchor="w", pady=(24, 36))

root.mainloop()
