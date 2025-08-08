#!/bin/bash

echo "🚀 Setting up Firestore export..."

# Check if firebase-admin is installed
if [ ! -d "node_modules/firebase-admin" ]; then
    echo "📦 Installing firebase-admin..."
    npm install firebase-admin
fi

# Run the export
echo "🔄 Exporting stories from Firestore..."
node export_firestore_stories.js

# Check if export was successful
if [ -f "firestore_stories.json" ]; then
    echo "✅ Export successful!"
    echo "📊 Running auto-mapping script..."
    python3 prepare_images_auto_mapping.py
else
    echo "❌ Export failed. Check the error messages above."
fi