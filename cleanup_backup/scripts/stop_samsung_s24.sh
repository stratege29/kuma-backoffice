#\!/bin/bash
# Stop Samsung Galaxy S24 Emulator

echo "🛑 Stopping Samsung Galaxy S24 Emulator..."

# Kill the emulator process
adb -s emulator-5554 emu kill 2>/dev/null || true
pkill -f "Galaxy_S24_API_35" 2>/dev/null || true

echo "✅ Samsung Galaxy S24 emulator stopped\!"
