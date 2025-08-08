#!/bin/bash
# Re-upload images with correct structure for Firebase Storage rules
# From: stories/story_id.jpg
# To: stories/{storyId}/image.jpg

echo "🔧 Re-uploading with correct Firebase Storage structure..."
echo "📍 Using bucket: gs://kumafire-7864b.firebasestorage.app"

OUTPUT_DIR="/Users/arnaudkossea/development/kumacodex/firebase_ready_images"

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ Directory $OUTPUT_DIR not found!"
    exit 1
fi

echo "📁 Source directory: $OUTPUT_DIR"
echo "🎯 Target structure: stories/{storyId}/image.jpg"
echo ""

# Count files first
file_count=$(ls -1 "$OUTPUT_DIR"/*.jpg 2>/dev/null | wc -l)
echo "📊 Found $file_count images to upload"
echo ""

current=0

# Upload each image to the correct path structure
for file in "$OUTPUT_DIR"/*.jpg; do
    if [ -f "$file" ]; then
        current=$((current + 1))
        filename=$(basename "$file")
        story_id="${filename%.jpg}"
        
        echo "[$current/$file_count] 📤 $filename → stories/$story_id/image.jpg"
        
        # Upload to new structure: stories/{storyId}/image.jpg
        gsutil -m cp "$file" "gs://kumafire-7864b.firebasestorage.app/stories/$story_id/image.jpg"
        
        if [ $? -eq 0 ]; then
            echo "              ✅ Success"
        else
            echo "              ❌ Failed"
        fi
        echo ""
    fi
done

echo "✅ Upload complete!"
echo ""
echo "🔗 New URL format:"
echo "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.firebasestorage.app/o/stories%2F{storyId}%2Fimage.jpg?alt=media"
echo ""
echo "📝 Example URL:"
echo "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.firebasestorage.app/o/stories%2Fstory_ao_001%2Fimage.jpg?alt=media"