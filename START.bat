@echo off
REM ===================================================================
REM  STL ShrinkWrap - Start aus dem Quellcode (Option B)
REM  Prueft Python, legt eine lokale venv an, installiert PyMeshLab
REM  beim ersten Mal automatisch und startet danach die App.
REM ===================================================================
setlocal
cd /d "%~dp0"

REM --- Python finden ---
set "PY="
where py >nul 2>nul && set "PY=py -3"
if "%PY%"=="" (
    where python >nul 2>nul && set "PY=python"
)
if "%PY%"=="" (
    echo.
    echo [FEHLER] Es wurde kein Python gefunden.
    echo Bitte Python 3.10+ installieren von https://www.python.org/downloads/
    echo Beim Installer unbedingt "Add Python to PATH" anhaken.
    echo.
    pause
    exit /b 1
)

REM --- Virtuelle Umgebung beim ersten Mal anlegen ---
if not exist ".venv\Scripts\python.exe" (
    echo [Setup] Erstelle virtuelle Umgebung ...
    %PY% -m venv ".venv"
    if errorlevel 1 ( echo [FEHLER] venv konnte nicht erstellt werden. & pause & exit /b 1 )
    echo [Setup] Installiere PyMeshLab ^(einmalig, kann ein paar Minuten dauern^) ...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 ( echo [FEHLER] Installation fehlgeschlagen. & pause & exit /b 1 )
)

REM --- App starten ---
".venv\Scripts\pythonw.exe" "stl_shrinkwrap.py"
endlocal
