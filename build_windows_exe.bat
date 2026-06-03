@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3 from https://www.python.org/downloads/windows/
    echo During installation, check "Add python.exe to PATH".
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install pyinstaller

python -m PyInstaller --onefile --windowed --name NetDebugTool net_debug_tool.py

echo.
echo Build finished.
echo EXE path: %cd%\dist\NetDebugTool.exe
pause
