#!/bin/bash

echo "🎯 CREATING GEANT OFFICIAL APP ICONS"
echo "=================================="

# Source image
SOURCE="geant_official_logo.png"

# Standard PWA icon sizes
sizes=("16" "32" "48" "72" "96" "128" "144" "152" "192" "384" "512")

echo "📱 Creating app icons from official Geant logo..."

for size in "${sizes[@]}"; do
    echo "Creating ${size}x${size} icon..."
    
    # Create icon with transparent background, centered logo
    convert "$SOURCE" \
        -background transparent \
        -gravity center \
        -resize "${size}x${size}" \
        -extent "${size}x${size}" \
        "icon-${size}x${size}.png"
    
    echo "✓ Created icon-${size}x${size}.png"
done

# Create Apple touch icons (180x180 for iOS)
echo "🍎 Creating Apple touch icons..."
convert "$SOURCE" \
    -background transparent \
    -gravity center \
    -resize "180x180" \
    -extent "180x180" \
    "apple-touch-icon.png"

# Create maskable icons with proper safe area (20% padding for Android adaptive icons)
echo "🤖 Creating Android maskable icons..."
for size in "192" "512"; do
    # Calculate safe area (80% of the size)
    safe_size=$((size * 80 / 100))
    convert "$SOURCE" \
        -background transparent \
        -gravity center \
        -resize "${safe_size}x${safe_size}" \
        -extent "${size}x${size}" \
        "icon-${size}x${size}-maskable.png"
    echo "✓ Created maskable icon-${size}x${size}-maskable.png"
done

# Create favicon.ico with multiple sizes
echo "🌐 Creating favicon.ico..."
convert "$SOURCE" \
    -background transparent \
    -gravity center \
    \( -clone 0 -resize 16x16 \) \
    \( -clone 0 -resize 32x32 \) \
    \( -clone 0 -resize 48x48 \) \
    -delete 0 \
    favicon.ico

# Create standard favicon.png
convert "$SOURCE" \
    -background transparent \
    -gravity center \
    -resize "32x32" \
    -extent "32x32" \
    "favicon.png"

# Create high-resolution preview
echo "🖼️ Creating preview images..."
convert \
  \( icon-72x72.png -resize 72x72 -background white -gravity center -extent 80x80 \) \
  \( icon-128x128.png -resize 128x128 -background white -gravity center -extent 136x136 \) \
  \( icon-192x192.png -resize 192x192 -background white -gravity center -extent 200x200 \) \
  \( icon-512x512.png -resize 256x256 -background white -gravity center -extent 264x264 \) \
  +append \
  -background lightgray \
  -gravity center \
  -extent 800x320 \
  official_icon_preview.png

echo ""
echo "✅ ALL OFFICIAL GEANT ICONS CREATED SUCCESSFULLY!"
echo "📊 Generated $(ls -1 icon-*.png | wc -l) app icons"
echo "📱 Generated $(ls -1 *maskable*.png | wc -l) maskable icons"
echo "🌐 Generated favicon.ico and favicon.png"
echo "🍎 Generated Apple touch icon"
