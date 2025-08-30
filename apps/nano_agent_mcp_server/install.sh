#!/bin/bash

# Nano Agent MCP Server - Production Installation Script
# This script installs nano-agent for end users who want to use it with Claude Desktop or other MCP clients

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.nano-agent"
CONFIG_DIR="$HOME/.nano-cli"
SERVICE_NAME="nano-agent"
GITHUB_REPO="https://github.com/your-org/nano-agent"  # Update with actual repo
VERSION="latest"

print_header() {
    echo -e "\n${BOLD}${BLUE}🤖 Nano Agent MCP Server - Production Installation${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_step() {
    echo -e "${BOLD}${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

check_requirements() {
    print_step "Checking system requirements..."
    
    # Check Python 3.9+
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
        REQUIRED_VERSION="3.9"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
            echo "Please install Python 3.9 or higher from https://python.org"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        echo "Please install Python 3.9+ from https://python.org"
        exit 1
    fi
    
    # Check uv (Python package manager)
    if ! command -v uv >/dev/null 2>&1; then
        print_warning "uv not found. Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if ! command -v uv >/dev/null 2>&1; then
            print_error "Failed to install uv"
            echo "Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
            exit 1
        fi
        print_success "uv installed successfully"
    else
        print_success "uv found"
    fi
    
    # Check if running on supported OS
    OS=$(uname -s)
    case "$OS" in
        Darwin*)
            print_success "macOS detected"
            ;;
        Linux*)
            print_success "Linux detected"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            print_success "Windows detected"
            ;;
        *)
            print_warning "Unsupported OS: $OS (continuing anyway)"
            ;;
    esac
}

install_nano_agent() {
    print_step "Installing Nano Agent MCP Server..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    
    # Clone or download the repository
    if [ -d "$INSTALL_DIR/nano-agent" ]; then
        print_step "Updating existing installation..."
        cd "$INSTALL_DIR/nano-agent"
        git pull origin main || {
            print_warning "Git pull failed, removing and re-cloning..."
            cd "$HOME"
            rm -rf "$INSTALL_DIR/nano-agent"
            git clone "$GITHUB_REPO.git" "$INSTALL_DIR/nano-agent"
        }
    else
        print_step "Downloading Nano Agent..."
        # For now, copy from current directory since we don't have the GitHub repo
        if [ -f "$(pwd)/pyproject.toml" ]; then
            # We're in the nano-agent directory
            cp -r "$(pwd)" "$INSTALL_DIR/nano-agent"
        else
            print_error "Unable to find nano-agent source code"
            echo "Please run this script from the nano-agent directory or provide the GitHub repository"
            exit 1
        fi
    fi
    
    cd "$INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server"
    
    # Install dependencies
    print_step "Installing dependencies..."
    if [ -f ".env.sample" ] && [ ! -f ".env" ]; then
        cp .env.sample .env
        print_success "Created .env file from template"
    fi
    
    uv sync
    print_success "Dependencies installed"
    
    # Install as a tool
    print_step "Installing nano-agent command..."
    uv tool install --force .
    print_success "nano-agent command installed"
}

setup_configuration() {
    print_step "Setting up configuration..."
    
    # Create config directory
    mkdir -p "$CONFIG_DIR"
    
    # Create default configuration
    cat > "$CONFIG_DIR/config.json" << EOF
{
  "default_model": "gpt-oss:20b",
  "default_provider": "ollama",
  "default_temperature": 0.7,
  "default_max_tokens": 4000
}
EOF
    
    print_success "Default configuration created at $CONFIG_DIR/config.json"
    
    # Setup example hooks if user wants them
    if [ -f "$INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/examples/setup_hooks.sh" ]; then
        echo
        read -p "$(echo -e "${YELLOW}Would you like to install example hooks? (y/N): ${NC}")" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server"
            ./examples/setup_hooks.sh
            print_success "Example hooks installed"
        fi
    fi
}

setup_claude_desktop() {
    print_step "Setting up Claude Desktop integration..."
    
    # Detect Claude Desktop config location
    CLAUDE_CONFIG_DIR=""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        CLAUDE_CONFIG_DIR="$APPDATA/Claude"
    fi
    
    if [ -n "$CLAUDE_CONFIG_DIR" ]; then
        mkdir -p "$CLAUDE_CONFIG_DIR"
        
        # Get the uv tool installation path
        UV_TOOL_BIN="$(uv tool dir)/bin"
        NANO_AGENT_PATH="$UV_TOOL_BIN/nano-agent"
        
        # Check if nano-agent is in PATH or use full path
        if command -v nano-agent >/dev/null 2>&1; then
            NANO_AGENT_CMD="nano-agent"
        else
            NANO_AGENT_CMD="$NANO_AGENT_PATH"
        fi
        
        # Create Claude Desktop MCP configuration
        cat > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" << EOF
{
  "mcpServers": {
    "nano-agent": {
      "command": "$NANO_AGENT_CMD",
      "args": [],
      "env": {
        "NANO_AGENT_MCP_MODE": "true"
      }
    }
  }
}
EOF
        
        print_success "Claude Desktop configuration created at $CLAUDE_CONFIG_DIR/claude_desktop_config.json"
        
        cat << EOF

${BOLD}${GREEN}Claude Desktop Setup Complete!${NC}

To use nano-agent with Claude Desktop:
1. Restart Claude Desktop if it's running
2. Open Claude Desktop and look for the 🔌 icon
3. Nano-agent tools should appear in the MCP section

Available tools in Claude Desktop:
• prompt_nano_agent - Execute autonomous agent tasks
• get_session_info - View session information  
• list_sessions - List your conversation sessions
• get_available_models - Check available AI models
• get_server_capabilities - View server features

EOF
    else
        print_warning "Could not detect Claude Desktop configuration directory"
        echo "Please manually add nano-agent to your Claude Desktop MCP configuration"
    fi
}

setup_api_keys() {
    print_step "Setting up API keys..."
    
    echo
    echo -e "${BOLD}API Key Setup${NC}"
    echo "Nano-agent supports multiple AI providers. You need at least one API key:"
    echo
    echo "1. ${BOLD}OpenAI${NC} (GPT models) - Get key from: https://platform.openai.com/api-keys"
    echo "2. ${BOLD}Anthropic${NC} (Claude models) - Get key from: https://console.anthropic.com/"
    echo "3. ${BOLD}Ollama${NC} (Local models) - Install from: https://ollama.ai"
    echo
    
    # Check for existing API keys
    ENV_FILE="$INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/.env"
    
    if [ -f "$ENV_FILE" ]; then
        echo "Current API key status:"
        
        if grep -q "OPENAI_API_KEY=sk-" "$ENV_FILE" 2>/dev/null; then
            print_success "OpenAI API key is configured"
        else
            echo -e "${YELLOW}  OpenAI API key: Not configured${NC}"
        fi
        
        if grep -q "ANTHROPIC_API_KEY=" "$ENV_FILE" && grep -v "ANTHROPIC_API_KEY=$" "$ENV_FILE" >/dev/null 2>&1; then
            print_success "Anthropic API key is configured"
        else
            echo -e "${YELLOW}  Anthropic API key: Not configured${NC}"
        fi
        
        # Check if Ollama is running
        if command -v ollama >/dev/null 2>&1 && pgrep ollama >/dev/null 2>&1; then
            print_success "Ollama is installed and running"
        else
            echo -e "${YELLOW}  Ollama: Not running or not installed${NC}"
        fi
    fi
    
    echo
    read -p "$(echo -e "${YELLOW}Would you like to configure API keys now? (y/N): ${NC}")" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_api_keys
    else
        echo "You can configure API keys later by editing: $ENV_FILE"
    fi
}

configure_api_keys() {
    ENV_FILE="$INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/.env"
    
    echo
    echo "Enter your API keys (press Enter to skip):"
    echo
    
    # OpenAI API Key
    read -p "OpenAI API Key (sk-...): " OPENAI_KEY
    if [ -n "$OPENAI_KEY" ]; then
        if grep -q "OPENAI_API_KEY=" "$ENV_FILE"; then
            sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$OPENAI_KEY/" "$ENV_FILE"
        else
            echo "OPENAI_API_KEY=$OPENAI_KEY" >> "$ENV_FILE"
        fi
        print_success "OpenAI API key configured"
    fi
    
    # Anthropic API Key
    read -p "Anthropic API Key: " ANTHROPIC_KEY
    if [ -n "$ANTHROPIC_KEY" ]; then
        if grep -q "ANTHROPIC_API_KEY=" "$ENV_FILE"; then
            sed -i.bak "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_KEY/" "$ENV_FILE"
        else
            echo "ANTHROPIC_API_KEY=$ANTHROPIC_KEY" >> "$ENV_FILE"
        fi
        print_success "Anthropic API key configured"
    fi
    
    # Ollama setup
    echo
    read -p "$(echo -e "${YELLOW}Would you like to install Ollama for local models? (y/N): ${NC}")" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_ollama
    fi
}

install_ollama() {
    print_step "Installing Ollama..."
    
    if command -v ollama >/dev/null 2>&1; then
        print_success "Ollama already installed"
    else
        # Install Ollama
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew >/dev/null 2>&1; then
                brew install ollama
            else
                curl -fsSL https://ollama.ai/install.sh | sh
            fi
        else
            # Linux and others
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
        
        if command -v ollama >/dev/null 2>&1; then
            print_success "Ollama installed successfully"
        else
            print_warning "Ollama installation may have failed. Please visit https://ollama.ai for manual installation"
            return
        fi
    fi
    
    # Start Ollama service
    print_step "Starting Ollama service..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - start as background process
        nohup ollama serve >/dev/null 2>&1 &
    else
        # Linux - try to start as service or background process
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start ollama || nohup ollama serve >/dev/null 2>&1 &
        else
            nohup ollama serve >/dev/null 2>&1 &
        fi
    fi
    
    sleep 3  # Wait for service to start
    
    # Download default model
    print_step "Downloading default model (gpt-oss:20b)..."
    echo "This may take several minutes..."
    
    if ollama pull gpt-oss:20b; then
        print_success "Default model downloaded successfully"
    else
        print_warning "Failed to download model. You can do this later with: ollama pull gpt-oss:20b"
    fi
}

test_installation() {
    print_step "Testing installation..."
    
    # Test that nano-agent command is available
    if command -v nano-agent >/dev/null 2>&1; then
        print_success "nano-agent command is available"
    else
        print_warning "nano-agent command not found in PATH"
        echo "You may need to restart your terminal or add $(uv tool dir)/bin to your PATH"
    fi
    
    # Test basic functionality
    echo "Testing basic functionality..."
    
    # Create a simple test
    cd /tmp
    mkdir -p nano-agent-test
    cd nano-agent-test
    
    # Test CLI if available
    if command -v nano-agent >/dev/null 2>&1; then
        echo "Running basic test..."
        if timeout 30 nano-agent --help >/dev/null 2>&1; then
            print_success "nano-agent CLI is working"
        else
            print_warning "nano-agent CLI test timed out or failed"
        fi
    fi
    
    # Cleanup
    cd /tmp
    rm -rf nano-agent-test
}

show_completion_message() {
    clear
    cat << EOF

${BOLD}${GREEN}🎉 Installation Complete!${NC}

${BOLD}Nano Agent MCP Server has been successfully installed!${NC}

${BOLD}📍 Installation Locations:${NC}
• Program files: $INSTALL_DIR/nano-agent
• Configuration: $CONFIG_DIR
• Command: $(command -v nano-agent 2>/dev/null || echo "$(uv tool dir)/bin/nano-agent")

${BOLD}🚀 What's Next:${NC}

${BOLD}1. For Claude Desktop users:${NC}
   • Restart Claude Desktop
   • Look for the 🔌 icon to access nano-agent tools
   • Try: "Use nano-agent to analyze this project"

${BOLD}2. For CLI users:${NC}
   • Run: nano-cli run "your prompt here"
   • Examples:
     nano-cli run "Create a Python hello world script"
     nano-cli run "Analyze the files in this directory" --read-only

${BOLD}3. Configure API Keys (if not done):${NC}
   • Edit: $INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/.env
   • Add your OpenAI, Anthropic, or setup Ollama

${BOLD}📚 Documentation:${NC}
   • Usage Guide: $INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/MCP_USAGE_GUIDE.md
   • Hooks System: $INSTALL_DIR/nano-agent/apps/nano_agent_mcp_server/HOOKS.md
   • README: $INSTALL_DIR/nano-agent/README.md

${BOLD}🆘 Need Help?${NC}
   • Run: nano-agent --help
   • Check: nano-cli run "test connection"
   • Issues: https://github.com/your-org/nano-agent/issues

${GREEN}Happy coding with nano-agent! 🤖✨${NC}

EOF
}

# Main installation flow
main() {
    print_header
    
    echo "This script will install Nano Agent MCP Server for production use."
    echo "It includes Claude Desktop integration and CLI tools."
    echo
    read -p "$(echo -e "${YELLOW}Continue with installation? (y/N): ${NC}")" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    check_requirements
    install_nano_agent
    setup_configuration
    setup_api_keys
    setup_claude_desktop
    test_installation
    show_completion_message
}

# Handle script interruption
trap 'echo -e "\n${RED}Installation interrupted.${NC}"; exit 1' INT TERM

# Run main installation
main "$@"