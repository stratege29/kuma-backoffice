#!/usr/bin/env python3
"""
Test script pour vérifier l'intégration audio dans kuma_desktop_app.py
"""

import os
import sys
import subprocess
from pathlib import Path

def test_ffmpeg_availability():
    """Test if ffmpeg is available"""
    print("🔍 Testing ffmpeg availability...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ffmpeg is available")
            return True
        else:
            print("❌ ffmpeg returned error")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found")
        print("Install with: brew install ffmpeg")
        return False

def test_audio_files():
    """Test if audio files exist"""
    print("\n🔍 Testing audio files...")
    audio_dir = Path("/Users/arnaudkossea/development/kumacodex/renamed_audio")
    
    if not audio_dir.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return False
    
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))
    
    if not audio_files:
        print("❌ No audio files found")
        return False
    
    print(f"✅ Found {len(audio_files)} audio files")
    for file in audio_files[:5]:  # Show first 5 files
        print(f"   - {file.name}")
    
    if len(audio_files) > 5:
        print(f"   ... and {len(audio_files) - 5} more files")
    
    return True

def test_firebase_credentials():
    """Test if Firebase credentials exist"""
    print("\n🔍 Testing Firebase credentials...")
    creds_path = Path("/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json")
    
    if not creds_path.exists():
        print(f"❌ Firebase credentials not found: {creds_path}")
        return False
    
    print("✅ Firebase credentials found")
    return True

def test_gsutil_availability():
    """Test if gsutil is available"""
    print("\n🔍 Testing gsutil availability...")
    try:
        result = subprocess.run(['gsutil', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ gsutil is available")
            return True
        else:
            print("❌ gsutil returned error")
            return False
    except FileNotFoundError:
        print("❌ gsutil not found")
        print("Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install")
        return False

def test_python_imports():
    """Test if required Python modules are available"""
    print("\n🔍 Testing Python imports...")
    
    required_modules = [
        'tkinter',
        'firebase_admin',
        'google.cloud.firestore',
        'google.cloud.storage'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            print(f"❌ {module} not available")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nInstall missing modules:")
        print(f"pip install firebase-admin google-cloud-firestore google-cloud-storage")
        return False
    
    return True

def test_file_structure():
    """Test if required files exist"""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "/Users/arnaudkossea/development/kumacodex/kuma_desktop_app.py",
        "/Users/arnaudkossea/development/kumacodex/kuma_image_manager.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {Path(file_path).name} exists")
        else:
            print(f"❌ {Path(file_path).name} not found")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🎵 Testing Kuma Audio Integration")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_python_imports,
        test_ffmpeg_availability,
        test_gsutil_availability,
        test_firebase_credentials,
        test_audio_files
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Audio integration is ready.")
        print("\nTo run the application:")
        print("python3 kuma_desktop_app.py")
    else:
        print("⚠️  Some tests failed. Fix the issues before running the application.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)