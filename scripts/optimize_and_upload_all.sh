#!/bin/bash

echo "🚀 Complete Image Optimization and Upload Pipeline"
echo "================================================"

# Step 1: Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install it first."
    exit 1
fi

# Step 2: Install dependencies
echo "📦 Installing dependencies..."
if [ ! -d "node_modules" ]; then
    npm init -y
fi
npm install firebase-admin

# Step 3: Export Firestore data
echo "🔄 Exporting stories from Firestore..."
node export_firestore_stories.js

if [ ! -f "firestore_stories.json" ]; then
    echo "❌ Firestore export failed!"
    exit 1
fi

# Step 4: Run auto-mapping
echo "🗺️  Running auto-mapping script..."
python3 prepare_images_auto_mapping.py

# Step 5: Check results
if [ -f "mapping_report.json" ]; then
    echo "✅ Mapping complete! Check mapping_report.json for details."
    
    # Show summary
    echo ""
    echo "📊 Mapping Summary:"
    python3 -c "
import json
with open('mapping_report.json', 'r') as f:
    report = json.load(f)
    summary = report['summary']
    print(f'   Total mapped: {summary[\"total_mapped\"]}')
    print(f'   High confidence: {summary[\"high_confidence\"]}')
    print(f'   Medium confidence: {summary[\"medium_confidence\"]}')
    print(f'   Low confidence: {summary[\"low_confidence\"]}')
    print(f'   Ambiguous: {summary[\"ambiguous\"]}')
    print(f'   Unmatched: {summary[\"unmatched\"]}')
"
    
    echo ""
    echo "📁 Output files created:"
    echo "   - firebase_ready_images/ (optimized images)"
    echo "   - firebase_upload_auto.sh (upload script)"
    echo "   - firestore_update_auto.js (Firestore update script)"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Review mapping_report.json"
    echo "2. Update YOUR-PROJECT-ID in the scripts"
    echo "3. Run ./firebase_upload_auto.sh"
    echo "4. Run firestore_update_auto.js"
else
    echo "❌ Mapping failed!"
    exit 1
fi