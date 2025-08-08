#!/usr/bin/env python3
"""Test script to verify country code extraction from image filenames"""

import os
import re

OPTIMIZED_DIR = "/Users/arnaudkossea/development/kuma_upload/images_optimized"

def extract_country_code(filename):
    """Extract country code from filename (last 2 chars before extension)"""
    # Remove extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Check if filename ends with @2x (retina version)
    if name_without_ext.endswith('@2x'):
        name_without_ext = name_without_ext[:-3]
    
    # Trim any trailing spaces
    name_without_ext = name_without_ext.rstrip()
    
    # Get last 2 characters as country code
    if len(name_without_ext) >= 2:
        # Handle potential space before country code (e.g., "Maria Luiza CV ")
        parts = name_without_ext.rsplit(' ', 1)
        if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isalpha():
            country_code = parts[1].upper()
            story_identifier = parts[0].strip()
        else:
            country_code = name_without_ext[-2:].upper()
            story_identifier = name_without_ext[:-2].rstrip(' _-')
        return country_code, story_identifier
    
    return None, None

# Test with all images
print("🔍 Testing country code extraction:\n")

image_files = [f for f in os.listdir(OPTIMIZED_DIR) 
               if f.endswith('.jpg') and not f.endswith('@2x.jpg')]

country_codes = {}

for img in sorted(image_files):
    cc, identifier = extract_country_code(img)
    if cc:
        if cc not in country_codes:
            country_codes[cc] = []
        country_codes[cc].append((img, identifier))
        print(f"✅ {img}")
        print(f"   → Country: {cc}, Story: {identifier}")
    else:
        print(f"❌ {img} - Could not extract country code")
    print()

print("\n📊 Summary by country:")
for cc in sorted(country_codes.keys()):
    print(f"\n{cc}: {len(country_codes[cc])} stories")
    for img, identifier in country_codes[cc]:
        print(f"   - {identifier}")

print(f"\n✅ Total countries: {len(country_codes)}")
print(f"✅ Total images: {len(image_files)}")