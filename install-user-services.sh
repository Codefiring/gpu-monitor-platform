#!/bin/bash

# Install user-level systemd services (no sudo required)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Installing User-level Systemd Services"
echo "========================================="
echo ""

# Create user systemd directory
mkdir -p ~/.config/systemd/user

# Substitute placeholders in service files
sed -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
    gpu-monitor-scheduler.user.service > ~/.config/systemd/user/gpu-monitor-scheduler.service

sed -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
    gpu-monitor-web.user.service > ~/.config/systemd/user/gpu-monitor-web.service

# Reload and enable services
systemctl --user daemon-reload
systemctl --user enable gpu-monitor-scheduler gpu-monitor-web
systemctl --user start gpu-monitor-scheduler gpu-monitor-web

echo -e "${GREEN}✓ User-level systemd services installed and started${NC}"
echo ""
echo "Manage services with:"
echo "  systemctl --user status gpu-monitor-scheduler gpu-monitor-web"
echo "  systemctl --user restart gpu-monitor-web"
echo "  journalctl --user -u gpu-monitor-scheduler -f"
echo ""
echo -e "${YELLOW}Note: Services start on login, not on boot${NC}"
echo "To enable on boot, run: sudo loginctl enable-linger $(whoami)"
echo ""
