@echo off
echo Installing dependencies...
:: Ensure no conflicting packages
pip uninstall -y google-generativeai
pip install -r requirements.txt
echo Done.
pause
