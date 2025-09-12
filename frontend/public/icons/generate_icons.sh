#!/bin/bash

# Source image
SOURCE="original_logo.png"

# Create square versions with proper padding for app icons
# Standard PWA icon sizes
sizes=("16" "32" "48" "72" "96" "128" "144" "152" "192" "384" "512")

echo "Creating app icons from Geant Hypermarket logo..."

for size in "${sizes[@]}"; do
    echo "Creating ${size}x${size} icon..."
    
    # Create icon with white background and centered logo
    convert "$SOURCE" \
        -background white \
        -gravity center \
        -resize "${size}x${size}" \
        -extent "${size}x${size}" \
        "icon-${size}x${size}.png"
    
    echo "✓ Created icon-${size}x${size}.png"
done

# Create Apple touch icons
echo "Creating Apple touch icons..."
convert "$SOURCE" \
    -background white \
    -gravity center \
    -resize "180x180" \
    -extent "180x180" \
    "apple-touch-icon.png"

# Create maskable icons (with extra padding for Android adaptive icons)
echo "Creating maskable icons..."
for size in "192" "512"; do
    convert "$SOURCE" \
        -background white \
        -gravity center \
        -resize "$((size-size/4))x$((size-size/4))" \
        -extent "${size}x${size}" \
        "icon-${size}x${size}-maskable.png"
    echo "✓ Created maskable icon-${size}x${size}-maskable.png"
done

# Create favicon.ico with multiple sizes
echo "Creating favicon.ico..."
convert "$SOURCE" \
    -background white \
    -gravity center \
    \( -clone 0 -resize 16x16 \) \
    \( -clone 0 -resize 32x32 \) \
    \( -clone 0 -resize 48x48 \) \
    -delete 0 \
    favicon.ico

# Create standard favicon.png
convert "$SOURCE" \
    -background white \
    -gravity center \
    -resize "32x32" \
    -extent "32x32" \
    "favicon.png"

echo "✓ All icons created successfully!"
ls -la *.png *.ico
