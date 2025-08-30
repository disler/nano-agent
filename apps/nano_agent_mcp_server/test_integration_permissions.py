#!/usr/bin/env python3
"""
Integration test for the permission system with the main MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from nano_agent.modules.nano_agent import prompt_nano_agent


async def test_permissions_integration():
    """Test permission system integration with the main agent function."""
    print("Testing permission system integration with nano_agent...")
    
    # Test 1: Read-only mode
    print("\n1. Testing read-only mode...")
    try:
        result = await prompt_nano_agent(
            agentic_prompt="Try to write a file called test.txt with content 'Hello World'",
            model="gpt-5-mini",
            provider="openai",
            read_only=True
        )
        
        print(f"Read-only test - Success: {result['success']}")
        if not result['success']:
            print(f"Expected failure: {result['error']}")
        elif "Permission denied" in result.get('result', ''):
            print("✓ Read-only mode correctly blocked write operation")
        else:
            print("⚠️ Read-only mode may not have been enforced properly")
            
    except Exception as e:
        print(f"⚠️ Read-only test failed with exception: {e}")
    
    # Test 2: Tool whitelist
    print("\n2. Testing tool whitelist...")
    try:
        result = await prompt_nano_agent(
            agentic_prompt="List the current directory contents",
            model="gpt-5-mini",
            provider="openai",
            allowed_tools=["list_directory"]
        )
        
        print(f"Whitelist test - Success: {result['success']}")
        if result['success']:
            print("✓ Whitelisted tool worked correctly")
        else:
            print(f"⚠️ Whitelisted tool failed: {result['error']}")
            
    except Exception as e:
        print(f"⚠️ Whitelist test failed with exception: {e}")
    
    # Test 3: Path restrictions
    print("\n3. Testing path restrictions...")
    try:
        result = await prompt_nano_agent(
            agentic_prompt="Try to read the file /etc/passwd",
            model="gpt-5-mini", 
            provider="openai",
            blocked_paths=["/etc", "/System"],
            allowed_tools=["read_file"]
        )
        
        print(f"Path restriction test - Success: {result['success']}")
        if not result['success']:
            print(f"Expected failure or permission denial: {result['error']}")
        elif "Permission denied" in result.get('result', ''):
            print("✓ Path restrictions correctly blocked access")
        else:
            print("ℹ️ Path restriction may not have been triggered")
            
    except Exception as e:
        print(f"⚠️ Path restriction test failed with exception: {e}")
    
    # Test 4: Permissions metadata
    print("\n4. Testing permissions metadata in response...")
    try:
        result = await prompt_nano_agent(
            agentic_prompt="Just say hello",
            model="gpt-5-mini",
            provider="openai", 
            read_only=True,
            allowed_tools=["read_file", "list_directory"]
        )
        
        if 'permissions_used' in result and result['permissions_used']:
            permissions = result['permissions_used']
            print(f"✓ Permissions metadata included:")
            print(f"  - Read-only: {permissions.get('read_only')}")
            print(f"  - Allowed tools: {permissions.get('allowed_tools')}")
        else:
            print("⚠️ Permissions metadata not found in response")
            
    except Exception as e:
        print(f"⚠️ Permissions metadata test failed with exception: {e}")
    
    print("\nIntegration tests completed!")


if __name__ == "__main__":
    asyncio.run(test_permissions_integration())