#!/bin/bash
echo "Installing dependencies..."
pip uninstall -y google-generativeai
pip install -r requirements.txt
echo "Done."
