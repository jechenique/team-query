#!/usr/bin/env bash
# team-query installation script
# This script installs team-query using pipx

set -e

# Print with colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

printf "${BLUE}======================================${NC}\n"
printf "${BLUE}     team-query Installer Script     ${NC}\n"
printf "${BLUE}======================================${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    printf "${RED}Error: Python 3 is not installed.${NC}\n"
    printf "Please install Python 3.9 or higher and try again.\n"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(printf "%s" "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(printf "%s" "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    printf "${RED}Error: Python 3.9 or higher is required.${NC}\n"
    printf "Current version: Python %s\n" "$PYTHON_VERSION"
    exit 1
fi

printf "${GREEN}✓ Python %s detected${NC}\n" "$PYTHON_VERSION"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    printf "${YELLOW}pipx is not installed. Attempting to install it...${NC}\n"
    
    # Try to install pipx using pip
    if command -v pip3 &> /dev/null; then
        printf "Installing pipx using pip...\n"
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        printf "${RED}Error: pip3 is not installed and is required to install pipx.${NC}\n"
        printf "Please install pip for Python 3 and try again, or install pipx manually:\n"
        printf "  - macOS: brew install pipx\n"
        printf "  - Ubuntu/Debian: sudo apt install pipx\n"
        printf "  - Fedora: sudo dnf install pipx\n"
        exit 1
    fi
    
    # Check if pipx was installed successfully
    if ! command -v pipx &> /dev/null; then
        printf "${RED}Failed to install pipx. Please install it manually:${NC}\n"
        printf "  - macOS: brew install pipx\n"
        printf "  - Ubuntu/Debian: sudo apt install pipx\n"
        printf "  - Fedora: sudo dnf install pipx\n"
        exit 1
    fi
fi

printf "${GREEN}✓ pipx is installed${NC}\n"

# Ask for confirmation
printf "\nThis script will install team-query globally using pipx.\n"
read -p "Do you want to continue? (y/N) " -n 1 -r
printf "\n"
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    printf "${YELLOW}Installation cancelled.${NC}\n"
    exit 0
fi

printf "\n${BLUE}Installing team-query...${NC}\n"

# Install from PyPI using pipx
printf "Installing from PyPI using pipx...\n"
pipx install team-query

# Check if installation was successful
if command -v team-query &> /dev/null; then
    printf "\n${GREEN}✓ team-query has been successfully installed!${NC}\n"
    printf "\nYou can now use team-query from anywhere with the command:\n"
    printf "${BLUE}team-query${NC}\n"
    
    # Print version
    VERSION=$(team-query --version 2>&1)
    printf "\nInstalled version: ${GREEN}%s${NC}\n" "$VERSION"
    
    printf "\n${BLUE}To get started, try:${NC}\n"
    printf "team-query --help\n"
else
    printf "\n${YELLOW}Installation completed, but team-query command not found in PATH.${NC}\n"
    printf "This might be because pipx's bin directory is not in your PATH.\n"
    printf "Try running: ${BLUE}python3 -m pipx ensurepath${NC}\n"
    printf "Then restart your terminal or run: ${BLUE}source ~/.bashrc${NC} (or the appropriate file for your shell)\n"
fi

printf "\n${BLUE}======================================${NC}\n"
printf "${BLUE}     Installation Complete!           ${NC}\n"
printf "${BLUE}======================================${NC}\n"
