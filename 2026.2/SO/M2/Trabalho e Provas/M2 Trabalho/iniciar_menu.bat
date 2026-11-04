@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -X utf8 menu.py
    goto fim
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -X utf8 menu.py
    goto fim
)
where python >nul 2>nul
if not errorlevel 1 (
    python -X utf8 menu.py
    goto fim
)
echo Python nao encontrado. Instale Python 3.11 ou superior e tente novamente.
:fim
echo.
pause
endlocal
