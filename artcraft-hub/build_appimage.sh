#!/usr/bin/env bash
# Builds ArtCraftHub-x86_64.AppImage on Linux. Needs python3-tk, pip, and internet for appimagetool.
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/make_icon.py
python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller --noconfirm --onedir --windowed --name ArtCraftHub main.py
rm -rf AppDir && mkdir -p AppDir/usr/bin
cp -r dist/ArtCraftHub/* AppDir/usr/bin/
cp assets/icon.png AppDir/artcrafthub.png
cat > AppDir/artcrafthub.desktop <<D
[Desktop Entry]
Type=Application
Name=ArtCraft Hub
Exec=ArtCraftHub
Icon=artcrafthub
Categories=Graphics;Utility;
D
printf '#!/bin/sh\nHERE="$(dirname "$(readlink -f "$0")")"\nexec "$HERE/usr/bin/ArtCraftHub" "$@"\n' > AppDir/AppRun
chmod +x AppDir/AppRun
[ -f appimagetool ] || { curl -L -o appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage; chmod +x appimagetool; }
ARCH=x86_64 ./appimagetool --appimage-extract-and-run AppDir ArtCraftHub-x86_64.AppImage
echo "Done: ArtCraftHub-x86_64.AppImage"
