#!/usr/bin/env bash
# Simple team-query installation script
set -e

# Basic output functions
log() { echo "$@"; }
success() { echo "✓ $@"; }
error() { echo "Error: $@"; exit 1; }

log "========================================"
log "     team-query Installer Script"
log "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3.9 or higher."
fi

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]); then
    error "Python 3.9 or higher is required. Current version: Python $PY_VERSION"
fi

success "Python $PY_VERSION detected"

# Check pipx
if ! command -v pipx &> /dev/null; then
    log "pipx is not installed. Installing it..."
    
    if command -v pip3 &> /dev/null; then
        python3 -m pip install --user pipx
        python3 -m pipx ensurepath
    else
        error "pip3 is not installed. Please install pip for Python 3."
    fi
    
    if ! command -v pipx &> /dev/null; then
        error "Failed to install pipx. Please install it manually."
    fi
fi

success "pipx is installed"

# Skip interactive prompts when running via pipe (like curl | bash)
if [ -t 0 ]; then
    # Running in a terminal with stdin attached - ask for confirmation
    log ""
    log "This script will install team-query globally using pipx."
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Installation cancelled."
        exit 0
    fi
else
    # Running via pipe - proceed automatically
    log ""
    log "This script will install team-query globally using pipx."
    log "Proceeding automatically (non-interactive mode)..."
fi

log ""
log "Installing team-query..."
log "Running: pipx install team-query"
pipx install team-query

# Check installation
if command -v team-query &> /dev/null; then
    success "team-query has been successfully installed!"
    log ""
    log "You can now use team-query from anywhere with the command:"
    log "team-query"
    
    VERSION=$(team-query --version 2>&1)
    log ""
    log "Installed version: $VERSION"
    
    log ""
    log "To get started, try:"
    log "team-query --help"
else
    log ""
    log "Installation completed, but team-query command not found in PATH."
    log "This might be because pipx's bin directory is not in your PATH."
    log "Try running: python3 -m pipx ensurepath"
    log "Then restart your terminal or source your shell configuration file."
fi

log ""
log "========================================"
log "     Installation Complete!"
log "========================================"
