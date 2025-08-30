#!/bin/bash

# Setup script for nano-cli hooks
# This script installs example hooks to ~/.nano-cli/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$HOME/.nano-cli/hooks"
CONFIG_FILE="$HOME/.nano-cli/hooks.json"

echo "Setting up nano-cli hooks..."

# Create hooks directory
mkdir -p "$HOOKS_DIR"
echo "✓ Created hooks directory: $HOOKS_DIR"

# Copy hook scripts
echo "Installing hook scripts..."
for script in hooks/*.{sh,py}; do
    if [ -f "$script" ]; then
        filename=$(basename "$script")
        cp "$script" "$HOOKS_DIR/$filename"
        chmod +x "$HOOKS_DIR/$filename"
        echo "  ✓ Installed: $filename"
    fi
done

# Install or update hooks configuration
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "⚠️  Hooks configuration already exists at: $CONFIG_FILE"
    echo "   To use the example configuration, either:"
    echo "   1. Back up your existing config and replace it"
    echo "   2. Merge the example hooks into your existing config"
    echo ""
    echo "Example configuration is available at: $SCRIPT_DIR/hooks.json"
else
    cp "$SCRIPT_DIR/hooks.json" "$CONFIG_FILE"
    echo "✓ Installed hooks configuration: $CONFIG_FILE"
fi

# Create required directories
mkdir -p "$HOME/.nano-cli/logs"
mkdir -p "$HOME/.nano-cli/metrics"
mkdir -p "$HOME/.nano-cli/stats"
mkdir -p "$HOME/.nano-cli/rate_limits"
echo "✓ Created required directories"

echo ""
echo "✅ Hooks setup complete!"
echo ""
echo "The following hooks are now available:"
echo "  • prompt_filter.py   - Validates and filters prompts"
echo "  • security_check.py  - Blocks operations on sensitive files"
echo "  • performance_monitor.py - Tracks execution performance"
echo "  • log_tool_usage.sh  - Logs all tool executions"
echo ""
echo "To customize hooks:"
echo "  1. Edit hooks configuration: $CONFIG_FILE"
echo "  2. Modify hook scripts in: $HOOKS_DIR"
echo "  3. Enable/disable specific hooks in the configuration"
echo ""
echo "To test hooks:"
echo "  nano-cli run 'Create a test file'"
echo "  tail -f ~/.nano-cli/logs/*.log"
echo ""