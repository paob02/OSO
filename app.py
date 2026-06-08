import tkinter as tk
from tkinter import font as tkfont


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSO")
        self.configure(bg="#1e1e2e")
        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))

        self.title_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        self.body_font = tkfont.Font(family="Helvetica", size=13)
        self.btn_font = tkfont.Font(family="Helvetica", size=11, weight="bold")

        # Page container
        self.container = tk.Frame(self, bg="#1e1e2e")
        self.container.pack(fill="both", expand=True)

        self.pages = [WelcomePage, DifficultyPage, PlaceholderPage]
        self.page_index = 0
        self.current_page = None
        self.show_page(WelcomePage)

        self.bind("<Left>", lambda e: self.go_prev())
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


class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        tk.Label(
            self, text="Welcome to OSO",
            font=controller.title_font,
            bg="#1e1e2e", fg="#cba6f7",
        ).pack(pady=(80, 16))

        tk.Label(
            self, text="Use ← → arrow keys or press 1 / 2 / 3 to navigate.",
            font=controller.body_font,
            bg="#1e1e2e", fg="#a6adc8",
        ).pack()


class DifficultyPage(tk.Frame):
    LEVELS = [
        ("Easy", "#a6e3a1"),
        ("Medium", "#f9e2af"),
        ("Hard", "#f38ba8"),
    ]

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        self.selected = tk.StringVar(value="")

        tk.Label(
            self, text="Select Difficulty",
            font=controller.title_font,
            bg="#1e1e2e", fg="#cba6f7",
        ).pack(pady=(60, 24))

        btn_frame = tk.Frame(self, bg="#1e1e2e")
        btn_frame.pack()

        for level, color in self.LEVELS:
            tk.Button(
                btn_frame, text=level, width=12,
                font=controller.btn_font,
                bg="#313244", fg=color,
                activebackground="#45475a", activeforeground=color,
                relief="flat", pady=10, cursor="hand2",
                command=lambda l=level: self.select(l),
            ).pack(side="left", padx=12)

        self.status = tk.Label(
            self, text="", font=controller.body_font,
            bg="#1e1e2e", fg="#a6adc8",
        )
        self.status.pack(pady=20)

    def select(self, level):
        self.selected.set(level)
        self.status.config(text=f"Selected: {level}")


class PlaceholderPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e2e")

        tk.Label(
            self, text="Page 3",
            font=controller.title_font,
            bg="#1e1e2e", fg="#cba6f7",
        ).pack(pady=(80, 16))

        tk.Label(
            self, text="Coming soon.",
            font=controller.body_font,
            bg="#1e1e2e", fg="#a6adc8",
        ).pack()


if __name__ == "__main__":
    App().mainloop()
