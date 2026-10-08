"""Per-app Setup Wizard: Welcome -> Options -> Installing -> Finish (Adobe-installer style)."""
import queue, threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from . import core
from .ui import Button, Progress, Toggle, entry as entry_widget, rrect, font, C


class Wizard(tk.Toplevel):
    def __init__(self, hub, product, entry, on_done):
        super().__init__(hub.root)
        self.hub, self.p, self.e, self.on_done = hub, product, entry, on_done
        self.step, self.alive, self.q, self.result = "welcome", True, queue.Queue(), None
        self.installer = entry["kind"] in ("msi", "setup")
        self.title(f"{product['name']} Setup"); self.configure(bg=C["bg"]); self.resizable(False, False)
        self.geometry(f"580x420+{hub.root.winfo_rootx() + 140}+{hub.root.winfo_rooty() + 80}")
        self.transient(hub.root); self.protocol("WM_DELETE_WINDOW", self.close)
        hd = tk.Frame(self, bg=C["side"], height=88); hd.pack(fill="x"); hd.pack_propagate(False)
        ic = tk.Canvas(hd, width=56, height=56, bg=C["side"], highlightthickness=0); ic.pack(side="left", padx=22)
        col = product.get("color", C["red"])
        rrect(ic, 2, 2, 54, 54, 10, fill="#1B1B1B", outline=col, width=2)
        ic.create_text(28, 28, text=product.get("abbr", product["name"][:2]), fill=col, font=font(16, True))
        tk.Label(hd, text=f"Set up {product['name']}", bg=C["side"], fg=C["text"], font=font(15, True)).pack(side="left")
        foot = tk.Frame(self, bg=C["side"], height=60); foot.pack(fill="x", side="bottom"); foot.pack_propagate(False)
        self.next = Button(foot, "Next", self.advance, width=110, bg=C["side"]); self.next.pack(side="right", padx=(8, 22), pady=14)
        self.cancel = Button(foot, "Cancel", self.close, "secondary", 90, bg=C["side"]); self.cancel.pack(side="right", pady=14)
        self.body = tk.Frame(self, bg=C["bg"]); self.body.pack(fill="both", expand=True, padx=30, pady=20)
        self.dir_var = tk.StringVar(value=str(core.default_install_dir(product)))
        self.opts = {}
        self.render(); self.after(150, self.poll); self.grab_set(); self.focus_force()

    # ---- helpers ----
    def label(self, text, size=10, bold=False, color=None, pady=(0, 8)):
        l = tk.Label(self.body, text=text, bg=C["bg"], fg=color or C["text"], font=font(size, bold), anchor="w",
                     justify="left", wraplength=510); l.pack(fill="x", pady=pady); return l

    def render(self):
        for w in self.body.winfo_children(): w.destroy()
        s = self.step
        if s == "welcome":
            self.label("Welcome", 13, True)
            self.label(f"This wizard will set up {self.p['name']} {self.e['version']} on this computer.")
            self.label(self.p.get("description", ""), color=C["mute"])
            self.label("Source: github.com/" + self.p["repo"], 9, color=C["mute"], pady=(14, 0))
            self.next.set("Next", True)
        elif s == "options" and self.installer:
            self.label("Installer", 13, True)
            self.label(f"{self.p['name']} comes with its own installer. Click Install and its setup wizard will open. "
                       "Come back here when it finishes.")
            self.next.set("Install", True)
        elif s == "options":
            self.label("Choose where to install", 13, True)
            row = tk.Frame(self.body, bg=C["bg"]); row.pack(fill="x", pady=(0, 14))
            entry_widget(row, self.dir_var, 44).pack(side="left", fill="x", expand=True, ipady=4)
            Button(row, "Browse…", self.browse, "secondary", 90, bg=C["bg"]).pack(side="left", padx=(8, 0))
            for key, text in (("desktop", "Create a desktop shortcut"),
                              ("menu", "Add to Start menu" if core.IS_WIN else "Add to application launcher")):
                r = tk.Frame(self.body, bg=C["bg"]); r.pack(fill="x", pady=5)
                t = Toggle(r, True, C["bg"]); t.pack(side="left"); self.opts[key] = t
                tk.Label(r, text=text, bg=C["bg"], fg=C["text"], font=font(10)).pack(side="left", padx=10)
            self.next.set("Install", True)
        elif s == "progress":
            self.label("Installing…", 13, True)
            self.status = self.label("Preparing…", color=C["mute"])
            self.bar = Progress(self.body, 500, C["bg"]); self.bar.pack(anchor="w", pady=10); self.bar.set(0.15)
            self.next.set("Please wait", False); self.cancel.set(enabled=False)
        elif s == "finish":
            self.label("All done", 13, True)
            self.label(f"{self.p['name']} {self.e['version']} is ready to use.")
            if self.result and self.result.get("exe"):
                r = tk.Frame(self.body, bg=C["bg"]); r.pack(fill="x", pady=10)
                self.launch_t = Toggle(r, True, C["bg"]); self.launch_t.pack(side="left")
                tk.Label(r, text=f"Launch {self.p['name']} now", bg=C["bg"], fg=C["text"], font=font(10)).pack(side="left", padx=10)
            self.next.set("Finish", True); self.cancel.pack_forget()
        elif s == "error":
            self.label("Setup could not finish", 13, True, C["red"])
            self.label(self.err)
            self.next.set("Try again", True); self.cancel.set(enabled=True)

    def browse(self):
        d = filedialog.askdirectory(parent=self, title="Choose install folder")
        if d: self.dir_var.set(str(Path(d) / self.p["name"]))

    def advance(self):
        s = self.step
        if s == "welcome": self.step = "options"
        elif s == "options": self.step = "progress"; self.render(); return self.start()
        elif s == "error": self.step = "options"
        elif s == "finish": return self.finish()
        self.render()

    # ---- work ----
    def start(self):
        dest, desktop, menu = self.dir_var.get().strip(), self.opts.get("desktop"), self.opts.get("menu")
        want_d, want_m = (desktop.value if desktop else False), (menu.value if menu else False)
        def work():
            try:
                if self.installer:
                    self.q.put(("s", "Waiting for the installer to finish…"))
                    res = core.run_installer(self.e, self.p)
                else:
                    self.q.put(("s", "Copying files…"))
                    res = core.setup_portable(self.e, self.p, dest)
                    self.q.put(("s", "Creating shortcuts…"))
                    res["shortcuts"] = core.make_shortcuts(self.p, res["exe"], want_d, want_m)
                core.save_entry(self.p["id"], res); self.q.put(("ok", res))
            except Exception as ex: self.q.put(("err", str(ex)))
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        if not self.alive: return
        try:
            while True:
                k, v = self.q.get_nowait()
                if k == "s": self.status.config(text=v)
                elif k == "ok": self.result, self.step = v, "finish"; self.bar.set(1); self.render()
                elif k == "err": self.err, self.step = v, "error"; self.render()
        except queue.Empty: pass
        except tk.TclError: return
        self.after(150, self.poll)

    def finish(self):
        launch = bool(self.result and self.result.get("exe") and getattr(self, "launch_t", None) and self.launch_t.value)
        self.close(); self.on_done(self.p, launch)

    def close(self):
        if self.step == "progress": return
        self.alive = False; self.grab_release(); self.destroy()
        if self.step != "finish": self.on_done(self.p, False)
