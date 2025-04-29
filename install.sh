#!/bin/bash
# team-query installation script
# This script installs team-query using pipx

set -e

# Print with colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}     team-query Installer Script     ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo -e "Please install Python 3.9 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo -e "${RED}Error: Python 3.9 or higher is required.${NC}"
    echo -e "Current version: Python $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo -e "${YELLOW}pipx is not installed. Attempting to install it...${NC}"
    
    # Try to install pipx using pip
    if command -v pip3 &> /dev/null; then
        echo -e "Installing pipx using pip..."
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        echo -e "${RED}Error: pip3 is not installed and is required to install pipx.${NC}"
        echo -e "Please install pip for Python 3 and try again, or install pipx manually:"
        echo -e "  - macOS: brew install pipx"
        echo -e "  - Ubuntu/Debian: sudo apt install pipx"
        echo -e "  - Fedora: sudo dnf install pipx"
        exit 1
    fi
    
    # Check if pipx was installed successfully
    if ! command -v pipx &> /dev/null; then
        echo -e "${RED}Failed to install pipx. Please install it manually:${NC}"
        echo -e "  - macOS: brew install pipx"
        echo -e "  - Ubuntu/Debian: sudo apt install pipx"
        echo -e "  - Fedora: sudo dnf install pipx"
        exit 1
    fi
fi

echo -e "${GREEN}✓ pipx is installed${NC}"

# Ask for confirmation
echo -e "\nThis script will install team-query globally using pipx."
read -p "Do you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled.${NC}"
    exit 0
fi

echo -e "\n${BLUE}Installing team-query...${NC}"

# Install from PyPI using pipx
echo -e "Installing from PyPI using pipx..."
pipx install team-query

# Check if installation was successful
if command -v team-query &> /dev/null; then
    echo -e "\n${GREEN}✓ team-query has been successfully installed!${NC}"
    echo -e "\nYou can now use team-query from anywhere with the command:"
    echo -e "${BLUE}team-query${NC}"
    
    # Print version
    VERSION=$(team-query --version 2>&1)
    echo -e "\nInstalled version: ${GREEN}$VERSION${NC}"
    
    echo -e "\n${BLUE}To get started, try:${NC}"
    echo -e "team-query --help"
else
    echo -e "\n${YELLOW}Installation completed, but team-query command not found in PATH.${NC}"
    echo -e "This might be because pipx's bin directory is not in your PATH."
    echo -e "Try running: ${BLUE}python3 -m pipx ensurepath${NC}"
    echo -e "Then restart your terminal or run: ${BLUE}source ~/.bashrc${NC} (or the appropriate file for your shell)"
fi

echo -e "\n${BLUE}======================================${NC}"
echo -e "${BLUE}     Installation Complete!           ${NC}"
echo -e "${BLUE}======================================${NC}"
