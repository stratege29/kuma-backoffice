#!/bin/bash

echo "🔧 Fixing splash sounds issue..."

# Check if splash_welcome.mp3 exists
if [ -f "assets/sounds/splash_welcome.mp3" ]; then
    echo "✅ splash_welcome.mp3 exists"
    
    # Create splash_transition.mp3 if it doesn't exist
    if [ ! -f "assets/sounds/splash_transition.mp3" ]; then
        echo "❌ splash_transition.mp3 missing - creating copy"
        cp assets/sounds/splash_welcome.mp3 assets/sounds/splash_transition.mp3
        echo "✅ splash_transition.mp3 created"
    else
        echo "✅ splash_transition.mp3 exists"
    fi
else
    echo "❌ splash_welcome.mp3 is missing!"
fi

# Check if splash_error.mp3 exists (used in error cases)
if [ ! -f "assets/sounds/splash_error.mp3" ]; then
    echo "❌ splash_error.mp3 missing - creating copy from quiz_incorrect"
    if [ -f "assets/sounds/quiz_incorrect.mp3" ]; then
        cp assets/sounds/quiz_incorrect.mp3 assets/sounds/splash_error.mp3
        echo "✅ splash_error.mp3 created"
    fi
fi

echo ""
echo "📁 Current sound files:"
ls -la assets/sounds/*.mp3

echo ""
echo "🧹 Cleaning Flutter cache..."
flutter clean

echo ""
echo "📦 Getting Flutter packages..."
flutter pub get

echo ""
echo "✅ Done! Now run 'flutter run' to test"