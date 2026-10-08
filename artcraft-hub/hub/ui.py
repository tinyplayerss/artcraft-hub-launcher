"""Adobe Creative Cloud-style widgets drawn on plain Tkinter canvases."""
import sys
import tkinter as tk

C = dict(bg="#1D1D1D", side="#141414", card="#2C2C2C", line="#3A3A3A",
         text="#EAEAEA", mute="#9B9B9B", blue="#1473E6", blue_hi="#0D66D0", blue_dn="#095ABA",
         green="#2D9D78", red="#E34850", grey="#4B4B4B", grey_hi="#5A5A5A")
FAMILY = "Segoe UI" if sys.platform.startswith("win") else "DejaVu Sans"
def font(size=10, bold=False): return (FAMILY, size, "bold" if bold else "normal")

def rrect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return c.create_polygon(pts, smooth=True, **kw)

class Button(tk.Canvas):
    """Pill button, Adobe style. kind: primary | secondary"""
    def __init__(self, master, text, command, kind="primary", width=110, height=32, bg=None):
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0,
                         bg=bg or master["bg"], cursor="hand2")
        self.cmd, self.kind, self.w, self.h, self.enabled, self.text = command, kind, width, height, True, text
        self.draw()
        self.bind("<Enter>", lambda e: self.draw("hi")); self.bind("<Leave>", lambda e: self.draw())
        self.bind("<ButtonPress-1>", lambda e: self.draw("dn")); self.bind("<ButtonRelease-1>", self._click)
    def draw(self, st=""):
        self.delete("all")
        i = ("", "hi", "dn").index(st)
        if not self.enabled: fill, line = C["grey"], ""
        elif self.kind == "primary": fill, line = (C["blue"], C["blue_hi"], C["blue_dn"])[i], ""
        else: fill, line = (C["card"], C["grey_hi"], C["grey"])[i], C["mute"]
        rrect(self, 1, 1, self.w-1, self.h-1, self.h//2-1, fill=fill, outline=line)
        self.create_text(self.w//2, self.h//2, text=self.text, fill=C["text"] if self.enabled else C["mute"], font=font(10, True))
    def set(self, text=None, enabled=None, kind=None):
        if text is not None: self.text = text
        if enabled is not None: self.enabled = enabled
        if kind is not None: self.kind = kind
        self.config(cursor="hand2" if self.enabled else "arrow"); self.draw()
    def _click(self, e):
        self.draw("hi")
        if self.enabled and 0 <= e.x <= self.w and 0 <= e.y <= self.h: self.cmd()

class Progress(tk.Canvas):
    def __init__(self, master, width=260, bg=None):
        super().__init__(master, width=width, height=6, highlightthickness=0, bg=bg or master["bg"]); self.w = width
    def set(self, frac):
        self.delete("all"); rrect(self, 0, 0, self.w, 6, 3, fill=C["grey"])
        if frac > 0.01: rrect(self, 0, 0, max(6, self.w*frac), 6, 3, fill=C["blue"])

class Toggle(tk.Canvas):
    def __init__(self, master, value, bg=None):
        super().__init__(master, width=40, height=22, highlightthickness=0, bg=bg or master["bg"], cursor="hand2")
        self.value = value; self.bind("<Button-1>", lambda e: self.flip()); self.draw()
    def flip(self): self.value = not self.value; self.draw()
    def draw(self):
        self.delete("all"); rrect(self, 1, 1, 39, 21, 10, fill=C["blue"] if self.value else C["grey"])
        x = 29 if self.value else 11; self.create_oval(x-8, 3, x+8, 19, fill="#fff", outline="")

class NavItem(tk.Canvas):
    def __init__(self, master, text, command):
        super().__init__(master, height=40, highlightthickness=0, bg=C["side"], cursor="hand2")
        self.text, self.active = text, False
        self.bind("<Configure>", lambda e: self.draw()); self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self.draw(True)); self.bind("<Leave>", lambda e: self.draw())
    def draw(self, hover=False):
        self.delete("all"); w = self.winfo_width()
        if self.active or hover: self.create_rectangle(0, 0, w, 40, fill=C["card"] if self.active else "#1E1E1E", outline="")
        if self.active: self.create_rectangle(0, 0, 3, 40, fill=C["blue"], outline="")
        self.create_text(22, 20, anchor="w", text=self.text, fill=C["text"] if self.active else C["mute"], font=font(10, self.active))

def entry(master, var, width=40, show=None):
    return tk.Entry(master, textvariable=var, width=width, show=show, bg=C["card"], fg=C["text"], insertbackground=C["text"],
                    relief="flat", highlightthickness=1, highlightbackground=C["line"], highlightcolor=C["blue"], font=font(10))


class Scroll(tk.Frame):
    """Vertically scrollable container (mouse wheel works on Windows and Linux). Put widgets in .inner"""
    def __init__(self, master, bg=None):
        super().__init__(master, bg=bg or C["bg"])
        self.cv = tk.Canvas(self, bg=self["bg"], highlightthickness=0)
        self.bar = tk.Scrollbar(self, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self.bar.set)
        self.cv.pack(side="left", fill="both", expand=True); self.bar.pack(side="right", fill="y")
        self.inner = tk.Frame(self.cv, bg=self["bg"]); win = self.cv.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.bind("<Configure>", lambda e: self.cv.itemconfigure(win, width=e.width))
        for w in (self.cv, self.inner):
            w.bind("<Enter>", lambda e: self._bind(True)); w.bind("<Leave>", lambda e: self._bind(False))
    def _bind(self, on):
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            (self.cv.bind_all if on else self.cv.unbind_all)(*((ev, self._wheel) if on else (ev,)))
    def _wheel(self, e):
        if self.inner.winfo_height() <= self.cv.winfo_height(): return
        self.cv.yview_scroll(-1 if (e.num == 4 or e.delta > 0) else 1, "units")


class Loading(tk.Canvas):
    """Grayed-out overlay: ghost grid of cards + spinning reticle. Blocks clicks while visible."""
    def __init__(self, master, count=13, cols=3):
        super().__init__(master, bg="#161616", highlightthickness=0, cursor="watch")
        self.count, self.cols, self.ang, self.label, self.sub, self.job = count, cols, 0, "Checking GitHub…", "", None
        self.bind("<Configure>", lambda e: self.draw()); self.bind("<Button-1>", lambda e: "break")
    def start(self):
        if self.job is None: self.tick()
    def stop(self):
        if self.job: self.after_cancel(self.job); self.job = None
    def text(self, label, sub=""): self.label, self.sub = label, sub
    def tick(self):
        self.ang = (self.ang + 14) % 360; self.draw(); self.job = self.after(40, self.tick)
    def draw(self):
        self.delete("all"); w, h = self.winfo_width(), self.winfo_height()
        if w < 50: return
        gw, ch = (w - 24) / self.cols, 215
        for i in range(self.count):                                  # ghost cards = the app grid, grayed out
            x, y = 6 + (i % self.cols) * gw + 6, 6 + (i // self.cols) * (ch + 12)
            if y > h: break
            rrect(self, x, y, x + gw - 12, y + ch, 6, fill="#202020", outline="#2A2A2A")
            rrect(self, x + 14, y + 14, x + 62, y + 62, 9, fill="#2A2A2A", outline="")
            rrect(self, x + 74, y + 24, x + 74 + gw * 0.35, y + 38, 4, fill="#2A2A2A", outline="")
            for k in range(3): rrect(self, x + 14, y + 80 + k * 20, x + gw - 40 - k * 30, y + 90 + k * 20, 4, fill="#252525", outline="")
        cx, cy = w // 2, min(h // 2, 230)
        rrect(self, cx - 110, cy - 85, cx + 110, cy + 85, 14, fill="#1D1D1D", outline="#3A3A3A")
        r = 34
        self.create_oval(cx - r, cy - 30 - r, cx + r, cy - 30 + r, outline="#3A3A3A", width=4)
        self.create_arc(cx - r, cy - 30 - r, cx + r, cy - 30 + r, start=-self.ang, extent=100, style="arc", outline=C["blue"], width=4)
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):            # reticle crosshair ticks
            self.create_line(cx + dx * (r + 4), cy - 30 + dy * (r + 4), cx + dx * (r + 12), cy - 30 + dy * (r + 12), fill=C["mute"], width=2)
        self.create_oval(cx - 3, cy - 33, cx + 3, cy - 27, fill=C["blue"], outline="")
        self.create_text(cx, cy + 36, text=self.label, fill=C["text"], font=font(10, True))
        self.create_text(cx, cy + 58, text=self.sub, fill=C["mute"], font=font(9))
