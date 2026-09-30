@echo off
cd /d "%~dp0"
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Setup complete. Use run.bat to start the widget.
pause
