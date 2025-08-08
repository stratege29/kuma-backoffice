#!/bin/bash

# Script to set up environment and run image optimization

echo "🚀 Setting up environment for image optimization..."

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Pillow if not already installed
echo "📚 Installing dependencies..."
pip install Pillow

# Run the optimization script
echo "🖼️  Running image optimization..."
python3 optimize_images.py

# Deactivate virtual environment
deactivate

echo "✅ Done!"