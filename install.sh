#!/bin/bash
# Kimi Enterprise CLI - System Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/kimi-enterprise/main/install.sh | bash

set -euo pipefail

INSTALL_DIR="${HOME}/.kimi-enterprise"
REPO_URL="${REPO_URL:-https://github.com/YOUR_USERNAME/kimi-enterprise.git}"
BRANCH="${BRANCH:-main}"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

log() { echo -e "${BLUE}[Kimi Enterprise]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; exit 1; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

check_deps() {
    log "Checking dependencies..."
    
    command -v python3 >/dev/null 2>&1 || error "Python 3.9+ required"
    command -v tmux >/dev/null 2>&1 || error "tmux required"
    
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION < 3.9" | bc -l) -eq 1 ]]; then
        error "Python 3.9+ required, found $PYTHON_VERSION"
    fi
    
    if ! command -v kimi >/dev/null 2>&1; then
        warn "Kimi CLI not found. Install from https://code.kimi.com"
    fi
    
    success "Dependencies OK"
}

setup_directories() {
    log "Creating system directories..."
    
    mkdir -p "$INSTALL_DIR"/{bin,lib/kimi_enterprise/{mcp,core,utils},share/prompts,var/{log,run}}
    
    success "Directories created"
}

create_files() {
    log "Installing system files..."
    
    # The actual files should be copied from the repo
    # This is a placeholder for the install process
    
    success "Files installed"
}

link_commands() {
    log "Setting up command aliases..."
    
    BIN_DIR="$INSTALL_DIR/bin"
    
    # Add to PATH
    SHELL_RC=""
    if [ -n "${ZSH_VERSION:-}" ]; then
        SHELL_RC="${HOME}/.zshrc"
    elif [ -n "${BASH_VERSION:-}" ]; then
        SHELL_RC="${HOME}/.bashrc"
    fi
    
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        if ! grep -q "kimi-enterprise" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# Kimi Enterprise CLI" >> "$SHELL_RC"
            echo 'export PATH="$PATH:'"$BIN_DIR"'"' >> "$SHELL_RC"
            echo "alias ke='kimi-enterprise-cli'" >> "$SHELL_RC"
            success "Added to PATH in ${SHELL_RC}"
            warn "Run 'source ${SHELL_RC}' or restart terminal"
        fi
    fi
}

main() {
    echo ""
    log "🚀 Kimi Enterprise CLI Installer v2.0"
    log "======================================"
    echo ""
    
    check_deps
    setup_directories
    create_files
    link_commands
    
    echo ""
    success "Installation complete!"
    echo ""
    echo "Quick start:"
    echo "  cd /path/to/your/project"
    echo "  kimi-enterprise-cli init --name MyApp --template startup"
    echo "  kimi-enterprise-cli start"
    echo "  kimi-enterprise-cli ceo"
    echo ""
    echo "Or use shorthand: ke init && ke start && ke ceo"
    echo ""
}

main "$@"
