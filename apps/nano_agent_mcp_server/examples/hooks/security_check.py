#!/usr/bin/env python3
"""
Example hook: Security check for file operations

This hook performs security checks on file operations:
- Blocks operations on sensitive files
- Warns about operations in system directories
- Logs security-relevant events
"""

import json
import sys
import os
from pathlib import Path

# Read JSON input from stdin
input_data = json.loads(sys.stdin.read())

# Extract event details
event = input_data.get("event", "")
tool_name = input_data.get("tool_name", "")
tool_args = input_data.get("tool_args", {})
context = input_data.get("context", "")

# Define sensitive paths and patterns
BLOCKED_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    ".ssh/id_rsa",
    ".ssh/id_ed25519",
    ".aws/credentials",
    ".env",
    "secrets.json",
    "credentials.json"
]

WARN_DIRECTORIES = [
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/System",
    "/Windows"
]

def check_path_security(path_str):
    """Check if a path is secure to operate on."""
    if not path_str:
        return True, None
    
    path = Path(path_str).resolve()
    
    # Check for blocked paths
    for blocked in BLOCKED_PATHS:
        if blocked in str(path):
            return False, f"Operation blocked: Access to sensitive file '{blocked}' is not allowed"
    
    # Check for system directories
    for warn_dir in WARN_DIRECTORIES:
        if str(path).startswith(warn_dir):
            print(f"WARNING: Operating in system directory '{warn_dir}'", file=sys.stderr)
    
    return True, None

# Only check pre_tool_use events
if event == "pre_tool_use" and tool_name in ["write_file", "edit_file"]:
    file_path = tool_args.get("file_path", "")
    
    # Security check
    is_secure, message = check_path_security(file_path)
    
    if not is_secure:
        # Block the operation
        print(message, file=sys.stderr)
        sys.exit(1)  # Non-zero exit blocks execution

# Log security-relevant events
if tool_name in ["write_file", "edit_file", "read_file"]:
    log_dir = Path.home() / ".nano-cli" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_dir / "security.log", "a") as f:
        f.write(f"[{input_data.get('timestamp')}] {event}: {tool_name} on {tool_args.get('file_path', 'unknown')}\n")

# Normal exit (don't block)
sys.exit(0)