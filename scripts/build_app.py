#!/usr/bin/env python3
"""
Build script to create executable for Kuma Image Manager
"""

import subprocess
import sys
import os
import shutil

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller"""
    print("📦 Installing PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_spec_file():
    """Create PyInstaller spec file with icon and resources"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['kuma_desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('kuma_image_manager.py', '.'),
        ('verify_images.py', '.'),
        ('README_BACKOFFICE.md', '.'),
    ],
    hiddenimports=[
        'PIL',
        'PIL._imaging',
        'firebase_admin',
        'google.auth',
        'google.auth.transport.requests',
        'google.oauth2.service_account',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KumaImageManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='KumaImageManager.app',
    icon=None,
    bundle_identifier='com.kuma.imagemanager',
    info_plist={
        'CFBundleDisplayName': 'Kuma Image Manager',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
)
"""
    
    with open('kuma_app.spec', 'w') as f:
        f.write(spec_content.strip())
    
    print("📝 Created kuma_app.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    # Run PyInstaller
    result = subprocess.run([
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'kuma_app.spec'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        return True
    else:
        print("❌ Build failed:")
        print(result.stderr)
        return False

def create_installer_script():
    """Create installation script for dependencies"""
    installer_script = """#!/bin/bash
# Kuma Image Manager Installer

echo "🖼️  Kuma Image Manager Setup"
echo "=========================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install Pillow firebase-admin google-auth PyInstaller

# Check Google Cloud SDK
if ! command -v gsutil &> /dev/null; then
    echo "⚠️  Google Cloud SDK not found"
    echo "📝 To install: brew install google-cloud-sdk"
    echo "   Then run: gcloud auth login"
else
    echo "✅ Google Cloud SDK found"
fi

echo ""
echo "✅ Setup complete!"
echo "🚀 You can now run: ./KumaImageManager.app"
"""
    
    with open('install_dependencies.sh', 'w') as f:
        f.write(installer_script)
    
    os.chmod('install_dependencies.sh', 0o755)
    print("📝 Created install_dependencies.sh")

def create_dmg_macos():
    """Create DMG file for macOS distribution"""
    if sys.platform != "darwin":
        print("📱 DMG creation is only available on macOS")
        return
    
    app_path = "dist/KumaImageManager.app"
    if not os.path.exists(app_path):
        print("❌ App bundle not found")
        return
    
    print("📱 Creating DMG installer...")
    
    # Create DMG
    dmg_script = f"""
    hdiutil create -volname "Kuma Image Manager" -srcfolder "{app_path}" -ov -format UDZO "dist/KumaImageManager.dmg"
    """
    
    result = subprocess.run(dmg_script, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ DMG created: dist/KumaImageManager.dmg")
    else:
        print("❌ DMG creation failed:")
        print(result.stderr)

def main():
    """Main build process"""
    print("🏗️  Kuma Image Manager Build Script")
    print("=" * 40)
    
    # Check dependencies
    if not check_pyinstaller():
        install_pyinstaller()
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if build_executable():
        print("\n🎉 Build Process Complete!")
        
        if sys.platform == "darwin":  # macOS
            print("📱 macOS App Bundle: dist/KumaImageManager.app")
            
            # Create DMG
            create_dmg = input("Create DMG installer? (y/n): ").lower() == 'y'
            if create_dmg:
                create_dmg_macos()
                
        elif sys.platform == "win32":  # Windows
            print("🪟 Windows Executable: dist/KumaImageManager.exe")
        else:  # Linux
            print("🐧 Linux Executable: dist/KumaImageManager")
        
        # Create installer script
        create_installer_script()
        
        print("\n📋 Distribution Files:")
        for item in os.listdir("dist"):
            size = os.path.getsize(f"dist/{item}")
            print(f"   📁 {item} ({size/1024/1024:.1f} MB)")
        
        print("\n🎯 Next Steps:")
        print("   1. Test the executable")
        print("   2. Distribute with install_dependencies.sh")
        print("   3. Include README_BACKOFFICE.md")
        
    else:
        print("❌ Build failed")

if __name__ == "__main__":
    main()