#!/bin/bash
# Fix Firebase Storage upload with correct structure
# Upload to stories/{storyId}/image.jpg instead of stories/story_id.jpg

echo "🔧 Fixing Firebase Storage structure..."

OUTPUT_DIR="/Users/arnaudkossea/development/kumacodex/firebase_ready_images"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ Directory $OUTPUT_DIR not found!"
    exit 1
fi

echo "📁 Found images in: $OUTPUT_DIR"

# Upload each image to the correct path structure
for file in "$OUTPUT_DIR"/*.jpg; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        story_id="${filename%.jpg}"
        
        echo "📤 Uploading $filename to stories/$story_id/image.jpg..."
        
        gsutil -m cp "$file" "gs://kumafire-7864b.appspot.com/stories/$story_id/image.jpg"
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Success"
        else
            echo "   ❌ Failed"
        fi
    fi
done

echo "✅ Upload complete!"
echo ""
echo "🔗 New URL format will be:"
echo "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2F{storyId}%2Fimage.jpg?alt=media"