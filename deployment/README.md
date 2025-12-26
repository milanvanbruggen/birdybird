# Raspberry Pi Deployment Guide

## 1. Transfer Files
Copy the entire `birdybird` folder to your Raspberry Pi.
You can use `scp` or a USB drive. If using `scp` (replace `pi@raspberrypi.local` with your Pi's username/hostname):

```bash
# Run this from your Mac
scp -r ../birdybird pi@raspberrypi.local:/home/pi/
```

## 2. Install
SSH into your Pi (or open a terminal on it) and run the install script:

```bash
cd birdybird
# Make the script executable
chmod +x deployment/install.sh
# Run the installer
./deployment/install.sh
```

This script will:
- Install system dependencies (OpenCV requires some).
- Create a python virtual environment.
- Install python libraries.
- Setup the systemd service so the app starts on boot.

## 3. Access the App
Once installed, the service will start automatically.
- **URL**: `http://<your-pi-ip>:8000`
- **Logs**: `journalctl -u birdybird -f` (to see what's happening)
- **Restart**: `sudo systemctl restart birdybird`
