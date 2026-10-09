<h1 align="center">ArtCraft Hub</h1>
<p align="center"><b>All your creative vision in one place.</b></p>
<p align="center">
  A lightweight, cross-platform launcher, installer and updater for the open-source <a href="https://github.com/storytold">ArtCraft</a> creative suite.
</p>
<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white">
  <img alt="GUI" src="https://img.shields.io/badge/GUI-Tkinter%20(stdlib)-1473E6">
  <img alt="Platforms" src="https://img.shields.io/badge/platform-Windows%2010%2F11%20%7C%20Linux%20(AppImage)-444">
  <img alt="Dependencies" src="https://img.shields.io/badge/runtime%20deps-none-2D9D78">
</p>

---

## Overview

ArtCraft Hub is a desktop application that does for the ArtCraft suite what a "creative cloud" desktop client does for a commercial suite: it gives you one window to **discover, download, install, update, launch, and manage projects** across every app. The difference is what sits behind it. There is no account, no sign-in, no licence server, and no recurring fee. Every app is fetched directly from its public GitHub Releases page, and everything the Hub stores lives on your own machine.

It is written in plain Python 3 with the standard library only. The interface is custom-drawn on Tkinter canvases (dark theme, pill buttons, card grid, loading states) so it feels like a modern creative-suite client without pulling in a heavyweight GUI framework.

> **Status:** actively developed. ArtCraft itself is a young project, so some apps may not have published releases yet. The Hub handles that gracefully (see [Behaviour](#behaviour-worth-knowing)).

## Features

| Area | What it does |
|---|---|
| **App catalogue** | 3-column grid of every ArtCraft app (ArtCraft, PhotoCraft, VectorCraft, FilmCraft, LightCraft, PrintCraft, EffectCraft, DesignCraft, SoundCraft, DeckCraft, GridCraft, WordCraft, CADCraft) with a **Download** button on each card. |
| **Install from GitHub** | Pulls the right asset for your OS straight from each repository's *Releases* tab. Windows: `.zip` / `.msi` / setup `.exe`. Linux: `.AppImage` / `.tar.gz` / `.tar.xz` / `.zip`. ARM and macOS builds are skipped on x86 Windows/Linux machines. |
| **Setup Wizard** | Per-app wizard (Welcome → install location and shortcuts → Installing → Finish with "Launch now"). Packages that ship their own installer run *that* installer's wizard instead. |
| **Update checks** | A **Check for updates** button compares installed versions against the latest release with numeric tag comparison (`v1.10.0` > `v1.9.2`). Optional pre-release channel. |
| **Automatic updates** | Apps that are already set up are updated in place after a check, preserving shortcuts and install location. Can be switched off in Settings. |
| **Project management** | Scans each app's default save location, reads file metadata (dates, size, plus PSD / PDF / DOCX / XLSX / DXF specifics), lists everything in one screen with **Open** and **Delete** (with a confirmation prompt, sent to the Recycle Bin / Trash). |
| **Last opened** | A dynamic sidebar button that re-opens your most recent project in the right ArtCraft app with one click. |
| **Integrity and safety** | SHA-256 verification when a release publishes checksums, path-traversal-safe archive extraction, TLS verification with a bundled CA store (`certifi`) so frozen builds work on any machine. |
| **Rate-limit friendly** | The Hub never polls. It talks to GitHub only when you press **Check for updates**, uses `ETag` conditional requests (cache hits do not count against the API limit), and stops immediately if GitHub reports a rate limit. |

## Why this exists: a different model for creative software

Professional creative tooling has been sold for years as a service: the software is rented, the licence is tied to an account, and access depends on continuing to pay. The desktop "hub" that manages installs and updates is an important part of that experience, and it has usually been inseparable from the subscription behind it.

ArtCraft Hub is a small proof that those two things are separable.

- **Ownership instead of tenancy.** You install a build, it is yours. Nothing phones home to decide whether you are still allowed to open your own files.
- **No account, no telemetry.** The Hub's only network traffic is to GitHub (release metadata and downloads). Configuration, caches, and project indexes are plain JSON in your user data folder.
- **Predictable cost.** The Hub is free to run and the apps it manages are open source. There is no per-seat pricing, tier, or plan to renew.
- **Transparent updates.** Release notes, versions and checksums come from public GitHub Releases that anyone can read, mirror, or audit. Pin to an older tag if a newer release regresses your workflow.
- **Your files stay in open or documented formats** and in folders you control, not in a vendor's cloud.

None of this makes subscriptions illegitimate; many teams value managed services and support contracts. The point is that **a polished, integrated suite experience no longer has to be bundled with a rental model**, and that professionals should be able to choose.

## ArtCraft and the FOSS ecosystem

Open-source creative software has produced excellent tools, but professionals have repeatedly run into the same barriers when trying to leave a proprietary workflow:

1. **Fragmentation.** A pipeline spans image editing, vector work, video, audio, layout, documents, and CAD. Open alternatives exist for many of these, but with different interfaces, file conventions, and release cadences, so they rarely feel like one suite.
2. **File-format friction.** Studios exchange work in de-facto standards such as PSD and PDF. Imperfect support means round-trips lose layers, effects, or fidelity, which is a hard stop for client work.
3. **Interface and workflow retraining.** Muscle memory and team conventions are expensive to change, so even a capable tool can be rejected for being unfamiliar.
4. **Distribution and update experience.** Compiling from source or hunting for installers is a long way from a one-click install-and-update client.

[ArtCraft by Storytold](https://github.com/storytold) is aimed squarely at those gaps. According to the organisation's own repository descriptions, it is building open-source tools and models for creatives, including clean-room reimplementations of industry staples (for example image editing, photo management, video editing, and PDF tooling) written in Rust. A single, memory-safe, cross-platform implementation language across the suite, published under open licences, is what makes a coherent *suite* possible rather than a collection of unrelated projects.

ArtCraft Hub is the glue on the distribution side: it removes the "how do I even install and keep this current" barrier so that evaluating and adopting the suite is as easy as a commercial client, while keeping the code, the formats, and the release process in the open.

> The ArtCraft apps are separate projects with their own licences, maturity levels, and release schedules. Check each repository for current status and terms before relying on it for production work.

## Screens

- **Apps:** card grid with per-app status (*Not installed*, *Downloaded*, *Installed vX · up to date*, *Update available*) and Download / Update / Open / Remove actions. A grayed-out loading overlay with a spinning reticle appears while checking GitHub.
- **Project management:** every project file in the suite, filterable per app, with expandable metadata, **Open** and **Delete**.
- **Updates:** latest release version and release notes per app.
- **Settings:** repository per app, auto-update and pre-release toggles, optional GitHub token.

## Getting started

Download the App from the [Releases](https://github.com/tinyplayerss/artcraft-hub-launcher/releases) page and always check the releases again from time to time to get Updates.

## Configuration

Settings are available in the app and stored in `config.json` under:

- Windows: `%LOCALAPPDATA%\ArtCraftHub`
- Linux: `~/.local/share/ArtCraftHub`

| Key | Purpose |
|---|---|
| `products` | List of apps: `id`, `name`, `repo` (`owner/repo`), `description`, `color`, `abbr`. Add or remove entries to customise the catalogue. |
| `auto_update` | Update already-installed apps automatically after a check. |
| `include_prereleases` | Treat pre-releases as eligible updates (default on while the suite is young). |
| `github_token` | Optional token to raise GitHub's API limit from 60 to 5,000 requests/hour. |
| `hub_repo` | Optional repository to check for Hub updates. |

### Release asset naming

So the Hub picks the correct file, name your release assets with the platform in the filename:

- Windows: contains `win`/`windows`, ends in `.zip`, `.msi`, or `.exe`.
- Linux: contains `linux`, ends in `.AppImage`, `.tar.gz`, `.tar.xz`, or `.zip`.
- Optional: `<asset>.sha256` or `SHA256SUMS.txt` in the same release enables checksum verification.

## Behaviour worth knowing

- **Repos without releases** show *No release published yet* with a **GitHub** button instead of a dead Download button.
- **Project scan locations** (non-recursive): Documents including OneDrive for `.psd`, `.vectorcraft`, `.fcproj`, `.xlsx`, `.dxf`, `.pdf`; each app's install folder for `.designcraft`, `.deckcraft`, `.docx`; `~/Untitled` for `.scraft`. OneDrive online-only files are listed but never read, so the scan cannot trigger a download.
- **Opening a project** launches the associated app with the file path as an argument.
- **Deleting a project** always asks first and uses the Recycle Bin / Trash where available.

## Project layout

```
artcraft-hub/
├── main.py                 # entry point
├── hub/
│   ├── app.py              # main window, pages, sidebar, update flow
│   ├── core.py             # config, GitHub releases, ETag cache, download, install, TLS
│   ├── wizard.py           # per-app Setup Wizard
│   ├── projects.py         # project discovery, metadata readers, recents, delete
│   └── ui.py               # canvas-drawn widgets, loading overlay, dialogs
├── tools/make_icon.py      # generates assets/icon.png and icon.ico
├── build_windows.bat       # PyInstaller build (Windows)
├── build_appimage.sh       # PyInstaller + AppImage build (Linux)
└── .github/workflows/      # CI builds on tag
```

## Roadmap

<img width="1600" height="800" alt="ArtCraft-Hub-Roadmap (2)" src="https://github.com/user-attachments/assets/1d9b8a89-67e1-4a8b-ab7b-7b235374c361" />

## Contributing

Issues and pull requests are welcome. Please keep the runtime dependency-free (standard library only), keep UI code in `hub/ui.py`, and test on both Windows and Linux where possible.

## Disclaimer

ArtCraft Hub is an independent project. ArtCraft is developed by Storytold and is a separate work with its own licences. All other product names mentioned are trademarks of their respective owners and are used only to describe compatibility and context. This project is not affiliated with or endorsed by any third-party software vendor.
