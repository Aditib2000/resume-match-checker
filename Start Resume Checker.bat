@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
streamlit run app.py
if errorlevel 1 (
    echo.
    echo Something went wrong starting the app - see the error above.
    pause
)
