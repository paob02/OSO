import tkinter as tk

from PIL import Image, ImageTk
import random
import numpy as np


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
    {"Astronaut",    "Atom"},
    {"Blåval",       "Cassiopeia A"},
    {"Katt",         "Jupiter"},
    {"Mars",         "Pyramid"},
    {"Saturnus",     "Röd jätte"},
    {"Tarmbakterie", "Teleskop"},
    {"Vintergatan",  "Virus"},
]

# Which physical drawer box each object lives in (1-indexed, matches drawers.png order)
_BOX = {
    "Astronaut":     1,
    "Atom":          1,
    "Cell":          2,
    "Mänskligt hår": 3,
    "Jorden":        4,
    "Pyramid":       5,
    "Mars":          5,
    "Herkules":      6,
    "Svart hål":     7,
    "Vattenmolekyl": 8,
    "Blåval":        9,
    "Cassiopeia A":  9,
    "DNA":           10,
    "Katt":          11,
    "Jupiter":       11,
    "Krabbnebulosa": 12,
    "Solen":         13,
    "Saturnus":      14,
    "Röd jätte":     14,
    "Tarmbakterie":  15,
    "Teleskop":      15,
    "Vintergatan":   16,
    "Virus":         16,
}

_DIFF_IMAGE = {
    "easy":   "images/blå knapp.png",
    "medium": "images/röd knapp.png",
    "hard":   "images/svart knapp.png",
}

_OBJ_PATH = {o[0]: o[1] for o in _OBJECTS}
_OBJ_SIZE = {o[0]: o[2] for o in _OBJECTS}


# ---------------------------------------------------------------------------
# Drawer helpers
# ---------------------------------------------------------------------------

def _segments(profile):
    segs, in_seg = [], False
    for i, v in enumerate(profile):
        if v and not in_seg:
            start, in_seg = i, True
        elif not v and in_seg:
            segs.append((start, i - 1))
            in_seg = False
    if in_seg:
        segs.append((start, len(profile) - 1))
    return segs


def _find_drawer_boxes(img):
    """Return list of (x0, y0, x1, y1) pixel boxes, top-row L→R then bottom-row L→R."""
    arr = np.array(img.convert("RGB"))
    fg = arr.max(axis=2) > 60

    boxes = []
    for c0, c1 in _segments(fg.any(axis=0)):
        for r0, r1 in _segments(fg[:, c0:c1 + 1].any(axis=1)):
            boxes.append((c0, r0, c1, r1))

    centers_y = [(r0 + r1) / 2 for (_, r0, _, r1) in boxes]
    ys = sorted(set(round(y) for y in centers_y))
    if len(ys) > 1:
        si = max(range(len(ys) - 1), key=lambda i: ys[i + 1] - ys[i])
        mid_y = (ys[si] + ys[si + 1]) / 2
    else:
        mid_y = float("inf")

    top = sorted([b for b in boxes if (b[1] + b[3]) / 2 < mid_y],  key=lambda b: b[0])
    bot = sorted([b for b in boxes if (b[1] + b[3]) / 2 >= mid_y], key=lambda b: b[0])
    return top + bot


def _build_drawer_image(drawer_orig, mission_names):
    """
    Returns (processed_img, label_data).
    label_data: list of (cx_px, cy_px, name, box_w_px) in original-image pixel space.
    Active boxes get the object image pasted in; inactive boxes are grayed out
    using direct numpy array assignment for pixel-perfect coverage.
    """
    img = drawer_orig.convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    boxes = _find_drawer_boxes(drawer_orig)
    active = {_BOX[n]: n for n in mission_names}

    paste_jobs = []
    label_data = []

    for i, (x0, y0, x1, y1) in enumerate(boxes):
        box_num = i + 1
        box_w = x1 - x0 + 1
        box_h = y1 - y0 + 1

        if box_num not in active:
            arr[y0:y1 + 1, x0:x1 + 1] = [80, 80, 80, 255]
        else:
            name = active[box_num]
            # Estimate name-text height in original-image pixels (~13pt on screen)
            name_h = max(14, box_h // 9)
            gap = 4
            h_pad = 3
            max_img_w = box_w - 2 * h_pad
            max_img_h = box_h - name_h - gap - 6

            if max_img_w > 0 and max_img_h > 0:
                obj = Image.open(_OBJ_PATH[name]).convert("RGBA")
                scale = min(max_img_w / max(obj.width, 1), max_img_h / max(obj.height, 1))
                ow = max(1, int(obj.width * scale))
                oh = max(1, int(obj.height * scale))
                obj_r = obj.resize((ow, oh), Image.LANCZOS)

                # Centre the (name + gap + image) block vertically in the box
                total_h = name_h + gap + oh
                top_y = y0 + max(3, (box_h - total_h) // 2)
                img_left = x0 + (box_w - ow) // 2
                img_top = top_y + name_h + gap
                paste_jobs.append((obj_r, img_left, img_top))
                label_data.append((x0 + box_w // 2, top_y + name_h // 2, name, box_w))
            else:
                label_data.append((x0 + box_w // 2, y0 + box_h // 2, name, box_w))

    result = Image.fromarray(arr)
    for obj_r, px, py in paste_jobs:
        result.paste(obj_r, (px, py), obj_r)

    return result, label_data


# ---------------------------------------------------------------------------
# Mission logic
# ---------------------------------------------------------------------------

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
        self.mission = []
        self.mission_sorted = []
        self.check_results = [None] * 5

        self.container = tk.Frame(self, bg="#1e1e2e")
        self.container.pack(fill="both", expand=True)

        self.pages = [WelcomePage, DifficultyPage, PlaceholderPage, Page4]
        self.page_index = 0
        self.current_page = None
        self.show_page(WelcomePage)

        self.bind("<Left>",  lambda e: self.go_prev())
        self.bind("<Right>", lambda e: self.go_next())
        self.bind("1", lambda e: self.show_page(WelcomePage))
        self.bind("2", lambda e: self.show_page(DifficultyPage))
        self.bind("3", lambda e: self.show_page(PlaceholderPage))
        self.bind("4", lambda e: self.show_page(Page4))

    def show_page(self, page_class, **kwargs):
        if self.current_page is not None:
            self.current_page.destroy()
        try:
            self.page_index = self.pages.index(page_class)
        except ValueError:
            self.page_index = -1
        self.current_page = page_class(self.container, self, **kwargs)
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
        ("images/blå knapp.png",   "LÄTTARE", "easy"),
        ("images/röd knapp.png",   "MEDEL",   "medium"),
        ("images/svart knapp.png", "SVÅRARE", "hard"),
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
            controller.mission = []
            controller.mission_sorted = []
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

        if not controller.mission:
            controller.mission = generate_mission(controller.difficulty)
            controller.mission_sorted = sorted(controller.mission, key=lambda n: _OBJ_SIZE[n])
        mission = controller.mission

        # Title
        canvas.create_text(
            sw // 2, int(sh * 0.28),
            text="Plocka fram följande modeller från byrålådorna:",
            font=("OpenDyslexic", 40, "bold"),
            fill="white",
            anchor="center",
        )

        # Mission object names (one row)
        name_y = int(sh * 0.37)
        for i, name in enumerate(mission):
            x = int(sw * (2 * i + 1) / 10)
            canvas.create_text(
                x, name_y,
                text=name,
                font=("OpenDyslexic", 28),
                fill="white",
                anchor="center",
            )

        # Drawers image — processed: active boxes get object image, inactive are grayed
        draw_orig = Image.open("images/drawers.png")
        orig_w, orig_h = draw_orig.size
        draw_w = int(sw * 0.92)
        draw_h = int(orig_h * draw_w / orig_w)
        draw_x = (sw - draw_w) // 2
        draw_y = int(sh * 0.42)

        processed, label_data = _build_drawer_image(draw_orig, mission)
        draw_scaled = processed.resize((draw_w, draw_h), Image.LANCZOS)
        self._drawer_photo = ImageTk.PhotoImage(draw_scaled)
        canvas.create_image(draw_x, draw_y, anchor="nw", image=self._drawer_photo)

        # Object name labels (black OpenDyslexic) above each pasted image
        sx = draw_w / orig_w
        sy = draw_h / orig_h
        for cx_px, cy_px, name, bw_px in label_data:
            cx_s = draw_x + cx_px * sx
            cy_s = draw_y + cy_px * sy
            bw_s = bw_px * sx
            canvas.create_text(
                cx_s, cy_s,
                text=name,
                font=("OpenDyslexic", 13, "bold"),
                fill="black",
                anchor="center",
                width=int(bw_s - 6),
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

        # Navigation buttons — positioned in the gap between dresser and screen bottom
        btn_size = 180
        btn_y = int(sh * 0.87)

        # Forward: röd knapp → Page4
        fwd_img = Image.open("images/röd knapp.png").convert("RGBA").resize(
            (btn_size, btn_size), Image.LANCZOS
        )
        self._fwd_photo = ImageTk.PhotoImage(fwd_img)

        def go_p4(*_):
            controller.show_page(Page4)

        fwd_item = canvas.create_image(sw // 2, btn_y, anchor="center", image=self._fwd_photo)
        canvas.tag_bind(fwd_item, "<Button-1>", go_p4)
        canvas.tag_bind(fwd_item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(fwd_item, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(
            sw // 2, btn_y + btn_size // 2 + 28,
            text="Gå till nästa steg",
            font=("OpenDyslexic", 36),
            fill="white",
            anchor="center",
        )

        # Back: blå knapp → DifficultyPage
        back_x = int(sw * 0.10)
        back_img = Image.open("images/blå knapp.png").convert("RGBA").resize(
            (btn_size, btn_size), Image.LANCZOS
        )
        self._back_photo = ImageTk.PhotoImage(back_img)

        def go_p2(*_):
            controller.show_page(DifficultyPage)

        back_item = canvas.create_image(back_x, btn_y, anchor="center", image=self._back_photo)
        canvas.tag_bind(back_item, "<Button-1>", go_p2)
        canvas.tag_bind(back_item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(back_item, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(
            back_x, btn_y + btn_size // 2 + 28,
            text="Tillbaka",
            font=("OpenDyslexic", 36),
            fill="white",
            anchor="center",
        )

        controller.bind("9", go_p4)
        controller.bind("8", go_p2)

        def on_destroy(_e):
            if _e.widget is self:
                controller.unbind("9")
                controller.unbind("8")

        self.bind("<Destroy>", on_destroy)


class Page4(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        mission = controller.mission

        # Title
        canvas.create_text(
            sw // 2, int(sh * 0.26),
            text="Placera ut modellerna på rätt podium i storlekordning och när du känner dig säker på ditt svar tryck på Klar-knappen:",
            font=("OpenDyslexic", 40, "bold"),
            fill="white",
            anchor="center",
            justify=tk.CENTER,
            width=int(sw * 0.85),
        )

        # Mission object names (one row)
        name_y = int(sh * 0.43)
        for i, name in enumerate(mission):
            x = int(sw * (2 * i + 1) / 10)
            canvas.create_text(
                x, name_y,
                text=name,
                font=("OpenDyslexic", 28),
                fill="white",
                anchor="center",
            )

        # Five podium images — gap between each equals one podium width
        pod_orig = Image.open("images/podium.png").convert("RGBA")
        n_pods = 5
        pw = int(sw * 0.55 / 9)  # 5 pods + 4 equal gaps → 9 units across 55 % of screen
        gap = pw
        ph = int(pod_orig.height * pw / pod_orig.width)
        pod_img = pod_orig.resize((pw, ph), Image.LANCZOS)
        self._pod_photo = ImageTk.PhotoImage(pod_img)

        pod_start_y = int(sh * 0.55)
        actual_row_w = n_pods * pw + (n_pods - 1) * gap
        pod_x0 = (sw - actual_row_w) // 2
        for i in range(n_pods):
            px = pod_x0 + i * (pw + gap)
            canvas.create_image(px, pod_start_y, anchor="nw", image=self._pod_photo)

        # Labels and arrow below podiums
        x_minst  = pod_x0 + pw // 2
        x_storst = pod_x0 + 4 * (pw + gap) + pw // 2
        label_y  = pod_start_y + ph + 35

        canvas.create_text(x_minst,  label_y, text="Minst",  font=("OpenDyslexic", 28, "bold"), fill="white", anchor="center")
        canvas.create_text(x_storst, label_y, text="Störst", font=("OpenDyslexic", 28, "bold"), fill="white", anchor="center")

        # Arrow spanning from after "Minst" to before "Störst"
        canvas.create_line(
            x_minst + pw // 2 + 15, label_y,
            x_storst - pw // 2 - 15, label_y,
            fill="white", width=4, arrow=tk.BOTH, arrowshape=(16, 20, 6),
        )

        # Difficulty indicator — top-right corner
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

        # Navigation buttons
        btn_size = 180
        btn_y = int(sh * 0.87)

        # Red button ("Klar") — centre
        fwd_img = Image.open("images/röd knapp.png").convert("RGBA").resize(
            (btn_size, btn_size), Image.LANCZOS
        )
        self._fwd_photo = ImageTk.PhotoImage(fwd_img)

        def go_done(*_):
            controller.check_results = [None] * 5
            controller.show_page(CheckPage, obj_index=0)

        fwd_item = canvas.create_image(sw // 2, btn_y, anchor="center", image=self._fwd_photo)
        canvas.tag_bind(fwd_item, "<Button-1>", go_done)
        canvas.tag_bind(fwd_item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(fwd_item, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(
            sw // 2, btn_y + btn_size // 2 + 28,
            text="Klar",
            font=("OpenDyslexic", 36),
            fill="white",
            anchor="center",
        )

        # Blue button ("Tillbaka") — bottom-left
        back_x = int(sw * 0.10)
        back_img = Image.open("images/blå knapp.png").convert("RGBA").resize(
            (btn_size, btn_size), Image.LANCZOS
        )
        self._back_photo = ImageTk.PhotoImage(back_img)

        def go_p3(*_):
            controller.show_page(PlaceholderPage)

        back_item = canvas.create_image(back_x, btn_y, anchor="center", image=self._back_photo)
        canvas.tag_bind(back_item, "<Button-1>", go_p3)
        canvas.tag_bind(back_item, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(back_item, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(
            back_x, btn_y + btn_size // 2 + 28,
            text="Tillbaka",
            font=("OpenDyslexic", 36),
            fill="white",
            anchor="center",
        )

        controller.bind("9", go_done)
        controller.bind("8", go_p3)

        def on_destroy(_e):
            if _e.widget is self:
                controller.unbind("9")
                controller.unbind("8")

        self.bind("<Destroy>", on_destroy)


def _format_size(m):
    import math

    def _full(v):
        """Format v as a full decimal without 'e' notation."""
        if v <= 0:
            return "0"
        if v < 1:
            exp = int(math.floor(math.log10(v)))
            decimals = -exp + 1
            return f"{v:.{decimals}f}".rstrip("0").rstrip(".")
        rounded = round(v)
        if abs(v - rounded) < max(v * 1e-9, 1e-9):
            return f"{rounded:,}".replace(",", " ")
        s = f"{v:.10g}"
        if "e" in s.lower():
            return f"{round(v):,}".replace(",", " ")
        return s

    LY = 9.461e15
    if m >= LY:
        return f"{_full(m / LY)} ly"
    if m >= 1000:
        return f"{_full(m / 1000)} km"
    return f"{_full(m)} m"


def _draw_diff_indicator(canvas, controller, sw):
    ind_size = 120
    ind_img = (Image.open(_DIFF_IMAGE[controller.difficulty]).convert("RGBA")
               .resize((ind_size, ind_size), Image.LANCZOS))
    photo = ImageTk.PhotoImage(ind_img)
    canvas._ind_photo = photo
    pad = 20
    img_cx = sw - pad - ind_size // 2
    img_cy = pad + ind_size // 2
    canvas.create_image(img_cx, img_cy, anchor="center", image=photo)
    diff_labels = {"easy": "LÄTTARE", "medium": "MEDEL", "hard": "SVÅRARE"}
    canvas.create_text(img_cx - ind_size//2 - 15, img_cy,
                       text=diff_labels[controller.difficulty],
                       font=("OpenDyslexic", 26, "bold"), fill="white", anchor="e")


def _check_pod_base(sw, sh):
    """Shared layout constants for both check pages."""
    pod_orig    = Image.open("images/podium.png").convert("RGBA")
    pw          = int(sw * 0.55 / 9)
    gap         = pw
    ph          = int(pod_orig.height * pw / pod_orig.width)
    pod_start_y = int(sh * 0.54)
    pod_x0      = (sw - (5 * pw + 4 * gap)) // 2
    max_img_h   = max(60, int(sh * 0.09))
    max_img_w   = pw + gap // 2
    # Fixed vertical slots above each podium (image/name never shift when size appears)
    size_cy     = pod_start_y - 26   # size text centre
    name_cy     = pod_start_y - 68   # name text centre
    img_bot     = pod_start_y - 98   # image bottom edge
    r           = max(22, int(pw * 0.42))
    pod_photo   = ImageTk.PhotoImage(pod_orig.resize((pw, ph), Image.LANCZOS))
    return pw, gap, ph, pod_start_y, pod_x0, max_img_h, max_img_w, size_cy, name_cy, img_bot, r, pod_photo


def _draw_check_content(canvas, self_ref, controller,
                        pw, gap, pod_start_y, pod_x0,
                        max_img_h, max_img_w, img_bot, name_cy, size_cy,
                        show_range, size_range):
    """Draw object image + name (and optionally size) above selected podiums.
    show_range: set of podium indices to draw image+name for.
    size_range: subset of show_range for which the size text is also drawn.
    """
    if not hasattr(self_ref, "_obj_photos"):
        self_ref._obj_photos = []
    for i, name in enumerate(controller.mission_sorted):
        if i not in show_range:
            continue
        cx = pod_x0 + i * (pw + gap) + pw // 2
        raw   = Image.open(_OBJ_PATH[name]).convert("RGBA")
        scale = min(max_img_w / raw.width, max_img_h / raw.height)
        iw    = max(1, int(raw.width  * scale))
        ih    = max(1, int(raw.height * scale))
        photo = ImageTk.PhotoImage(raw.resize((iw, ih), Image.LANCZOS))
        self_ref._obj_photos.append(photo)
        canvas.create_image(cx, img_bot, anchor="s", image=photo)
        canvas.create_text(cx, name_cy, text=name,
                            font=("OpenDyslexic", 20, "bold"), fill="white", anchor="center")
        if i in size_range:
            canvas.create_text(cx, size_cy, text=_format_size(_OBJ_SIZE[name]),
                                font=("OpenDyslexic", 20), fill="white", anchor="center")


def _draw_result_circles(canvas, pw, gap, ph, pod_start_y, pod_x0, r,
                         results, current_index, current_result):
    """Draw green/red circles for 0..current_index.
    current_result: True, False, or "blink".  Returns blink oval item id or None.
    """
    lw = max(3, r // 5)
    blink_id = None
    for i in range(current_index + 1):
        cx  = pod_x0 + i * (pw + gap) + pw // 2
        cy  = pod_start_y + ph // 2
        res = current_result if i == current_index else results[i]
        if res == "blink":
            blink_id = canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="yellow", outline="")
        elif res is True:
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#22cc44", outline="")
            canvas.create_line(cx-r*0.45, cy+r*0.05, cx-r*0.05, cy+r*0.45,
                               cx+r*0.55, cy-r*0.40,
                               fill="black", width=lw, joinstyle=tk.ROUND, capstyle=tk.ROUND)
        elif res is False:
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#cc2222", outline="")
            canvas.create_line(cx-r*0.5, cy-r*0.5, cx+r*0.5, cy+r*0.5,
                               fill="black", width=lw, capstyle=tk.ROUND)
            canvas.create_line(cx+r*0.5, cy-r*0.5, cx-r*0.5, cy+r*0.5,
                               fill="black", width=lw, capstyle=tk.ROUND)
    return blink_id


def _draw_minst_storst(canvas, pw, gap, ph, pod_start_y, pod_x0):
    x_minst  = pod_x0 + pw // 2
    x_storst = pod_x0 + 4 * (pw + gap) + pw // 2
    label_y  = pod_start_y + ph + 35
    canvas.create_text(x_minst,  label_y, text="Minst",  font=("OpenDyslexic", 28, "bold"), fill="white", anchor="center")
    canvas.create_text(x_storst, label_y, text="Störst", font=("OpenDyslexic", 28, "bold"), fill="white", anchor="center")
    canvas.create_line(x_minst + pw//2 + 15, label_y, x_storst - pw//2 - 15, label_y,
                       fill="white", width=4, arrow=tk.BOTH, arrowshape=(16, 20, 6))


class CheckPage(tk.Frame):
    def __init__(self, parent, controller, obj_index=0):
        super().__init__(parent, bg="#1e1e2e")
        self._blink_job  = None
        self._obj_photos = []

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        obj_name = controller.mission_sorted[obj_index]
        canvas.create_text(
            sw // 2, int(sh * 0.20),
            text=f"Placerade du {obj_name} på detta podium?",
            font=("OpenDyslexic", 40, "bold"),
            fill="white", anchor="center", justify=tk.CENTER,
            width=int(sw * 0.85),
        )

        (pw, gap, ph, pod_start_y, pod_x0,
         max_img_h, max_img_w, size_cy, name_cy, img_bot, r, pod_photo) = _check_pod_base(sw, sh)
        canvas._pod_photo = pod_photo
        for i in range(5):
            canvas.create_image(pod_x0 + i * (pw + gap), pod_start_y, anchor="nw", image=pod_photo)

        # Reveal only podiums 0..obj_index; show sizes for already-answered 0..obj_index-1
        _draw_check_content(canvas, self, controller, pw, gap, pod_start_y, pod_x0,
                            max_img_h, max_img_w, img_bot, name_cy, size_cy,
                            show_range=set(range(obj_index + 1)),
                            size_range=set(range(obj_index)))

        blink_id = _draw_result_circles(canvas, pw, gap, ph, pod_start_y, pod_x0, r,
                                        controller.check_results, obj_index, "blink")
        blink_on = [True]

        def _blink():
            canvas.itemconfig(blink_id, state="normal" if blink_on[0] else "hidden")
            blink_on[0] = not blink_on[0]
            self._blink_job = self.after(500, _blink)
        self._blink_job = self.after(0, _blink)

        _draw_minst_storst(canvas, pw, gap, ph, pod_start_y, pod_x0)
        _draw_diff_indicator(canvas, controller, sw)

        btn_size_sm = 180
        btn_size_lg = 210
        btn_y = int(sh * 0.87)

        # Tillbaka (blå)
        back_img = Image.open("images/blå knapp.png").convert("RGBA").resize((btn_size_sm, btn_size_sm), Image.LANCZOS)
        self._back_photo = ImageTk.PhotoImage(back_img)
        def go_back(*_):
            if obj_index == 0:
                controller.show_page(Page4)
            else:
                controller.show_page(CheckPage, obj_index=obj_index - 1)
        bi = canvas.create_image(int(sw * 0.10), btn_y, anchor="center", image=self._back_photo)
        canvas.tag_bind(bi, "<Button-1>", go_back)
        canvas.tag_bind(bi, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(bi, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.10), btn_y + btn_size_sm // 2 + 28,
                           text="Tillbaka", font=("OpenDyslexic", 36), fill="white", anchor="center")

        # Ja (röd)
        ja_img = Image.open("images/röd knapp.png").convert("RGBA").resize((btn_size_lg, btn_size_lg), Image.LANCZOS)
        self._ja_photo = ImageTk.PhotoImage(ja_img)
        def go_yes(*_):
            controller.check_results[obj_index] = True
            if obj_index == 4:
                controller.show_page(FinalPage)
            else:
                controller.show_page(CheckResultPage, obj_index=obj_index, correct=True)
        ji = canvas.create_image(int(sw * 0.40), btn_y, anchor="center", image=self._ja_photo)
        canvas.tag_bind(ji, "<Button-1>", go_yes)
        canvas.tag_bind(ji, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(ji, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.40), btn_y + btn_size_lg // 2 + 28,
                           text="Ja", font=("OpenDyslexic", 36), fill="white", anchor="center")

        # Nej (svart)
        nej_img = Image.open("images/svart knapp.png").convert("RGBA").resize((btn_size_lg, btn_size_lg), Image.LANCZOS)
        self._nej_photo = ImageTk.PhotoImage(nej_img)
        def go_no(*_):
            controller.check_results[obj_index] = False
            if obj_index == 4:
                controller.show_page(FinalPage)
            else:
                controller.show_page(CheckResultPage, obj_index=obj_index, correct=False)
        ni = canvas.create_image(int(sw * 0.60), btn_y, anchor="center", image=self._nej_photo)
        canvas.tag_bind(ni, "<Button-1>", go_no)
        canvas.tag_bind(ni, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(ni, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.60), btn_y + btn_size_lg // 2 + 28,
                           text="Nej", font=("OpenDyslexic", 36), fill="white", anchor="center")

        controller.bind("9", go_yes)
        controller.bind("0", go_no)
        controller.bind("8", go_back)

        def on_destroy(_e):
            if _e.widget is self:
                if self._blink_job:
                    self.after_cancel(self._blink_job)
                controller.unbind("9")
                controller.unbind("0")
                controller.unbind("8")
        self.bind("<Destroy>", on_destroy)


class CheckResultPage(tk.Frame):
    def __init__(self, parent, controller, obj_index=0, correct=True):
        super().__init__(parent, bg="#1e1e2e")
        self._obj_photos = []

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        canvas.create_text(
            sw // 2, int(sh * 0.20),
            text="Bra jobbat!" if correct else "Det var tyvärr fel!",
            font=("OpenDyslexic", 40, "bold"),
            fill="white", anchor="center",
        )

        (pw, gap, ph, pod_start_y, pod_x0,
         max_img_h, max_img_w, size_cy, name_cy, img_bot, r, pod_photo) = _check_pod_base(sw, sh)
        canvas._pod_photo = pod_photo
        for i in range(5):
            canvas.create_image(pod_x0 + i * (pw + gap), pod_start_y, anchor="nw", image=pod_photo)

        # Reveal 0..obj_index with image+name+size; nothing beyond
        _draw_check_content(canvas, self, controller, pw, gap, pod_start_y, pod_x0,
                            max_img_h, max_img_w, img_bot, name_cy, size_cy,
                            show_range=set(range(obj_index + 1)),
                            size_range=set(range(obj_index + 1)))

        _draw_result_circles(canvas, pw, gap, ph, pod_start_y, pod_x0, r,
                             controller.check_results, obj_index, correct)

        _draw_minst_storst(canvas, pw, gap, ph, pod_start_y, pod_x0)
        _draw_diff_indicator(canvas, controller, sw)

        btn_size = 180
        btn_y = int(sh * 0.87)

        # Tillbaka (blå) — clears current answer, re-asks
        back_img = Image.open("images/blå knapp.png").convert("RGBA").resize((btn_size, btn_size), Image.LANCZOS)
        self._back_photo = ImageTk.PhotoImage(back_img)
        def go_back(*_):
            controller.check_results[obj_index] = None
            controller.show_page(CheckPage, obj_index=obj_index)
        bi = canvas.create_image(int(sw * 0.10), btn_y, anchor="center", image=self._back_photo)
        canvas.tag_bind(bi, "<Button-1>", go_back)
        canvas.tag_bind(bi, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(bi, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.10), btn_y + btn_size // 2 + 28,
                           text="Tillbaka", font=("OpenDyslexic", 36), fill="white", anchor="center")

        # Fortsätt rätta (röd)
        fwd_img = Image.open("images/röd knapp.png").convert("RGBA").resize((btn_size, btn_size), Image.LANCZOS)
        self._fwd_photo = ImageTk.PhotoImage(fwd_img)
        def go_next(*_):
            if obj_index < 4:
                controller.show_page(CheckPage, obj_index=obj_index + 1)
            else:
                controller.show_page(FinalPage)
        fi = canvas.create_image(sw // 2, btn_y, anchor="center", image=self._fwd_photo)
        canvas.tag_bind(fi, "<Button-1>", go_next)
        canvas.tag_bind(fi, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(fi, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(sw // 2, btn_y + btn_size // 2 + 28,
                           text="Fortsätt rätta", font=("OpenDyslexic", 36), fill="white", anchor="center")

        controller.bind("9", go_next)
        controller.bind("8", go_back)

        def on_destroy(_e):
            if _e.widget is self:
                controller.unbind("9")
                controller.unbind("8")
        self.bind("<Destroy>", on_destroy)


class FinalPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")
        self._obj_photos = []

        canvas = tk.Canvas(self, highlightthickness=0, bg="#1e1e2e")
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=controller.bg_photo)

        sw = controller.winfo_screenwidth()
        sh = controller.winfo_screenheight()

        canvas.create_text(
            sw // 2, int(sh * 0.20),
            text="Bra Jobbat!\nPlacera tillbaka modellerna i deras lådor.",
            font=("OpenDyslexic", 40, "bold"),
            fill="white", anchor="center", justify=tk.CENTER,
            width=int(sw * 0.85),
        )

        # All 5 podiums with full results
        (pw, gap, ph, pod_start_y, pod_x0,
         max_img_h, max_img_w, size_cy, name_cy, img_bot, r, pod_photo) = _check_pod_base(sw, sh)
        canvas._pod_photo = pod_photo
        for i in range(5):
            canvas.create_image(pod_x0 + i * (pw + gap), pod_start_y, anchor="nw", image=pod_photo)

        _draw_check_content(canvas, self, controller, pw, gap, pod_start_y, pod_x0,
                            max_img_h, max_img_w, img_bot, name_cy, size_cy,
                            show_range=set(range(5)),
                            size_range=set(range(5)))

        _draw_result_circles(canvas, pw, gap, ph, pod_start_y, pod_x0, r,
                             controller.check_results, 4, controller.check_results[4])

        _draw_minst_storst(canvas, pw, gap, ph, pod_start_y, pod_x0)
        _draw_diff_indicator(canvas, controller, sw)

        # "Vill du spela igen?" above the buttons
        btn_size = 210
        btn_y = int(sh * 0.87)
        canvas.create_text(
            sw // 2, btn_y - btn_size // 2 - 40,
            text="Vill du spela igen?",
            font=("OpenDyslexic", 36, "bold"),
            fill="white", anchor="center",
        )

        # Ja (röd) → DifficultyPage
        ja_img = Image.open("images/röd knapp.png").convert("RGBA").resize((btn_size, btn_size), Image.LANCZOS)
        self._ja_photo = ImageTk.PhotoImage(ja_img)
        def go_yes(*_): controller.show_page(DifficultyPage)
        ji = canvas.create_image(int(sw * 0.40), btn_y, anchor="center", image=self._ja_photo)
        canvas.tag_bind(ji, "<Button-1>", go_yes)
        canvas.tag_bind(ji, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(ji, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.40), btn_y + btn_size // 2 + 28,
                           text="Ja", font=("OpenDyslexic", 36), fill="white", anchor="center")

        # Nej (svart) → WelcomePage
        nej_img = Image.open("images/svart knapp.png").convert("RGBA").resize((btn_size, btn_size), Image.LANCZOS)
        self._nej_photo = ImageTk.PhotoImage(nej_img)
        def go_no(*_): controller.show_page(WelcomePage)
        ni = canvas.create_image(int(sw * 0.60), btn_y, anchor="center", image=self._nej_photo)
        canvas.tag_bind(ni, "<Button-1>", go_no)
        canvas.tag_bind(ni, "<Enter>", lambda *_: canvas.config(cursor="hand2"))
        canvas.tag_bind(ni, "<Leave>", lambda *_: canvas.config(cursor=""))
        canvas.create_text(int(sw * 0.60), btn_y + btn_size // 2 + 28,
                           text="Nej", font=("OpenDyslexic", 36), fill="white", anchor="center")

        controller.bind("9", go_yes)
        controller.bind("0", go_no)

        def on_destroy(_e):
            if _e.widget is self:
                controller.unbind("9")
                controller.unbind("0")
        self.bind("<Destroy>", on_destroy)


if __name__ == "__main__":
    App().mainloop()
