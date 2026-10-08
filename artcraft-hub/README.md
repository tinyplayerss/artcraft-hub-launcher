# ArtCraft Hub
Creative-Cloud-style launcher for ArtCraft Suites (Python 3 + Tkinter, stdlib only).

Run: `python3 main.py` (Linux needs `python3-tk`).
Build: `build_windows.bat` -> dist/ArtCraftHub.exe | `./build_appimage.sh` -> ArtCraftHub-x86_64.AppImage
CI: push a `v*` tag; .github/workflows/build.yml builds both and attaches them to the release.

## Bundled apps
Pre-loaded from github.com/storytold: ArtCraft, PhotoCraft, VectorCraft, FilmCraft, LightCraft, PrintCraft,
EffectCraft, DesignCraft, SoundCraft, DeckCraft, GridCraft, WordCraft, CADCraft. Each gets a Download button on the Apps screen.
Repos without a published release show "No release published yet" and a GitHub button.

## Point it at your repos
Edit Settings in-app, or config.json in %LOCALAPPDATA%\ArtCraftHub / ~/.local/share/ArtCraftHub,
or change DEFAULT_CONFIG in hub/core.py. Add more entries to "products" for multiple apps.

## Release asset naming
Windows: name contains "win", ends .zip/.exe/.msi.  Linux: contains "linux", ends .AppImage/.tar.gz/.zip.
Optional `<asset>.sha256` or SHA256SUMS.txt is verified before install. Tags like v1.2.3 compare numerically.

## Download -> Setup Wizard -> Open
Download fetches the release package from GitHub. A per-app Setup Wizard then opens (Welcome, install folder + shortcuts,
Installing, Finish with "Launch now"). Packages that ship their own .msi/setup .exe run that installer's own wizard instead.
Until setup is finished the card's Open button re-opens the wizard; afterwards Open launches the app.
Apps that are already set up are updated in place automatically.

## Rate limiting
The Hub never contacts GitHub on its own. Release info is fetched only when you press "Check for updates"
(unchanged answers use ETags and don't count against GitHub's limit). On launch it shows the last known results
from a local cache. If GitHub reports a rate limit the check stops immediately; add a token in Settings for 5,000 requests/hour.
