@echo off
echo Installing dependencies...
python -m pip install --upgrade pip
pip uninstall -y google-generativeai
pip install -r requirements.txt
echo.
echo Dependencies installed successfully.
echo You can now run the bot with: python main.py
echo Or run the test with: python tests/test_live_integration.py
echo.
pause
