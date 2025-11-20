@echo off
echo ========================================
echo AI Diagram Generator - Streamlit Version  
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and add it to your PATH
    pause
    exit /b 1
)

echo Python found. Checking dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting AI Diagram Generator (Streamlit version)...
echo Application will open in your default browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

streamlit run src/streamlit_app.py

echo.
echo Application stopped.
pause
