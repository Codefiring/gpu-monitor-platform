#!/bin/bash

# GPU Monitor Platform - Direct Host Deployment
# No Docker required - runs directly on the host system

set -e

echo "========================================="
echo "GPU Monitor Platform - Host Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for NVIDIA GPU
echo "Checking for NVIDIA GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}nvidia-smi not found. Please install NVIDIA drivers first.${NC}"
    exit 1
fi
nvidia-smi --query-gpu=name --format=csv,noheader
echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
echo ""

# Check for Python 3
echo "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check for pip and venv
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${RED}python3-venv not found.${NC}"
    echo "Please install it with:"
    echo "  sudo apt-get install python3-venv"
    echo "Or on other systems:"
    echo "  sudo yum install python3-venv"
    echo "  sudo dnf install python3-venv"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Create necessary directories
mkdir -p data logs logs/tasks static

# Run migrations
echo "Running database migrations..."
python manage.py migrate --run-syncdb -v 0
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Collect static files
python manage.py collectstatic --noinput -v 0
echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

# Create superuser
echo "========================================="
echo "Create admin user (Ctrl+C to skip)"
echo "========================================="
python manage.py createsuperuser || true
echo ""

# Ask about systemd installation
echo "========================================="
echo "Auto-start on boot (systemd)"
echo "========================================="
echo "Choose installation mode:"
echo "  1) User-level (no sudo required, starts on login)"
echo "  2) System-level (requires sudo, starts on boot)"
echo "  3) Skip (use ./start.sh manually)"
read -p "Enter choice [1/2/3]: " SYSTEMD_CHOICE

if [[ "$SYSTEMD_CHOICE" == "1" ]]; then
    # User-level systemd services (no sudo required)
    echo "Installing user-level systemd services..."

    # Create user systemd directory
    mkdir -p ~/.config/systemd/user

    # Substitute placeholders in service files
    sed -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
        gpu-monitor-scheduler.user.service > ~/.config/systemd/user/gpu-monitor-scheduler.service

    sed -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
        gpu-monitor-web.user.service > ~/.config/systemd/user/gpu-monitor-web.service

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

elif [[ "$SYSTEMD_CHOICE" == "2" ]]; then
    # System-level systemd services (requires sudo)
    echo "Installing system-level systemd services..."
    CURRENT_USER=$(whoami)

    # Substitute placeholders in service files
    sed -e "s|%USER%|$CURRENT_USER|g" \
        -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
        gpu-monitor-scheduler.service | sudo tee /etc/systemd/system/gpu-monitor-scheduler.service > /dev/null

    sed -e "s|%USER%|$CURRENT_USER|g" \
        -e "s|%INSTALL_DIR%|$SCRIPT_DIR|g" \
        gpu-monitor-web.service | sudo tee /etc/systemd/system/gpu-monitor-web.service > /dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable gpu-monitor-scheduler gpu-monitor-web
    sudo systemctl start gpu-monitor-scheduler gpu-monitor-web

    echo -e "${GREEN}✓ System-level systemd services installed and started${NC}"
    echo ""
    echo "Manage services with:"
    echo "  sudo systemctl status gpu-monitor-scheduler gpu-monitor-web"
    echo "  sudo systemctl restart gpu-monitor-web"
    echo "  sudo journalctl -u gpu-monitor-scheduler -f"
else
    echo ""
    echo "Start manually with:"
    echo -e "${GREEN}  ./start.sh${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Dashboard:   http://localhost:8888/"
echo "Admin Panel: http://localhost:8888/admin/"
echo ""
