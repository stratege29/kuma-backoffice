#!/bin/bash
# Firebase Storage upload script
# Generated: 2025-07-05 14:43:14
# Project: kumafire-7864b

echo "🚀 Uploading 21 images to Firebase Storage..."

# Upload all images
for file in /Users/arnaudkossea/development/kumacodex/firebase_ready_images/*.jpg; do
    filename=$(basename "$file")
    echo "📤 Uploading $filename..."
    gsutil -m cp "$file" "gs://kumafire-7864b.appspot.com/stories/$filename"
done

echo "✅ Upload complete!"
