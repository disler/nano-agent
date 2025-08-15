#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
import os
from pathlib import Path
from utils.constants import ensure_session_log_dir

def is_dangerous_removal_command(command):
    """
    Comprehensive detection of dangerous removal commands including:
    - rm commands (with or without -rf)
    - mv commands to trash
    - trash commands
    - osascript/AppleScript removal
    - find with -delete
    - rmdir commands
    - rsync with --delete
    """
    # Normalize command by removing extra spaces and converting to lowercase
    normalized = ' '.join(command.lower().split())

    # Pattern 1: Standard rm -rf variations
    rm_patterns = [
        r'\brm\s+.*-[a-z]*r[a-z]*f',  # rm -rf, rm -fr, rm -Rf, etc.
        r'\brm\s+.*-[a-z]*f[a-z]*r',  # rm -fr variations
        r'\brm\s+--recursive\s+--force',  # rm --recursive --force
        r'\brm\s+--force\s+--recursive',  # rm --force --recursive
        r'\brm\s+-r\s+.*-f',  # rm -r ... -f
        r'\brm\s+-f\s+.*-r',  # rm -f ... -r
        r'\brm\s+-[a-z]*r',  # rm -r (recursive without force)
        r'\brm\s+--recursive',  # rm --recursive
        r'\brmdir\s+',  # rmdir command
    ]

    # Pattern 2: Move to trash variations
    trash_patterns = [
        r'\bmv\s+.*\.trash',  # mv to .Trash
        r'\bmv\s+.*trash/',  # mv to trash/
        r'\bmv\s+.*/\.trash',  # mv to /.Trash
        r'\bmv\s+.*~/\.trash',  # mv to ~/.Trash
        r'\btrash\s+',  # trash command
        r'\bgio\s+trash',  # gio trash (Linux)
        r'\bmove-to-trash',  # move-to-trash command
        r'\btrash-put',  # trash-put command
    ]

    # Pattern 3: AppleScript/osascript removal
    applescript_patterns = [
        r'\bosascript.*delete',  # osascript with delete
        r'\bosascript.*trash',  # osascript with trash
        r'\bfinder.*delete',  # Finder delete
        r'\bfinder.*trash',  # Finder trash
    ]

    # Pattern 4: Other dangerous removal patterns
    other_patterns = [
        r'\bfind\s+.*-delete',  # find with -delete
        r'\bfind\s+.*-exec\s+rm',  # find with -exec rm
        r'\brsync\s+.*--delete',  # rsync with --delete
        r'\bshred\s+',  # shred command
        r'\bwipe\s+',  # wipe command
        r'\bsrm\s+',  # secure rm
    ]

    # Check all patterns
    all_patterns = rm_patterns + trash_patterns + applescript_patterns + other_patterns
    for pattern in all_patterns:
        if re.search(pattern, normalized):
            return True

    # Pattern 5: Check for rm with any flag targeting paths
    dangerous_paths = [
        r'/',           # Root directory
        r'/\*',         # Root with wildcard
        r'~',           # Home directory
        r'~/',          # Home directory path
        r'\$HOME',      # Home environment variable
        r'\.\.',        # Parent directory references
        r'\*',          # Wildcards
        r'\.',          # Current directory
        r'\.\s*$',      # Current directory at end of command
    ]

    # Check if any form of rm is used on dangerous paths
    if re.search(r'\brm\s+', normalized):
        for path in dangerous_paths:
            if re.search(path, normalized):
                return True

    return False

def get_protected_paths():
    """
    Get list of protected paths from environment variable or use defaults.
    Users can set CLAUDE_PROTECTED_PATHS env var with colon-separated paths.
    """
    # Default protected paths
    default_protected = [
        "/System",
        "/Library",
        "/Applications",
        "/usr/bin",
        "/usr/sbin",
        "/bin",
        "/sbin",
        "~/.ssh",
        "~/.aws",
        "~/.config",
    ]

    # Get custom protected paths from environment
    custom_paths = os.environ.get('CLAUDE_PROTECTED_PATHS', '').strip()
    if custom_paths:
        custom_list = [p.strip() for p in custom_paths.split(':') if p.strip()]
        default_protected.extend(custom_list)

    # Expand ~ to home directory
    expanded_paths = []
    for path in default_protected:
        if path.startswith('~'):
            expanded_paths.append(os.path.expanduser(path))
        else:
            expanded_paths.append(path)

    return expanded_paths

def is_protected_path_operation(command):
    """
    Check if the command is attempting to operate on protected paths.
    """
    protected_paths = get_protected_paths()
    normalized = command.lower()

    # Extract potential file paths from the command
    # Look for paths after common commands
    path_indicators = [
        r'\brm\s+(?:-[a-z]*\s+)*([^\s]+)',
        r'\bmv\s+([^\s]+)',
        r'\brmdir\s+([^\s]+)',
        r'\btrash\s+([^\s]+)',
        r'\bfind\s+([^\s]+)',
    ]

    for pattern in path_indicators:
        matches = re.findall(pattern, command, re.IGNORECASE)
        for match in matches:
            # Expand the path if it contains ~
            expanded_match = os.path.expanduser(match)
            # Check if any protected path is a prefix of the target
            for protected in protected_paths:
                if expanded_match.startswith(protected) or match.startswith(protected):
                    return True, protected

    return False, None

def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    NOTE: This check has been disabled to allow .env file access.
    """
    # Environment file check disabled - returning False to allow access
    return False

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        # Check for .env file access - DISABLED
        # The check below has been commented out to allow .env file access
        # if is_env_file_access(tool_name, tool_input):
        #     print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
        #     print("Use .env.sample for template files instead", file=sys.stderr)
        #     sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Check for dangerous removal commands
        if tool_name == 'Bash':
            command = tool_input.get('command', '')

            # First check if operating on protected paths
            is_protected, protected_path = is_protected_path_operation(command)
            if is_protected:
                print(f"BLOCKED: Attempt to modify protected path: {protected_path}", file=sys.stderr)
                print("Protected paths cannot be modified. Set CLAUDE_PROTECTED_PATHS env var to customize.", file=sys.stderr)
                sys.exit(2)

            # Block removal commands with comprehensive pattern matching
            if is_dangerous_removal_command(command):
                # Provide specific feedback based on the type of command
                if 'trash' in command.lower() or 'mv' in command.lower():
                    print("BLOCKED: File/folder removal attempt detected. Moving to trash is also prohibited.", file=sys.stderr)
                elif 'osascript' in command.lower() or 'finder' in command.lower():
                    print("BLOCKED: AppleScript removal attempt detected and prevented.", file=sys.stderr)
                elif 'find' in command.lower() and '-delete' in command.lower():
                    print("BLOCKED: Find with -delete detected and prevented.", file=sys.stderr)
                else:
                    print("BLOCKED: Dangerous removal command detected and prevented.", file=sys.stderr)
                print("If you need to remove files, please ask the user for explicit permission.", file=sys.stderr)
                sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        # Extract session_id
        session_id = input_data.get('session_id', 'unknown')

        # Ensure session log directory exists
        log_dir = ensure_session_log_dir(session_id)
        log_path = log_dir / 'pre_tool_use.json'

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        sys.exit(0)

    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()
