#\!/bin/bash
# Start Samsung Galaxy S24 Emulator

echo "🚀 Starting Samsung Galaxy S24 Emulator..."

# Kill any existing emulator instances
pkill -f "emulator-5554" 2>/dev/null || true

# Start the Samsung Galaxy S24 emulator
$ANDROID_HOME/emulator/emulator -avd Galaxy_S24_API_35 \
  -no-audio \
  -netdelay none \
  -netspeed full \
  -no-snapshot-save \
  -no-boot-anim \
  -gpu host \
  -memory 8192 &

echo "📱 Samsung Galaxy S24 emulator started\!"
echo "⏳ Waiting for emulator to boot..."

# Wait for the emulator to be ready
adb wait-for-device

echo "✅ Samsung Galaxy S24 emulator is ready\!"
echo "🔗 Device ID: emulator-5554"
echo ""
echo "To run your Flutter app:"
echo "  flutter run -d emulator-5554"
echo ""
echo "Or use VS Code with the 'Launch Samsung Galaxy S24 (Debug)' configuration"
