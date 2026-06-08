import tkinter as tk

from PIL import Image, ImageTk
import random


# ---------------------------------------------------------------------------
# Mission data
# ---------------------------------------------------------------------------

_OBJECTS = [
    ("Atom",           "images/atom.png",          5e-11),
    ("Vattenmolekyl",  "images/vattenmolekyl.png", 2.7e-10),
    ("DNA",            "images/dna.png",            3e-9),
    ("Virus",          "images/virus.png",          2e-8),
    ("Tarmbakterie",   "images/tarmbakterie.png",   1e-6),
    ("Cell",           "images/cell.png",           5e-5),
    ("Mänskligt hår",  "images/hår.png",            1e-4),
    ("Katt",           "images/katt.png",           0.3),
    ("Astronaut",      "images/astronaut.png",      1.7),
    ("Teleskop",       "images/teleskop.png",       13.0),
    ("Blåval",         "images/val.png",            30.0),
    ("Pyramid",        "images/pyramid.png",        137.0),
    ("Mars",           "images/mars.png",           7e6),
    ("Jorden",         "images/jorden.png",         1.3e7),
    ("Vintergatan",    "images/vintergatan.png",    8.7e7),
    ("Saturnus",       "images/saturnus.png",       1.2e8),
    ("Jupiter",        "images/jupiter.png",        1.4e8),
    ("Solen",          "images/solen.png",          1.4e9),
    ("Röd jätte",      "images/röd jätte.png",      3.5e10),
    ("Svart hål",      "images/svart hål.png",      5.2e10),
    ("Cassiopeia A",   "images/cassiopeia.png",     9.461e16),
    ("Krabbnebulosa",  "images/krabbnebula.png",    1.04e17),
    ("Herkules",       "images/herkules.png",       9.461e26),
]
_OBJECTS.sort(key=lambda o: o[2])

_FORBIDDEN = [
    {"Astronaut",   "Atom"},
    {"Blåval",      "Cassiopeia A"},
    {"Katt",        "Jupiter"},
    {"Mars",        "Pyramid"},
    {"Saturnus",    "Röd jätte"},
    {"Tarmbakterie","Teleskop"},
    {"Vintergatan", "Virus"},
]

_DIFF_IMAGE = {
    "easy":   "images/blå knapp.png",
    "medium": "images/röd knapp.png",
    "hard":   "images/svart knapp.png",
}


def _mission_valid(picks):
    names = {o[0] for o in picks}
    return not any(fp.issubset(names) for fp in _FORBIDDEN)


def generate_mission(difficulty: str) -> list:
    n = len(_OBJECTS)
    for _ in range(2000):
        if difficulty == "easy":
            g = n // 5
            picks = [
                random.choice(_OBJECTS[i * g : (i + 1) * g if i < 4 else n])
                for i in range(5)
            ]
        elif difficulty == "medium":
            t = n // 3
            spread = [
                random.choice(_OBJECTS[:t]),
                random.choice(_OBJECTS[t : 2 * t]),
                random.choice(_OBJECTS[2 * t :]),
            ]
            used = {o[0] for o in spread}
            ws = random.randint(0, n - 5)
            pool = [o for o in _OBJECTS[ws : ws + 5] if o[0] not in used]
            if len(pool) < 2:
                continue
            picks = spread + random.sample(pool, 2)
        else:  # hard
            ws = random.randint(0, n - 8)
            picks = random.sample(_OBJECTS[ws : ws + 8], 5)

        if _mission_valid(picks):
            return sorted([o[0] for o in picks])

    return sorted([_OBJECTS[i][0] for i in range(0, n, n // 5)][:5])


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSO")
        self.configure(bg="#1e1e2e")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        img = Image.open("images/background.png").resize((sw, sh), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(img)

        self.difficulty = "medium"

        self.container = tk.Frame(self, bg="#1e1e2e")
        self.container.pack(fill="both", expand=True)

        self.pages = [WelcomePage, DifficultyPage, PlaceholderPage]
        self.page_index = 0
        self.current_page = None
        self.show_page(WelcomePage)

        self.bind("<Left>",  lambda e: self.go_prev())
        self.bind("<Right>", lambda e: self.go_next())
        self.bind("1", lambda e: self.show_page(WelcomePage))
        self.bind("2", lambda e: self.show_page(DifficultyPage))
        self.bind("3", lambda e: self.show_page(PlaceholderPage))

    def show_page(self, page_class):
        if self.current_page is not None:
            self.current_page.destroy()
        self.page_index = self.pages.index(page_class)
        self.current_page = page_class(self.container, self)
        self.current_page.pack(fill="both", expand=True)

    def go_prev(self):
        self.show_page(self.pages[(self.page_index - 1) % len(self.pages)])

    def go_next(self):
        self.show_page(self.pages[(self.page_index + 1) % len(self.pages)])


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        canvas.create_text(
            sw // 2, int(sh * 0.33),
            text="Utforska din kunskap om storlekar!",
            font=("OpenDyslexic", 54, "bold"),
            fill="white",
            anchor="center",
        )

        canvas.create_text(
            sw // 2, int(sh * 0.42),
            text="Tryck på START-knappen för att påbörja ditt äventyr",
            font=("OpenDyslexic", 26),
            fill="white",
            anchor="center",
        )

        btn_size = 220
        btn_y = int(sh * 0.65)
        img = Image.open("images/röd knapp.png").convert("RGBA").resize(
            (btn_size, btn_size), Image.LANCZOS
        )
        self._photo = ImageTk.PhotoImage(img)

        def go_p2(*_):
            controller.show_page(DifficultyPage)

        item = canvas.create_image(sw // 2, btn_y, anchor="center", image=self._photo)
        canvas.tag_bind(item, "<Button-1>", go_p2)
        canvas.tag_bind(item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(item, "<Leave>", lambda *_: canvas.config(cursor=""))

        canvas.create_text(
            sw // 2, btn_y + btn_size // 2 + 28,
            text="START",
            font=("OpenDyslexic", 36),
            fill="white",
            anchor="center",
        )

        controller.bind("9", go_p2)

        def on_destroy(_e):
            if _e.widget is self:
                controller.unbind("9")

        self.bind("<Destroy>", on_destroy)


class DifficultyPage(tk.Frame):
    _BUTTONS = [
        ("images/blå knapp.png",  "LÄTTARE", "easy"),
        ("images/röd knapp.png",  "MEDEL",   "medium"),
        ("images/svart knapp.png","SVÅRARE",  "hard"),
    ]
    _KEY_DIFF = {"8": "easy", "9": "medium", "0": "hard"}

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        canvas.create_text(
            sw // 2, int(sh * 0.37),
            text="Välj en svårighetsgrad!",
            font=("OpenDyslexic", 54, "bold"),
            fill="white",
            anchor="center",
        )

        btn_size = 220
        self._photos = []
        xs = [int(sw * 0.25), sw // 2, int(sw * 0.75)]
        btn_y = int(sh * 0.65)

        def go_p3(difficulty):
            controller.difficulty = difficulty
            controller.show_page(PlaceholderPage)

        for (path, label, diff), x in zip(self._BUTTONS, xs):
            img = Image.open(path).convert("RGBA").resize(
                (btn_size, btn_size), Image.LANCZOS
            )
            photo = ImageTk.PhotoImage(img)
            self._photos.append(photo)

            item = canvas.create_image(x, btn_y, anchor="center", image=photo)
            canvas.tag_bind(item, "<Button-1>", lambda *_, d=diff: go_p3(d))
            canvas.tag_bind(item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
            canvas.tag_bind(item, "<Leave>", lambda *_: canvas.config(cursor=""))

            canvas.create_text(
                x, btn_y + btn_size // 2 + 28,
                text=label,
                font=("OpenDyslexic", 36),
                fill="white",
                anchor="center",
            )

        for key, diff in self._KEY_DIFF.items():
            controller.bind(key, lambda *_, d=diff: go_p3(d))

        def on_destroy(_e):
            if _e.widget is self:
                for key in self._KEY_DIFF:
                    controller.unbind(key)

        self.bind("<Destroy>", on_destroy)


class PlaceholderPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        mission = generate_mission(controller.difficulty)

        canvas.create_text(
            sw // 2, int(sh * 0.25),
            text="Plocka fram följande modeller från byrålådorna:",
            font=("OpenDyslexic", 40, "bold"),
            fill="white",
            anchor="center",
        )

        name_y = int(sh * 0.55)
        for i, name in enumerate(mission):
            x = int(sw * (2 * i + 1) / 10)
            canvas.create_text(
                x, name_y,
                text=name,
                font=("OpenDyslexic", 28),
                fill="white",
                anchor="center",
            )

        # Difficulty indicator + label in top-right corner
        ind_size = 120
        ind_img = (
            Image.open(_DIFF_IMAGE[controller.difficulty])
            .convert("RGBA")
            .resize((ind_size, ind_size), Image.LANCZOS)
        )
        self._indicator = ImageTk.PhotoImage(ind_img)
        pad = 20
        img_cx = sw - pad - ind_size // 2
        img_cy = pad + ind_size // 2
        canvas.create_image(img_cx, img_cy, anchor="center", image=self._indicator)

        diff_labels = {"easy": "LÄTTARE", "medium": "MEDEL", "hard": "SVÅRARE"}
        canvas.create_text(
            img_cx - ind_size // 2 - 15, img_cy,
            text=diff_labels[controller.difficulty],
            font=("OpenDyslexic", 26, "bold"),
            fill="white",
            anchor="e",
        )


if __name__ == "__main__":
    App().mainloop()
