#!/bin/bash
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
pip3 uninstall -y google-generativeai
pip3 install -r requirements.txt
echo ""
echo "Dependencies installed successfully."
echo "You can now run the bot with: python3 main.py"
echo "Or run the test with: python3 tests/test_live_integration.py"
