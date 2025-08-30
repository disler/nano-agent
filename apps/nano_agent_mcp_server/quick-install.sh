#!/bin/bash

# Nano Agent - Quick Installation Script
# For users who want to get up and running quickly

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "\n${BOLD}${BLUE}🚀 Nano Agent - Quick Install${NC}\n"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Python 3.9+ required. Install from https://python.org${NC}"
    exit 1
fi

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${BLUE}Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install nano-agent
echo -e "${BLUE}Installing nano-agent...${NC}"
uv tool install --force .

# Create config directory
mkdir -p "$HOME/.nano-cli"

# Copy environment file
if [ -f ".env.sample" ] && [ ! -f ".env" ]; then
    cp .env.sample .env
fi

echo -e "${GREEN}✅ Nano Agent installed successfully!${NC}"
echo
echo -e "${BOLD}Quick start:${NC}"
echo "  • CLI: nano-cli run 'Create a hello world script'"
echo "  • MCP: Add to Claude Desktop config:"
echo
echo '  {'
echo '    "mcpServers": {'
echo '      "nano-agent": {'
echo '        "command": "nano-agent"'
echo '      }'
echo '    }'
echo '  }'
echo
echo -e "${YELLOW}Note: Configure API keys in .env file for full functionality${NC}"