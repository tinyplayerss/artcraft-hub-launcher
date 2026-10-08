@echo off
REM Builds dist\ArtCraftHub.exe (Windows 10/11). Requires Python 3.9+ with tkinter.
python tools\make_icon.py || exit /b 1
python -m pip install -r requirements-build.txt || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name ArtCraftHub --icon assets\icon.ico main.py
echo Done: dist\ArtCraftHub.exe
