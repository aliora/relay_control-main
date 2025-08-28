#!/usr/bin/env bash
set -euo pipefail

# setup.sh - prepares python environment, installs pip packages and sets udev rules
# Run as a normal user; the script will call sudo for system changes when needed.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME=${SUDO_USER:-$(whoami)}

echo "[setup] Repository: $REPO_DIR"
echo "[setup] Running as: $USER_NAME"

# Prevent running the whole script under sudo/root. The script will call sudo for
# specific operations. Running the script as root can make the created .venv
# owned by root and cause ensurepip failures.
if [ "$(id -u)" -eq 0 ]; then
  cat <<MSG
Do not run this script with sudo or as root.
Run as your normal user (the script will call sudo for system changes as needed):

  bash setup.sh

If you already ran this script with sudo and see the ensurepip error,
remove the root-owned virtualenv and re-run as your user:

  sudo rm -rf "$REPO_DIR/.venv"
  bash setup.sh

MSG
  exit 1
fi

# Check python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Please install python3 and retry."
  exit 1
fi

# Ensure pip3 is available
if ! command -v pip3 >/dev/null 2>&1; then
  echo "pip3 not found — installing python3-pip via apt"
  sudo apt-get update
  sudo apt-get install -y python3-pip python3-venv
fi

# Create virtualenv
if [ ! -d "$REPO_DIR/.venv" ]; then
  echo "[setup] Creating virtualenv at $REPO_DIR/.venv"
  python3 -m venv "$REPO_DIR/.venv"
fi

# Activate venv for installation
# shellcheck disable=SC1090
source "$REPO_DIR/.venv/bin/activate"

pip install --upgrade pip

if [ -f "$REPO_DIR/requirements.txt" ]; then
  echo "[setup] Installing from requirements.txt"
  pip install -r "$REPO_DIR/requirements.txt"
else
  echo "[setup] No requirements.txt found — installing recommended minimal packages"
  pip install pyserial
  # RPi.GPIO and Jetson.GPIO are hardware-specific; only install if present/desired
  echo "[setup] (Optional) To support GPIO on RPi or Jetson, install RPi.GPIO or Jetson.GPIO inside the venv when on the target hardware."
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
