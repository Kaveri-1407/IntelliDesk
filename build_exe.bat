@echo off
REM Build IntelliDesk.exe using PyInstaller
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name IntelliDesk --add-data "screenshots;screenshots" app.py

echo Build complete. See dist\IntelliDesk.exe
pause
