#!/bin/bash
# Example hook: Log tool usage to a file
#
# This hook logs all tool executions with timestamps and arguments
# Used for auditing and debugging tool usage

# Read JSON input from stdin
INPUT=$(cat)

# Extract relevant fields using jq (if available) or basic text processing
EVENT=$(echo "$INPUT" | grep -o '"event":"[^"]*"' | cut -d'"' -f4)
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
TIMESTAMP=$(echo "$INPUT" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)

# Create logs directory if it doesn't exist
LOG_DIR="$HOME/.nano-cli/logs"
mkdir -p "$LOG_DIR"

# Log to file
LOG_FILE="$LOG_DIR/tool_usage.log"

if [ "$EVENT" = "pre_tool_use" ]; then
    echo "[$TIMESTAMP] TOOL_START: $TOOL_NAME" >> "$LOG_FILE"
    # Log full input for debugging
    echo "$INPUT" >> "$LOG_DIR/tool_usage_debug.log"
elif [ "$EVENT" = "post_tool_use" ]; then
    echo "[$TIMESTAMP] TOOL_COMPLETE: $TOOL_NAME" >> "$LOG_FILE"
elif [ "$EVENT" = "tool_error" ]; then
    echo "[$TIMESTAMP] TOOL_ERROR: $TOOL_NAME" >> "$LOG_FILE"
fi

# Always exit 0 to not block execution
exit 0