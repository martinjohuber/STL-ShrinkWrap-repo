@echo off
REM ===================================================================
REM  Baut den portablen Ordner  STL-ShrinkWrap-Portable\  komplett neu.
REM  Voraussetzung: ein installiertes Python mit funktionierendem
REM  PyMeshLab (Python 3.9-3.12). Ergebnis laeuft danach OHNE Python.
REM ===================================================================
setlocal
cd /d "%~dp0"

REM --- Python mit pymeshlab finden (3.9 bevorzugt) ---
set "PY="
for %%V in (3.9 3.10 3.11 3.12) do (
    if not defined PY ( py -%%V -c "import pymeshlab" >nul 2>nul && set "PY=py -%%V" )
)
if not defined PY ( py -3 -c "import pymeshlab" >nul 2>nul && set "PY=py -3" )
if not defined PY (
    echo [FEHLER] Kein Python mit installiertem PyMeshLab gefunden.
    echo Bitte zuerst:  pip install pymeshlab
    pause & exit /b 1
)
echo [Info] Verwende: %PY%

REM --- Installationsordner dieses Python ermitteln ---
for /f "delims=" %%P in ('%PY% -c "import sys;print(sys.prefix)"') do set "PREFIX=%%P"
echo [Info] Python-Ordner: %PREFIX%

set "BUNDLE=%~dp0STL-ShrinkWrap-Portable"
if exist "%BUNDLE%" rmdir /s /q "%BUNDLE%"
mkdir "%BUNDLE%"

echo [1/3] Kopiere portablen Python ...
robocopy "%PREFIX%" "%BUNDLE%\python" /E /NFL /NDL /NJH /NJS /NP /R:1 /W:1 ^
    /XD Doc Tools test tests __pycache__ idlelib >nul
copy /y "stl_shrinkwrap.py" "%BUNDLE%\stl_shrinkwrap.py" >nul
if exist "icon.ico" copy /y "icon.ico" "%BUNDLE%\icon.ico" >nul
REM Startsprache des Bundles (de oder en); fuer ein EN-Bundle einfach "en" hineinschreiben
echo de> "%BUNDLE%\language.txt"

echo [2/3] Stelle PyInstaller bereit ...
%PY% -m pip install --user --quiet --upgrade pyinstaller

echo [3/3] Baue Starter-EXE ...
%PY% -m PyInstaller --noconfirm --clean --name "STL-ShrinkWrap" --onefile --windowed ^
    --distpath "%BUNDLE%" --workpath "%TEMP%\sw_launcher_build" --specpath "%TEMP%\sw_launcher_build" ^
    "launcher.py"
if errorlevel 1 ( echo [FEHLER] EXE-Build fehlgeschlagen. & pause & exit /b 1 )

echo.
echo [OK] Fertig:  %BUNDLE%\STL-ShrinkWrap.exe
echo Den GANZEN Ordner weitergeben (laeuft ohne Python).
pause
endlocal
