import queue, threading, webbrowser
import tkinter as tk
from tkinter import messagebox
from .wizard import Wizard
from . import core
from .ui import Button, Progress, Toggle, NavItem, Scroll, Loading, entry, rrect, font, C

class Hub:
    def __init__(self):
        self.cfg, self.state = core.load_config(), core.load_state()
        self.rel, self.busy, self.msg, self.frac = {}, set(), {}, {}
        self.q, self.cards, self.page = queue.Queue(), {}, "apps"
        r = self.root = tk.Tk(); r.title("ArtCraft Hub"); r.geometry("1120x720"); r.minsize(1000, 560); r.configure(bg=C["bg"])
        side = tk.Frame(r, bg=C["side"], width=210); side.pack(side="left", fill="y"); side.pack_propagate(False)
        logo = tk.Canvas(side, width=210, height=100, bg=C["side"], highlightthickness=0); logo.pack()
        rrect(logo, 22, 24, 54, 56, 7, fill=C["red"]); logo.create_text(38, 40, text="Ac", fill="#fff", font=font(13, True))
        logo.create_text(64, 31, anchor="w", text="ArtCraft Hub", fill=C["text"], font=font(12, True))
        logo.create_text(64, 46, anchor="nw", width=136, text="All your creative vision in one place.", fill=C["mute"], font=font(8))
        self.nav = {}
        for key, label in (("apps", "Apps"), ("updates", "Updates"), ("settings", "Settings")):
            n = NavItem(side, label, lambda k=key: self.show(k)); n.pack(fill="x"); self.nav[key] = n
        tk.Label(side, text=f"v{core.HUB_VERSION}", bg=C["side"], fg=C["mute"], font=font(8)).pack(side="bottom", pady=10)
        self.hubbtn = Button(side, "Hub update available", lambda: webbrowser.open(
            f"https://github.com/{self.cfg['hub_repo']}/releases/latest"), width=170, bg=C["side"])
        self.main = tk.Frame(r, bg=C["bg"]); self.main.pack(side="left", fill="both", expand=True)
        self._checking, self.loading = False, None
        for p in self.cfg["products"]:                      # show last known results WITHOUT touching the network
            found, rel = core.cached_release(p["repo"], self.cfg["include_prereleases"])
            if found: self.rel[p["id"]] = rel
        self.show("apps"); self.poll()

    # ---------- pages ----------
    def show(self, page):
        if getattr(self, "_building", False): return
        self._building = True
        try: self._show(page)
        finally: self._building = False

    def _show(self, page):
        self.page = page
        for k, n in self.nav.items(): n.active = k == page; n.draw()
        for w in self.main.winfo_children(): w.destroy()
        self.cards = {}
        head = tk.Frame(self.main, bg=C["bg"]); head.pack(fill="x", padx=36, pady=(28, 12))
        tk.Label(head, text=page.capitalize(), bg=C["bg"], fg=C["text"], font=font(20, True)).pack(side="left")
        if page != "settings": Button(head, "Check for updates", self.check_all, "secondary", 150).pack(side="right")
        holder = tk.Frame(self.main, bg=C["bg"]) if page == "updates" else Scroll(self.main)
        holder.pack(fill="both", expand=True, padx=(36, 24), pady=(0, 24))
        body = holder if page == "updates" else holder.inner
        {"apps": self.page_apps, "updates": self.page_updates, "settings": self.page_settings}[page](body)
        self.loading = Loading(holder, len(self.cfg["products"])) if page == "apps" else None
        self.sync_overlay()

    COLS = 3

    def sync_overlay(self):
        L = self.loading
        if not L or not L.winfo_exists(): return
        if self._checking: L.place(x=0, y=0, relwidth=1, relheight=1); tk.Misc.tkraise(L); L.start()
        else: L.stop(); L.place_forget()

    def page_apps(self, body):
        seen = set()
        for c in range(self.COLS): body.grid_columnconfigure(c, weight=1, uniform="col")
        for p in core.dedupe_products(self.cfg["products"]):
            if p["id"] in seen: continue
            seen.add(p["id"]); i = len(seen) - 1
            card = tk.Frame(body, bg=C["card"], highlightthickness=1, highlightbackground=C["line"])
            card.grid(row=i // self.COLS, column=i % self.COLS, sticky="nsew", padx=6, pady=6)
            col = p.get("color", C["red"])
            top = tk.Frame(card, bg=C["card"]); top.pack(fill="x", padx=14, pady=(14, 6))
            ic = tk.Canvas(top, width=48, height=48, bg=C["card"], highlightthickness=0); ic.pack(side="left")
            rrect(ic, 2, 2, 46, 46, 9, fill="#1B1B1B", outline=col, width=2)
            ic.create_text(24, 24, text=p.get("abbr", p["name"][:2]), fill=col, font=font(14, True))
            tk.Label(top, text=p["name"], bg=C["card"], fg=C["text"], font=font(12, True)).pack(side="left", padx=12)
            tk.Label(card, text=p.get("description", ""), bg=C["card"], fg=C["mute"], font=font(9), anchor="nw",
                     justify="left", wraplength=210, height=3).pack(fill="x", padx=14)
            st = tk.Label(card, bg=C["card"], fg=C["mute"], font=font(9), anchor="nw", justify="left", wraplength=210, height=2)
            st.pack(fill="x", padx=14, pady=(2, 4))
            pr = Progress(card, 210, C["card"]); pr.pack(anchor="w", padx=14)
            row = tk.Frame(card, bg=C["card"]); row.pack(fill="x", padx=14, pady=(10, 14))
            b1 = Button(row, "Download", lambda x=p: self.act(x), "primary", 104, 30, bg=C["card"])
            b2 = Button(row, "Remove", lambda x=p: self.uninstall(x["id"]), "secondary", 80, 30, bg=C["card"])
            b1.pack(side="left"); b2.pack(side="left", padx=(8, 0))
            self.cards[p["id"]] = (st, pr, b1, b2); self.refresh(p["id"])

    def page_updates(self, body):
        t = tk.Text(body, bg=C["card"], fg=C["text"], relief="flat", wrap="word", font=font(10), padx=16, pady=14, highlightthickness=0)
        t.pack(fill="both", expand=True); t.tag_config("h", font=font(12, True)); t.tag_config("m", foreground=C["mute"])
        for p in self.cfg["products"]:
            r, cur = self.rel.get(p["id"]), self.state.get(p["id"], {}).get("version")
            t.insert("end", f"{p['name']}\n", "h")
            if not r: t.insert("end", "No release info yet. Press “Check for updates”.\n\n", "m"); continue
            flag = "  — update available" if cur and core.is_newer(r["tag_name"], cur) else ""
            t.insert("end", f"Latest: {r['tag_name']}   Installed: {cur or 'not installed'}{flag}\n", "m")
            t.insert("end", (r.get("body") or "No release notes.").strip() + "\n\n")
        t.config(state="disabled")

    def page_settings(self, body):
        self.vars = {}
        def row(label, fn):
            f = tk.Frame(body, bg=C["bg"]); f.pack(fill="x", pady=7)
            tk.Label(f, text=label, width=28, anchor="w", bg=C["bg"], fg=C["text"], font=font(10)).pack(side="left"); fn(f)
        v = tk.StringVar(value=self.cfg["hub_repo"]); self.vars["hub_repo"] = v
        row("Hub repository (optional)", lambda f: entry(f, v).pack(side="left"))
        for p in self.cfg["products"]:
            v = tk.StringVar(value=p["repo"]); self.vars[p["id"]] = v
            row(f"{p['name']} repository", lambda f, v=v: entry(f, v).pack(side="left"))
        for key, label in (("auto_update", "Install updates automatically"), ("include_prereleases", "Include pre-releases")):
            def mk(f, key=key):
                t = Toggle(f, self.cfg[key], C["bg"]); t.pack(side="left"); self.vars[key] = t
            row(label, mk)
        v = tk.StringVar(value=self.cfg["github_token"]); self.vars["github_token"] = v
        row("GitHub token (optional)", lambda f: entry(f, v, 40, "•").pack(side="left"))
        Button(body, "Save settings", self.save_settings, width=130).pack(anchor="w", pady=16)

    def save_settings(self):
        g, c = self.vars, self.cfg
        c["hub_repo"] = g["hub_repo"].get().strip()
        for p in c["products"]: p["repo"] = g[p["id"]].get().strip()
        c["auto_update"], c["include_prereleases"] = g["auto_update"].value, g["include_prereleases"].value
        c["github_token"] = g["github_token"].get().strip(); core.save_config(c)

    # ---------- state / actions ----------
    def refresh(self, pid):
        if pid not in self.cards: return
        st, pr, b1, b2 = self.cards[pid]
        cur_entry = self.state.get(pid, {}); cur, r = cur_entry.get("version"), self.rel.get(pid)
        if pid in self.busy:
            st.config(text=self.msg.get(pid, "Working…"), fg=C["text"]); pr.set(self.frac.get(pid, 0))
            b1.set("Working…", False); b2.set(enabled=False); return
        pr.set(0); b2.set(enabled=bool(cur))
        newer = bool(cur and r and core.is_newer(r["tag_name"], cur))
        if not cur and pid not in self.rel: txt, bt = ("Checking GitHub…" if self._checking else "Press “Check for updates”"), "Download"
        elif not cur and r is None: txt, bt = "No release published yet", "GitHub"
        elif not cur: txt, bt = f"Not installed · latest {r['tag_name']}", "Download"
        elif not cur_entry.get("setup_done"): txt, bt = f"Downloaded {cur} · setup not finished", "Open"
        elif newer: txt, bt = f"Installed {cur} · update {r['tag_name']} available", "Update"
        else: txt, bt = f"Installed {cur} · up to date", "Open"
        err = self.msg.get(pid, "").startswith("Error")
        if err: txt = self.msg[pid]
        st.config(text=txt, fg=C["red"] if err else C["green"] if bt == "Open" else C["mute"])
        b1.set(bt, bt in ("Open", "GitHub") or r is not None, "secondary" if bt == "GitHub" else "primary")

    def act(self, p):
        pid, cur, r = p["id"], self.state.get(p["id"]), self.rel.get(p["id"])
        if not cur and pid in self.rel and r is None:
            return webbrowser.open(f"https://github.com/{p['repo']}/releases")
        newer = bool(cur and r and cur.get("setup_done") and core.is_newer(r["tag_name"], cur["version"]))
        if cur and not newer:
            return self.launch(p, cur) if cur.get("setup_done") else self.open_wizard(p)
        self.start_install(p)

    def launch(self, p, entry):
        try: proc = core.launch(entry)
        except Exception as e:
            self.msg[p["id"]] = f"Error: {e}"; self.refresh(p["id"]); return messagebox.showerror(p["name"], str(e))
        def check():
            if proc.poll() not in (None, 0): messagebox.showerror(p["name"], f"{p['name']} closed right after starting (code {proc.returncode}).")
        self.root.after(2500, check)

    def open_wizard(self, p):
        entry = self.state.get(p["id"])
        if getattr(self, "_wiz", None) and self._wiz.winfo_exists(): return self._wiz.lift()
        if not entry or not core.Path(entry.get("package", "")).exists(): return self.start_install(p)
        self._wiz = Wizard(self, p, entry, self.wizard_done)

    def wizard_done(self, p, launch):
        self.state = core.load_state(); self.refresh(p["id"])
        if launch and self.state.get(p["id"], {}).get("setup_done"): self.launch(p, self.state[p["id"]])

    def start_install(self, p):
        pid = p["id"]
        if pid in self.busy or not self.rel.get(pid): return
        self.busy.add(pid); self.msg.pop(pid, None); self.frac[pid] = 0; self.refresh(pid)
        rel, tok = self.rel[pid], self.cfg["github_token"]
        def work():
            try:
                core.fetch(p, rel, tok, lambda f: self.q.put(("p", pid, f)), lambda s: self.q.put(("s", pid, s)))
                self.q.put(("done", pid, None))
            except Exception as e: self.q.put(("err", pid, str(e)))
        threading.Thread(target=work, daemon=True).start()

    def uninstall(self, pid):
        if pid not in self.state: return
        name = next(x["name"] for x in self.cfg["products"] if x["id"] == pid)
        if messagebox.askyesno("Remove", f"Remove {name} from this computer?"):
            core.uninstall(pid); self.state = core.load_state(); self.msg.pop(pid, None); self.refresh(pid)

    def check_all(self):
        """Fetches release info from GitHub - ONLY runs when the user presses 'Check for updates'."""
        if self._checking: return
        self._checking = True; cfg = self.cfg; prods = core.dedupe_products(cfg["products"])
        self.sync_overlay()
        for p in prods: self.refresh(p["id"])
        def work():
            limited = False
            for i, p in enumerate(prods):
                self.q.put(("prog", None, (i, len(prods), p["name"])))
                if limited: self.q.put(("err", p["id"], "Skipped - GitHub rate limit reached")); continue
                try: self.q.put(("rel", p["id"], core.latest_release(p["repo"], cfg["include_prereleases"], cfg["github_token"])))
                except Exception as e:
                    limited = "rate limited" in str(e); self.q.put(("err", p["id"], str(e)))
            if cfg["hub_repo"] and not limited:
                try:
                    r = core.latest_release(cfg["hub_repo"], False, cfg["github_token"])
                    self.q.put(("hub", None, bool(r and core.is_newer(r["tag_name"], core.HUB_VERSION))))
                except Exception: pass
            self.q.put(("fin", None, None))
        threading.Thread(target=work, daemon=True).start()

    def _redo_updates(self):
        self._upd = False
        if self.page == "updates": self.show("updates")

    def poll(self):
        try:
            while True:
                k, pid, v = self.q.get_nowait()
                if k == "p": self.frac[pid] = v
                elif k == "s": self.msg[pid] = v
                elif k == "rel":
                    self.rel[pid] = v; cur = self.state.get(pid)
                    if self.msg.get(pid, "").startswith("Error") and pid not in self.busy: self.msg.pop(pid)
                    p = next(x for x in self.cfg["products"] if x["id"] == pid)
                    if self.cfg["auto_update"] and cur and v and core.is_newer(v["tag_name"], cur["version"]): self.start_install(p)
                    if self.page == "updates" and not getattr(self, "_upd", False):
                        self._upd = True; self.root.after(300, self._redo_updates)
                elif k == "prog":
                    if self.loading and self.loading.winfo_exists(): self.loading.text("Checking GitHub…", f"{v[2]}  ·  {v[0] + 1} of {v[1]}")
                elif k == "fin":
                    self._checking = False; self.sync_overlay()
                    for cid in list(self.cards): self.refresh(cid)
                elif k == "done":
                    self.busy.discard(pid); self.state = core.load_state(); self.msg.pop(pid, None)
                    if not self.state.get(pid, {}).get("setup_done"):          # first download -> show the Setup Wizard
                        self.refresh(pid); self.root.after(200, lambda p=next(x for x in self.cfg["products"] if x["id"] == pid): self.open_wizard(p))
                elif k == "err": self.busy.discard(pid); self.msg[pid] = f"Error: {v}"
                elif k == "hub":
                    if v: self.hubbtn.pack(side="bottom", pady=4)
                    else: self.hubbtn.pack_forget()
                if pid: self.refresh(pid)
        except queue.Empty: pass
        self.root.after(100, self.poll)

def main(): Hub().root.mainloop()
