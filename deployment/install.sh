#!/bin/bash

# BirdyBird Installation Script for Raspberry Pi
set -e

echo "🐦 Installing BirdyBird..."

# 1. Update and install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv libgl1-mesa-glx libgtk2.0-dev pkg-config

# 2. Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
else
    echo "🐍 Virtual environment already exists."
fi

# 3. Install Python requirements
echo "📥 Installing Python requirements (this may take a while)..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Configure systemd service
echo "⚙️ Configuring systemd service..."
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)

SERVICE_FILE="deployment/birdybird.service"
TARGET_SERVICE_FILE="/etc/systemd/system/birdybird.service"

# Create a temporary service file with correct paths
cp "$SERVICE_FILE" birdybird.service.tmp
sed -i "s|__USER__|$CURRENT_USER|g" birdybird.service.tmp
sed -i "s|__DIR__|$CURRENT_DIR|g" birdybird.service.tmp

echo "Installing service to $TARGET_SERVICE_FILE..."
sudo mv birdybird.service.tmp "$TARGET_SERVICE_FILE"

# 5. Enable and start service
echo "🚀 Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable birdybird
sudo systemctl restart birdybird

echo "✅ Installation complete!"
echo "📡 You should be able to access the app at http://$(hostname -I | awk '{print $1}'):8000"
echo "Check status with: sudo systemctl status birdybird"
