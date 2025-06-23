#!/bin/bash
# Korean font download script for Docker container

# Create fonts directory
mkdir -p /app/fonts

# Download Nanum Gothic font
echo "Downloading Korean fonts..."
cd /app/fonts

# Download from official source
wget -q https://github.com/naver/nanumfont/releases/download/VER2.5/NanumGothic.ttf

# Check if download was successful
if [ -f "NanumGothic.ttf" ]; then
    echo "Korean font downloaded successfully"
    chmod 644 NanumGothic.ttf
else
    echo "Failed to download Korean font"
    exit 1
fi

echo "Font setup complete"