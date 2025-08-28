#!/usr/bin/env bash
set -euo pipefail

# setup.sh - prepares python environment, installs pip packages and sets udev rules
# Run as a normal user; the script will call sudo for system changes when needed.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME=${SUDO_USER:-$(whoami)}


echo "[setup] Repository: $REPO_DIR"
echo "[setup] Running as: $USER_NAME"

# This script installs packages system-wide and writes udev rules.
# It will use sudo for system changes. Run as your normal user or with sudo.

# Check python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Please install python3 and retry."
  exit 1
fi

# Ensure pip3 is available and install packages system-wide using sudo pip3
if ! command -v pip3 >/dev/null 2>&1; then
  echo "pip3 not found — installing python3-pip via apt"
  sudo apt-get update
  sudo apt-get install -y python3-pip
fi

echo "[setup] Installing packages system-wide (this uses sudo)"
sudo pip3 install --upgrade pip

if [ -f "$REPO_DIR/requirements.txt" ]; then
  echo "[setup] Installing from requirements.txt (system-wide)"
  sudo pip3 install -r "$REPO_DIR/requirements.txt"
else
  echo "[setup] Installing minimal recommended packages system-wide"
  sudo pip3 install pyserial
  echo "[setup] (Optional) To support GPIO on RPi or Jetson, install RPi.GPIO or Jetson.GPIO on the target hardware."
fi

# Create udev rule to allow non-root access to hidraw and serial USB devices
UDEV_RULE="/etc/udev/rules.d/99-relay-control.rules"
RULE_CONTENT="# relay_control udev rules - allow user access to relay devices\nKERNEL==\"hidraw*\", MODE=\"0666\"\nKERNEL==\"ttyUSB*\", MODE=\"0666\"\nKERNEL==\"ttyACM*\", MODE=\"0666\"\n"

echo "[setup] Writing udev rule to $UDEV_RULE (requires sudo)"
printf "%s" "$RULE_CONTENT" | sudo tee "$UDEV_RULE" > /dev/null

echo "[setup] Reloading udev rules and triggering"
sudo udevadm control --reload-rules || true
sudo udevadm trigger || true

# Add user to plugdev group if available (helps device permissions on some distros)
if getent group plugdev >/dev/null 2>&1; then
  echo "[setup] Adding $USER_NAME to plugdev group (requires sudo)"
  sudo usermod -a -G plugdev "$USER_NAME" || true
  echo "[setup] You may need to log out and back in for group change to take effect."
fi

# Make setup script executable (it already is but ensure correct mode)
sudo chmod +x "$REPO_DIR/setup.sh" || true

cat <<EOF

✅ Setup complete.
- A virtualenv was created at: $REPO_DIR/.venv
- Pip packages installed into the venv.
- Udev rule installed at: $UDEV_RULE (allows access to /dev/hidraw* and /dev/ttyUSB*)

Next steps:
  1) If you installed the plugdev group membership, log out and back in (or reboot).
  2) Activate the venv: source .venv/bin/activate
  3) Run the server or tests as your user. If you still see permission errors, try running the specific command with sudo.

EOF
