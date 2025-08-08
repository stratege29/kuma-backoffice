#!/bin/bash
# Quick launcher for Kuma Image Manager GUI

echo "🖼️  Launching Kuma Image Manager..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 first."
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."

# Check Pillow
python3 -c "import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing Pillow..."
    pip3 install Pillow
fi

# Check Firebase Admin
python3 -c "import firebase_admin" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing Firebase Admin..."
    pip3 install firebase-admin
fi

# Check tkinter (usually comes with Python)
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ tkinter not available. On Ubuntu/Debian: sudo apt-get install python3-tk"
    exit 1
fi

# Launch the GUI
echo "🚀 Starting GUI application..."
python3 kuma_desktop_app.py