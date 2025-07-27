#!/bin/bash

# SEO Auditor MCP Server - One-Command Installer for Claude Code
# Usage: curl -sSL https://raw.githubusercontent.com/tuckercoffey/seo-auditor-mcp/main/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/tuckercoffey/seo-auditor-mcp.git"
TEMP_DIR=$(mktemp -d)
SCRIPT_NAME="SEO Auditor MCP Installer"

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}$SCRIPT_NAME${NC}"
    echo -e "${BLUE}=================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Python
    if check_command python3; then
        PYTHON_CMD="python3"
    elif check_command python; then
        PYTHON_CMD="python"
    else
        print_error "Python 3.8+ is required but not found"
        echo "Please install Python from: https://python.org"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 1 ]] 2>/dev/null || [[ "$PYTHON_VERSION" > "3.7" ]]; then
        print_success "Python $PYTHON_VERSION detected"
    else
        print_error "Python 3.8+ is required, found $PYTHON_VERSION"
        exit 1
    fi
    
    # Check git
    if check_command git; then
        print_success "Git is available"
    else
        print_error "Git is required but not found"
        echo "Please install Git from: https://git-scm.com"
        exit 1
    fi
    
    # Check pip
    if $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        print_success "pip is available"
    else
        print_error "pip is required but not working"
        exit 1
    fi
    
    # Check Node.js (optional)
    if check_command node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js detected: $NODE_VERSION"
    else
        print_warning "Node.js not found - Lighthouse features will be limited"
        print_info "Install Node.js from: https://nodejs.org/"
    fi
}

install_seo_auditor() {
    echo
    echo "Installing SEO Auditor MCP Server..."
    
    # Clone repository to temp directory
    print_info "Downloading from $REPO_URL..."
    git clone "$REPO_URL" "$TEMP_DIR/seo-auditor-mcp" >/dev/null 2>&1
    
    # Run the Python installer
    cd "$TEMP_DIR/seo-auditor-mcp"
    
    # Make install.py executable and run it
    chmod +x install.py
    $PYTHON_CMD install.py install "$@"
}

cleanup() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --google-api-key KEY    Google API key for PageSpeed Insights"
    echo "  --ahrefs-api-key KEY    Ahrefs API key for backlink analysis"  
    echo "  --semrush-api-key KEY   SEMrush API key for competitive analysis"
    echo "  --dir DIRECTORY         Custom installation directory"
    echo "  --name NAME             Custom server name (default: seo-auditor)"
    echo "  --force                 Force reinstall if already exists"
    echo "  --help                  Show this help message"
    echo
    echo "Examples:"
    echo "  $0                                    # Basic installation"
    echo "  $0 --google-api-key YOUR_KEY        # Install with Google API"
    echo "  $0 --force                          # Force reinstall"
    echo
}

main() {
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Parse arguments
    ARGS=()
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --google-api-key|--ahrefs-api-key|--semrush-api-key|--dir|--name)
                ARGS+=("$1" "$2")
                shift 2
                ;;
            --force)
                ARGS+=("$1")
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_header
    check_prerequisites
    install_seo_auditor "${ARGS[@]}"
}

# Run main function with all arguments
main "$@"