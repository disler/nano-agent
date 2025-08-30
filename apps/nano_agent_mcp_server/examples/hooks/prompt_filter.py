#!/usr/bin/env python3
"""
Example hook: Prompt filtering and validation

This hook validates and filters prompts before execution:
- Blocks prompts with forbidden content
- Validates prompt length
- Adds context or templates
- Logs prompt patterns
"""

import json
import sys
import re
from pathlib import Path

# Read JSON input from stdin
input_data = json.loads(sys.stdin.read())

# Extract event details
event = input_data.get("event", "")
prompt = input_data.get("prompt", "")
context = input_data.get("context", "")

# Configuration
MAX_PROMPT_LENGTH = 10000
MIN_PROMPT_LENGTH = 3

# Forbidden patterns (customize based on your needs)
FORBIDDEN_PATTERNS = [
    r"rm\s+-rf\s+/",  # Dangerous rm commands
    r":(){ :|:& };:",  # Fork bomb
    r"dd\s+if=/dev/zero",  # Disk wipe commands
]

# Context-specific templates
TEMPLATES = {
    "test": "Write comprehensive unit tests with edge cases for: ",
    "doc": "Create detailed documentation with examples for: ",
    "review": "Perform a thorough code review focusing on quality and security for: ",
}

def validate_prompt(prompt_text):
    """Validate the prompt for safety and requirements."""
    # Check length
    if len(prompt_text) < MIN_PROMPT_LENGTH:
        return False, f"Prompt too short (minimum {MIN_PROMPT_LENGTH} characters)"
    
    if len(prompt_text) > MAX_PROMPT_LENGTH:
        return False, f"Prompt too long (maximum {MAX_PROMPT_LENGTH} characters)"
    
    # Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, prompt_text, re.IGNORECASE):
            return False, f"Prompt contains forbidden pattern"
    
    return True, None

def enhance_prompt(prompt_text):
    """Enhance prompt with templates or context."""
    # Check if prompt starts with a template keyword
    for keyword, template in TEMPLATES.items():
        if prompt_text.lower().startswith(f"/{keyword} "):
            # Apply template
            enhanced = template + prompt_text[len(keyword)+2:]
            return enhanced
    
    return prompt_text

def log_prompt_stats():
    """Log prompt statistics for analysis."""
    stats_dir = Path.home() / ".nano-cli" / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "timestamp": input_data.get("timestamp"),
        "prompt_length": len(prompt),
        "model": input_data.get("model"),
        "provider": input_data.get("provider"),
        "context": context,
        "first_50_chars": prompt[:50] if prompt else ""
    }
    
    with open(stats_dir / "prompts.jsonl", "a") as f:
        f.write(json.dumps(stats) + "\n")

# Only process pre-agent start events
if event in ["pre_agent_start", "user_prompt_submit"]:
    if prompt:
        # Validate prompt
        is_valid, message = validate_prompt(prompt)
        
        if not is_valid:
            print(f"Prompt validation failed: {message}", file=sys.stderr)
            sys.exit(1)  # Block execution
        
        # Log statistics
        log_prompt_stats()
        
        # Optionally enhance prompt (would need mechanism to pass back)
        # For now, just log the enhancement suggestion
        enhanced = enhance_prompt(prompt)
        if enhanced != prompt:
            print(f"Suggestion: Consider using enhanced prompt", file=sys.stderr)

# MCP-specific filtering
if event == "mcp_request_received" and context == "mcp":
    # Add any MCP-specific validation here
    mcp_client = input_data.get("mcp_client", "")
    
    # Example: Rate limiting per client
    rate_limit_dir = Path.home() / ".nano-cli" / "rate_limits"
    rate_limit_dir.mkdir(parents=True, exist_ok=True)
    
    client_file = rate_limit_dir / f"{mcp_client}.json"
    
    # Simple rate limiting (customize as needed)
    import time
    current_time = time.time()
    
    if client_file.exists():
        with open(client_file, "r") as f:
            last_request = json.load(f).get("last_request", 0)
        
        if current_time - last_request < 1.0:  # 1 second minimum between requests
            print("Rate limit exceeded", file=sys.stderr)
            sys.exit(1)
    
    # Update last request time
    with open(client_file, "w") as f:
        json.dump({"last_request": current_time}, f)

# Normal exit
sys.exit(0)