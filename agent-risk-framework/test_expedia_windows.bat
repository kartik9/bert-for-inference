@echo off
REM Expedia GPT End-to-End Testing Script for Windows
REM This script will test the framework with the REAL Expedia GPT

echo ================================================================================
echo  EXPEDIA GPT END-TO-END TESTING
echo ================================================================================
echo.
echo This script will test the AI Agent Risk Assessment Framework
echo against the REAL Expedia GPT from the ChatGPT Store.
echo.
echo GPT ID: g-68d8ecbe98388191bd93f6b1d03158bf
echo GPT URL: https://chatgpt.com/g/g-68d8ecbe98388191bd93f6b1d03158bf-expedia
echo.
echo.

echo [Step 1] Checking virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [Step 2] Activating virtual environment...
call venv\Scripts\activate.bat

echo [Step 3] Checking Playwright installation...
python -c "import playwright" 2>nul
if errorlevel 1 (
    echo ERROR: Playwright not installed!
    echo Installing Playwright...
    pip install playwright
    python -m playwright install chromium
)

echo [Step 4] Checking configuration...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo Please edit .env and set USE_WEB_TESTING=true
    pause
    exit /b 1
)

findstr /C:"USE_WEB_TESTING=true" .env >nul
if errorlevel 1 (
    echo WARNING: USE_WEB_TESTING is not set to true in .env
    echo.
    echo Please edit .env and set:
    echo USE_WEB_TESTING=true
    echo WEB_TESTING_HEADLESS=false
    echo.
    pause
)

echo.
echo ================================================================================
echo  RUNNING AUTOMATED TEST
echo ================================================================================
echo.
echo This will:
echo  1. Open a browser window to ChatGPT
echo  2. Navigate to Expedia GPT
echo  3. Prompt you to log in if needed
echo  4. Send a real travel query to Expedia
echo  5. Run 3 prompt injection security tests
echo  6. Display results
echo.
echo IMPORTANT: You may need to log in to ChatGPT when the browser opens.
echo           After login, the test will continue automatically.
echo.
pause

echo.
echo [Step 5] Running test...
python test_expedia_auto.py

if errorlevel 1 (
    echo.
    echo ================================================================================
    echo  TEST FAILED
    echo ================================================================================
    echo.
    echo Please check the error messages above.
    echo Common issues:
    echo  - Need to log in to ChatGPT manually in browser
    echo  - Network connectivity issues
    echo  - ChatGPT UI changes (CSS selectors need updating)
    echo.
    echo See EXPEDIA_TEST_GUIDE.md for troubleshooting steps.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo  TEST COMPLETED SUCCESSFULLY!
echo ================================================================================
echo.
echo Next step: Run full assessment via API
echo.
echo Option 1 - Using test script:
echo   python test_real_gpt.py g-68d8ecbe98388191bd93f6b1d03158bf
echo.
echo Option 2 - Using API server:
echo   Terminal 1: run_server.bat
echo   Terminal 2: See EXPEDIA_TEST_GUIDE.md for curl commands
echo.
pause
