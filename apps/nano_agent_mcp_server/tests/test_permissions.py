#!/usr/bin/env python3
"""
Test the new permission system for the nano agent MCP server.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add the src directory to the path to import nano_agent modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from nano_agent.modules.data_types import ToolPermissions
from nano_agent.modules.nano_agent_tools import get_nano_agent_tools, read_file_raw, write_file_raw


class TestToolPermissions(unittest.TestCase):
    """Test the ToolPermissions class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        self.blocked_file = os.path.join(self.temp_dir, "blocked", "secret.txt")
        
        # Create test files
        with open(self.test_file, "w") as f:
            f.write("Test content")
            
        os.makedirs(os.path.dirname(self.blocked_file), exist_ok=True)
        with open(self.blocked_file, "w") as f:
            f.write("Secret content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_restrictions(self):
        """Test permission system with no restrictions."""
        permissions = ToolPermissions()
        
        # All tools should be allowed
        allowed, reason = permissions.check_tool_permission("read_file")
        self.assertTrue(allowed)
        self.assertEqual(reason, "Allowed")
        
        allowed, reason = permissions.check_tool_permission("write_file")
        self.assertTrue(allowed)
        self.assertEqual(reason, "Allowed")
    
    def test_tool_whitelist(self):
        """Test tool whitelist functionality."""
        permissions = ToolPermissions(allowed_tools=["read_file", "list_directory"])
        
        # Allowed tools should pass
        allowed, reason = permissions.check_tool_permission("read_file")
        self.assertTrue(allowed)
        
        allowed, reason = permissions.check_tool_permission("list_directory")
        self.assertTrue(allowed)
        
        # Non-allowed tools should fail
        allowed, reason = permissions.check_tool_permission("write_file")
        self.assertFalse(allowed)
        self.assertIn("not in allowed list", reason)
    
    def test_tool_blacklist(self):
        """Test tool blacklist functionality."""
        permissions = ToolPermissions(blocked_tools=["write_file", "edit_file"])
        
        # Non-blocked tools should pass
        allowed, reason = permissions.check_tool_permission("read_file")
        self.assertTrue(allowed)
        
        # Blocked tools should fail
        allowed, reason = permissions.check_tool_permission("write_file")
        self.assertFalse(allowed)
        self.assertIn("is blocked", reason)
        
        allowed, reason = permissions.check_tool_permission("edit_file")
        self.assertFalse(allowed)
        self.assertIn("is blocked", reason)
    
    def test_read_only_mode(self):
        """Test read-only mode functionality."""
        permissions = ToolPermissions(read_only=True)
        
        # Read operations should be allowed
        allowed, reason = permissions.check_tool_permission("read_file")
        self.assertTrue(allowed)
        
        allowed, reason = permissions.check_tool_permission("list_directory")
        self.assertTrue(allowed)
        
        allowed, reason = permissions.check_tool_permission("get_file_info")
        self.assertTrue(allowed)
        
        # Write operations should be blocked
        allowed, reason = permissions.check_tool_permission("write_file")
        self.assertFalse(allowed)
        self.assertIn("read-only mode", reason)
        
        allowed, reason = permissions.check_tool_permission("edit_file")
        self.assertFalse(allowed)
        self.assertIn("read-only mode", reason)
    
    def test_path_restrictions_allowed(self):
        """Test path whitelist functionality."""
        permissions = ToolPermissions(allowed_paths=[self.temp_dir])
        
        # Files within allowed path should pass
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": self.test_file})
        self.assertTrue(allowed)
        
        # Files outside allowed path should fail
        outside_file = "/etc/passwd"
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": outside_file})
        self.assertFalse(allowed)
        self.assertIn("not in allowed paths", reason)
    
    def test_path_restrictions_blocked(self):
        """Test path blacklist functionality."""
        blocked_dir = os.path.join(self.temp_dir, "blocked")
        permissions = ToolPermissions(blocked_paths=[blocked_dir])
        
        # Files outside blocked path should pass
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": self.test_file})
        self.assertTrue(allowed)
        
        # Files within blocked path should fail
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": self.blocked_file})
        self.assertFalse(allowed)
        self.assertIn("is blocked by pattern", reason)
    
    def test_combined_restrictions(self):
        """Test combination of multiple restrictions."""
        permissions = ToolPermissions(
            allowed_tools=["read_file", "write_file"],
            blocked_paths=[os.path.join(self.temp_dir, "blocked")],
            read_only=False
        )
        
        # Allowed tool on allowed path should pass
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": self.test_file})
        self.assertTrue(allowed)
        
        # Blocked tool should fail
        allowed, reason = permissions.check_tool_permission("edit_file")
        self.assertFalse(allowed)
        self.assertIn("not in allowed list", reason)
        
        # Allowed tool on blocked path should fail
        allowed, reason = permissions.check_tool_permission("read_file", {"file_path": self.blocked_file})
        self.assertFalse(allowed)
        self.assertIn("is blocked by pattern", reason)


class TestPermissionAwareTools(unittest.TestCase):
    """Test the permission-aware tool system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        # Create test file
        with open(self.test_file, "w") as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_unrestricted_tools(self):
        """Test tools with no restrictions."""
        tools = get_nano_agent_tools(permissions=None)
        
        # Should get all 5 tools
        self.assertEqual(len(tools), 5)
        # Test by checking if we can call a basic function
        # (we can't easily inspect function names with OpenAI Agent SDK)
    
    def test_tool_filtering(self):
        """Test that restricted tools are filtered out."""
        permissions = ToolPermissions(allowed_tools=["read_file", "list_directory"])
        tools = get_nano_agent_tools(permissions=permissions)
        
        # Should only get allowed tools
        self.assertEqual(len(tools), 2)
    
    def test_read_only_filtering(self):
        """Test that read-only mode filters out write tools."""
        permissions = ToolPermissions(read_only=True)
        tools = get_nano_agent_tools(permissions=permissions)
        
        # Should get read-only tools (read_file, list_directory, get_file_info)
        self.assertEqual(len(tools), 3)


def test_basic_functionality():
    """Simple functional test of the permission system."""
    print("Testing ToolPermissions functionality...")
    
    # Test 1: No restrictions
    permissions = ToolPermissions()
    allowed, reason = permissions.check_tool_permission("read_file")
    assert allowed, f"Expected allowed but got: {reason}"
    print("✓ No restrictions test passed")
    
    # Test 2: Read-only mode
    permissions = ToolPermissions(read_only=True)
    allowed, reason = permissions.check_tool_permission("write_file")
    assert not allowed, "Expected write_file to be blocked in read-only mode"
    print("✓ Read-only mode test passed")
    
    # Test 3: Tool whitelist
    permissions = ToolPermissions(allowed_tools=["read_file"])
    allowed, reason = permissions.check_tool_permission("write_file")
    assert not allowed, "Expected write_file to be blocked when not in whitelist"
    print("✓ Tool whitelist test passed")
    
    # Test 4: Tool filtering
    permissions = ToolPermissions(read_only=True)
    tools = get_nano_agent_tools(permissions=permissions)
    assert len(tools) == 3, f"Expected 3 read-only tools, got {len(tools)}"
    print("✓ Tool filtering test passed")
    
    print("All basic tests passed! 🎉")


if __name__ == "__main__":
    # Run basic functionality test first
    test_basic_functionality()
    print()
    
    # Run unit tests
    unittest.main()