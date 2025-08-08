# Scripts Directory

This directory contains utility scripts for the Kumacodex project.

## Python Scripts

### Image Management
- `clean_flags.py` - Clean up flag assets
- `copy_african_flags.py` - Copy African country flags
- `copy_story_images.py` - Copy story images
- `create_app_icon.py` - Generate app icons
- `delete_non_african_flags.py` - Remove non-African flags
- `manual_delete.py` - Manual deletion utility
- `optimize_images.py` - Image optimization
- `optimize_images_simple.py` - Simple image optimization
- `prepare_images_auto_mapping.py` - Auto-map images
- `prepare_images_for_firebase.py` - Prepare images for Firebase
- `verify_images.py` - Verify image integrity

### Audio Management
- `create_missing_sounds.py` - Create missing sound files
- `process_audio_files.py` - Process audio files
- `rename_audio_files.py` - Rename audio files
- `test_audio_integration.py` - Test audio integration

### Firebase & Firestore
- `backup_firestore.js` - Backup Firestore data
- `check_firestore_mapping.js` - Check Firestore mappings
- `export_firestore_stories.js` - Export stories from Firestore
- `firebase_upload_api.py` - Firebase upload API
- `firestore_update.js` - Update Firestore documents
- `firestore_upload.py` - Upload to Firestore
- `fix_firestore_init.py` - Fix Firestore initialization
- `fix_image_mapping.js` - Fix image mappings
- `rename_firestore_documents.py` - Rename Firestore documents
- `test_image_urls.js` - Test image URLs
- `update_firestore_correct_urls.js` - Update correct URLs

### Development Tools
- `build_app.py` - Build application
- `complete_image_migration.py` - Complete image migration
- `kuma_desktop_app.py` - Desktop GUI application
- `kuma_image_manager.py` - Image management GUI
- `test_country_codes.py` - Test country codes

## Shell Scripts

### Build & Deploy
- `build_app.sh` - Build application
- `deploy_testflight.sh` - Deploy to TestFlight
- `install_kuma_deps.sh` - Install dependencies
- `launch_kuma_gui.sh` - Launch GUI application

### Asset Management
- `clean_flags.sh` - Clean flag assets
- `clean_flags_simple.sh` - Simple flag cleanup
- `correct_upload_structure.sh` - Correct upload structure
- `fix_splash_sounds.sh` - Fix splash screen sounds
- `fix_upload_structure.sh` - Fix upload structure
- `optimize_and_upload_all.sh` - Optimize and upload all assets
- `run_optimization.sh` - Run optimization

### Firebase Operations
- `firebase_upload.sh` - Upload to Firebase
- `run_firestore_export.sh` - Export from Firestore

## Usage

Most scripts can be run directly from the scripts directory:

```bash
cd scripts
python3 script_name.py
# or
./script_name.sh
```

Make sure to install required dependencies first:

```bash
./install_kuma_deps.sh
```

## Configuration

Some scripts may require configuration files or environment variables. Check individual script documentation for requirements.