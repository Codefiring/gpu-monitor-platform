#!/bin/bash

# GPU Monitor Platform - One-Click Deployment Script
# For single-server GPU monitoring and task management

set -e

echo "========================================="
echo "GPU Monitor Platform Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run this script as root${NC}"
    exit 1
fi

# Check for NVIDIA GPU
echo "Checking for NVIDIA GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}nvidia-smi not found. Please install NVIDIA drivers first.${NC}"
    exit 1
fi

nvidia-smi --query-gpu=name --format=csv,noheader
echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
echo ""

# Check for Docker
echo "Checking for Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✓ Docker installed${NC}"
    echo -e "${YELLOW}Please log out and log back in for Docker permissions to take effect${NC}"
    exit 0
fi

echo -e "${GREEN}✓ Docker found${NC}"
echo ""

# Check for Docker Compose
echo "Checking for Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
fi

echo -e "${GREEN}✓ Docker Compose found${NC}"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data logs logs/tasks static
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Build and start services
echo "Building Docker image..."
docker build -f Dockerfile.simple -t gpu-monitor:latest .
echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

echo "Starting services..."
docker-compose -f docker-compose.simple.yml up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be ready
echo "Waiting for services to initialize..."
sleep 10

# Create superuser
echo ""
echo "========================================="
echo "Creating admin user..."
echo "========================================="
docker exec -it gpu_monitor python manage.py createsuperuser

echo ""
echo "========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "========================================="
echo ""
echo "Access the platform at:"
echo -e "${GREEN}Dashboard: http://localhost:8888/${NC}"
echo -e "${GREEN}Admin Panel: http://localhost:8888/admin/${NC}"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.simple.yml logs -f"
echo ""
echo "To stop the platform:"
echo "  docker-compose -f docker-compose.simple.yml down"
echo ""
echo "To restart the platform:"
echo "  docker-compose -f docker-compose.simple.yml restart"
echo ""
