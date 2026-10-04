@echo off
cd /d "%~dp0"
for %%V in (3.12 3.11 3.10) do (
 py -%%V -c "import sys" >nul 2>nul
 if not errorlevel 1 (
  py -%%V run.py --open-browser %*
  goto done
 )
)
python run.py --open-browser %*
:done
if errorlevel 1 pause
