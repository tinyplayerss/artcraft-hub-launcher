"""ArtCraft Hub core: config, GitHub releases, install, update. Stdlib only."""
import hashlib, json, os, platform, re, shutil, stat, subprocess, sys, tarfile, tempfile, zipfile
import urllib.request, urllib.error
from pathlib import Path

HUB_VERSION = "1.3.0"
IS_WIN = sys.platform.startswith("win")
DATA = (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ArtCraftHub") if IS_WIN \
    else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "ArtCraftHub"
CONFIG, STATE = DATA / "config.json", DATA / "state.json"

def _p(id, name, desc, color, abbr):
    return {"id": id, "name": name, "repo": f"storytold/{id}", "description": desc, "color": color, "abbr": abbr}

PRODUCTS = [
    _p("artcraft", "ArtCraft", "Intentional crafting engine for artists, designers and filmmakers", "#E34850", "Ac"),
    _p("photocraft", "PhotoCraft", "Image editing: layers, masks, type and real PSD files", "#31A8FF", "Pc"),
    _p("vectorcraft", "VectorCraft", "Vector illustration", "#FF9A00", "Vc"),
    _p("filmcraft", "FilmCraft", "Video editing, color and sound", "#9999FF", "Fc"),
    _p("lightcraft", "LightCraft", "Photo library and raw development", "#6FC3FF", "Lc"),
    _p("printcraft", "PrintCraft", "Reading, organizing and protecting PDFs", "#FA3A2F", "Pr"),
    _p("effectcraft", "EffectCraft", "Motion graphics and visual effects", "#D291FF", "Ec"),
    _p("designcraft", "DesignCraft", "Page layout and publishing", "#FF3DA5", "Dc"),
    _p("soundcraft", "SoundCraft", "Audio production and mixing", "#00C4B3", "Sc"),
    _p("deckcraft", "DeckCraft", "Presentations and slide shows", "#FF7A45", "Dk"),
    _p("gridcraft", "GridCraft", "Spreadsheets", "#2DA66F", "Gc"),
    _p("wordcraft", "WordCraft", "Word processing", "#4C8DF6", "Wc"),
    _p("cadcraft", "CADCraft", "Computer-aided design and drafting", "#E8453C", "Cc"),
]

DEFAULT_CONFIG = {
    "hub_repo": "", "products": PRODUCTS,
    "auto_update": True, "check_minutes": 30,
    "include_prereleases": True, "github_token": ""}


def _load(path, default):
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return json.loads(json.dumps(default))

def _save(path, data):
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), "utf-8")
    tmp.replace(path)

def dedupe_products(items):
    """Keep exactly one entry per app id / repo; first one wins."""
    seen_id, seen_repo, out = set(), set(), []
    for p in items:
        i, r = str(p.get("id", "")).lower(), str(p.get("repo", "")).lower()
        if not i or i in seen_id or (r and r in seen_repo): continue
        seen_id.add(i); seen_repo.add(r); out.append(p)
    return out

def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG)); saved = _load(CONFIG, {}); cfg.update(saved)
    have = {p["id"]: p for p in saved.get("products", []) if p.get("id") != "suite"}   # drop old placeholder
    cfg["products"] = [have.get(p["id"], p) for p in PRODUCTS] + [p for i, p in have.items() if i not in {x["id"] for x in PRODUCTS}]
    cfg["products"] = dedupe_products(cfg["products"])
    for p in cfg["products"]:                                                           # keep new fields on old configs
        d = next((x for x in PRODUCTS if x["id"] == p["id"]), {}); p.setdefault("color", d.get("color", "#E34850")); p.setdefault("abbr", d.get("abbr", p["name"][:2]))
    return cfg
def save_config(c):
    c["products"] = dedupe_products(c.get("products", [])); _save(CONFIG, c)
def load_state(): return _load(STATE, {})
def save_state(s): _save(STATE, s)


def vtuple(tag):
    return tuple(int(x) for x in re.findall(r"\d+", tag or "")[:4]) or (0,)

def is_newer(remote, local):
    a, b = vtuple(remote), vtuple(local)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


def _req(url, token=""):
    h = {"User-Agent": "ArtCraft-Hub", "Accept": "application/vnd.github+json"}
    if token: h["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=h)

def _http_msg(e, repo):
    return (f"GitHub returned {e.code} for {repo}"
            + (" (rate limited - add a token in Settings)" if e.code == 403 else "")
            + (" (repo not found or private - check Settings / add a token)" if e.code == 404 else ""))

def latest_release(repo, prereleases=False, token=""):
    """Newest published release of `repo` (from the GitHub Releases tab).
    Uses ETags: unchanged answers (HTTP 304) don't count against GitHub's rate limit."""
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    cache = _load(DATA / "etag.json", {}); hit = cache.get(url)
    rq = _req(url, token)
    if hit: rq.add_header("If-None-Match", hit["etag"])
    try:
        with urllib.request.urlopen(rq, timeout=20) as r:
            rels = json.load(r)
            if r.headers.get("ETag"):
                cache[url] = {"etag": r.headers["ETag"], "body": rels}; _save(DATA / "etag.json", cache)
    except urllib.error.HTTPError as e:
        if e.code == 304 and hit: rels = hit["body"]
        else: raise RuntimeError(_http_msg(e, repo))
    except Exception as e:
        raise RuntimeError(f"Network error: {e}")
    return _pick_latest(rels, prereleases)

def _pick_latest(rels, prereleases):
    rels = [x for x in rels if not x.get("draft") and (prereleases or not x.get("prerelease"))]
    return max(rels, key=lambda x: vtuple(x["tag_name"])) if rels else None

def cached_release(repo, prereleases=False):
    """Last known release from the local cache - makes NO network request. Returns (found, release)."""
    hit = _load(DATA / "etag.json", {}).get(f"https://api.github.com/repos/{repo}/releases?per_page=20")
    return (True, _pick_latest(hit["body"], prereleases)) if hit else (False, None)


def pick_asset(rel):
    exts = (".zip", ".msi", ".exe") if IS_WIN else (".appimage", ".tar.gz", ".tgz", ".tar.xz", ".zip")
    best, best_score = None, -99
    for a in rel.get("assets", []):
        n = a["name"].lower()
        hit = [i for i, e in enumerate(exts) if n.endswith(e)]
        if not hit: continue
        if "mac" in n or "darwin" in n or "osx" in n or "wasm" in n: continue
        if platform.machine().lower() in ("x86_64", "amd64") and re.search(r"aarch64|arm64", n): continue
        if IS_WIN and "linux" in n: continue
        if not IS_WIN and re.search(r"win(dows|32|64)?[-_.]", n): continue
        score = (10 if ("win" if IS_WIN else "linux") in n else 0) - hit[0]
        if score > best_score: best, best_score = a, score
    return best


def download(url, dest, token="", progress=None):
    with urllib.request.urlopen(_req(url, token), timeout=30) as r, open(dest, "wb") as f:
        total, done = int(r.headers.get("Content-Length") or 0), 0
        while chunk := r.read(1 << 16):
            f.write(chunk); done += len(chunk)
            if progress and total: progress(done / total)

def _sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def _safe_extract(archive, out):
    out = out.resolve()
    def ok(name): return (out / name).resolve().is_relative_to(out)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as z:
            if not all(ok(m) for m in z.namelist()): raise RuntimeError("Unsafe path in archive")
            z.extractall(out)
    else:
        with tarfile.open(archive) as t:
            if not all(ok(m.name) for m in t.getmembers()): raise RuntimeError("Unsafe path in archive")
            t.extractall(out)

MARK = ".artcraft-hub-install"
ARCHIVES = (".zip", ".tar.gz", ".tgz", ".tar.xz")

def _safe(tag): return re.sub(r"[^\w.\-]", "_", tag)

def _find_exe(folder, hint=""):
    cands = []
    for p in Path(folder).rglob("*"):
        if not p.is_file() or p.name == MARK: continue
        n = p.name.lower()
        if IS_WIN and n.endswith(".exe") and not n.startswith(("unins", "uninstall")): cands.append(p)
        elif not IS_WIN and (n.endswith(".appimage") or (p.suffix == "" and os.access(p, os.X_OK))): cands.append(p)
    return min(cands, key=lambda p: (hint.lower() not in p.name.lower(), len(p.parts), len(p.name))) if cands else None

def default_install_dir(product):
    if IS_WIN: return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "ArtCraft" / product["name"]
    return Path.home() / ".local/share/artcraft" / product["id"]


def fetch(product, rel, token="", progress=None, status=None):
    """Step 1: download + verify the release package. First time it waits for the Setup Wizard;
    for apps that are already set up it updates them in place automatically."""
    status = status or (lambda s: None)
    asset = pick_asset(rel)
    if not asset: raise RuntimeError(f"No {'Windows' if IS_WIN else 'Linux'} asset in release {rel['tag_name']}")
    tag, pid = rel["tag_name"], product["id"]
    pdir = DATA / "packages" / pid / _safe(tag)
    if pdir.exists(): shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    f = pdir / asset["name"]
    status("Downloading…"); download(asset["browser_download_url"], f, token, progress)
    sums = next((a for a in rel["assets"] if a["name"].lower() in
                 (asset["name"].lower() + ".sha256", "sha256sums.txt", "checksums.txt")), None)
    if sums:
        status("Verifying…"); sf = pdir / "sums.tmp"; download(sums["browser_download_url"], sf, token)
        ok = _sha256(f) in sf.read_text("utf-8", "ignore").lower(); sf.unlink()
        if not ok: shutil.rmtree(pdir, ignore_errors=True); raise RuntimeError("Checksum mismatch - download discarded")
    n = f.name.lower()
    kind = ("archive" if n.endswith(ARCHIVES) else "msi" if n.endswith(".msi") else
            "setup" if (IS_WIN and n.endswith(".exe") and re.search("setup|install", n)) else "file")
    entry = {"version": tag, "package": str(f), "kind": kind, "setup_done": False}
    state = load_state(); old = state.get(pid, {})
    if old.get("setup_done"):                                   # automatic in-place update
        status("Updating…")
        try:
            if kind in ("archive", "file") and old.get("dir"):
                entry = setup_portable(entry, product, old["dir"]); entry["shortcuts"] = old.get("shortcuts", [])
            elif kind == "msi" and old.get("installer"):
                subprocess.run(["msiexec", "/i", str(f), "/qn", "/norestart"], check=True)
                entry.update(setup_done=True, installer=True, exe=old.get("exe"), shortcuts=[])
        except Exception as e:
            entry.update(setup_done=False, note=str(e))
    state[pid] = entry; save_state(state)
    for d in (DATA / "packages" / pid).iterdir():
        if d != pdir: shutil.rmtree(d, ignore_errors=True)
    return entry


def setup_portable(entry, product, dest):
    """Step 2 (archives / single files): put the app in `dest`."""
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        if not (dest / MARK).exists(): raise RuntimeError("That folder isn't empty - choose an empty or new folder")
        for c in dest.iterdir():
            if c.name != MARK: shutil.rmtree(c, ignore_errors=True) if c.is_dir() else c.unlink()
    dest.mkdir(parents=True, exist_ok=True); (dest / MARK).write_text(product["id"])
    pkg = Path(entry["package"])
    if entry["kind"] == "archive": _safe_extract(pkg, dest)
    else: shutil.copy2(pkg, dest / pkg.name)
    if not IS_WIN:
        for p in dest.rglob("*"):
            if p.is_file() and p.name != MARK and (p.suffix == "" or p.name.lower().endswith(".appimage")):
                p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    exe = _find_exe(dest, product["id"])
    if not exe: raise RuntimeError("Setup finished but no program file was found in the package")
    return {**entry, "dir": str(dest), "exe": str(exe), "setup_done": True}


def run_installer(entry, product):
    """Step 2 (packages with their own installer): show that installer's own wizard and wait for it."""
    cmd = ["msiexec", "/i", entry["package"]] if entry["kind"] == "msi" else [entry["package"]]
    rc = subprocess.run(cmd).returncode
    if rc not in (0, 3010): raise RuntimeError(f"The installer closed with code {rc}")
    exe = None
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = Path(os.environ.get(env, ""))
        base = base / "Programs" if env == "LOCALAPPDATA" else base
        if base.is_dir():
            for d in base.iterdir():
                if d.is_dir() and (product["id"] in d.name.lower() or product["name"].lower() in d.name.lower()):
                    exe = _find_exe(d, product["id"]) or exe
    return {**entry, "setup_done": True, "installer": True, "exe": str(exe) if exe else None}


def make_shortcuts(product, exe, desktop=True, menu=True):
    made = []
    name = product["name"]
    if IS_WIN:
        for want, folder in ((desktop, "Desktop"), (menu, "Programs")):
            if not want: continue
            ps = ('$d=[Environment]::GetFolderPath("%s");$p=Join-Path $d "%s.lnk";'
                  '$s=(New-Object -ComObject WScript.Shell).CreateShortcut($p);$s.TargetPath="%s";'
                  '$s.WorkingDirectory="%s";$s.Save();Write-Output $p') % (folder, name, exe, Path(exe).parent)
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                               creationflags=0x08000000)
            if r.stdout.strip(): made.append(r.stdout.strip())
    else:
        text = (f"[Desktop Entry]\nType=Application\nName={name}\nExec=\"{exe}\"\n"
                f"Path={Path(exe).parent}\nTerminal=false\nCategories=Graphics;\n")
        targets = []
        if menu: targets.append(Path.home() / ".local/share/applications" / f"artcraft-{product['id']}.desktop")
        if desktop and (Path.home() / "Desktop").is_dir(): targets.append(Path.home() / "Desktop" / f"{name}.desktop")
        for t in targets:
            t.parent.mkdir(parents=True, exist_ok=True); t.write_text(text); t.chmod(0o755); made.append(str(t))
    return made


def save_entry(pid, entry):
    st = load_state(); st[pid] = entry; save_state(st)

def launch(entry):
    exe = entry.get("exe")
    if not exe or not Path(exe).exists():
        raise RuntimeError("This app was set up with its own installer - open it from your Start menu / app launcher."
                           if entry.get("installer") else "Program file not found - run Download again.")
    return subprocess.Popen([exe], cwd=str(Path(exe).parent), start_new_session=not IS_WIN)

def uninstall(pid):
    s = load_state(); e = s.pop(pid, None); save_state(s)
    if not e: return
    d = Path(e["dir"]) if e.get("dir") else None
    if d and (d / MARK).exists(): shutil.rmtree(d, ignore_errors=True)
    for sc in e.get("shortcuts", []): Path(sc).unlink(missing_ok=True)
    shutil.rmtree(DATA / "packages" / pid, ignore_errors=True)
