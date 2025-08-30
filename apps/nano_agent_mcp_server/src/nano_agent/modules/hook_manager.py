"""
Hook manager for nano-agent hooks system.

Manages loading, filtering, and executing user-defined hooks.
"""

import os
import json
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from .hook_types import (
    HookEvent,
    HookEventData,
    HookConfig,
    HooksConfiguration,
    HookExecutionResult,
    HookResult
)

logger = logging.getLogger(__name__)


class HookExecutor:
    """Executes individual hook commands."""
    
    async def execute_hook(
        self,
        hook_config: HookConfig,
        event_data: HookEventData
    ) -> HookExecutionResult:
        """Execute a single hook command.
        
        Args:
            hook_config: Hook configuration
            event_data: Event data to pass to hook
            
        Returns:
            HookExecutionResult with execution details
        """
        start_time = time.time()
        
        # Skip if hook is disabled
        if not hook_config.enabled:
            return HookExecutionResult(
                hook_name=hook_config.name,
                success=True,
                exit_code=0,
                stdout="Hook disabled",
                execution_time=0.0
            )
        
        # Prepare JSON input
        input_json = json.dumps(event_data.to_dict(), indent=2)
        
        # Prepare environment variables
        env = os.environ.copy()
        env.update({
            "NANO_CLI_EVENT": event_data.event,
            "NANO_CLI_CONTEXT": event_data.context,
            "NANO_CLI_WORKING_DIR": event_data.working_dir,
            "NANO_CLI_SESSION_ID": event_data.session_id or "",
            "NANO_CLI_MODEL": event_data.model or "",
            "NANO_CLI_PROVIDER": event_data.provider or ""
        })
        
        # Add MCP-specific variables if in MCP context
        if event_data.context == "mcp":
            env["NANO_MCP_CONTEXT"] = "true"
            if event_data.mcp_client:
                env["NANO_MCP_CLIENT"] = event_data.mcp_client
            if event_data.mcp_request_id:
                env["NANO_MCP_REQUEST_ID"] = event_data.mcp_request_id
        
        try:
            # Expand command path if it starts with ~
            command = hook_config.command
            if command.startswith("~"):
                command = os.path.expanduser(command)
            
            logger.debug(f"Executing hook '{hook_config.name}': {command}")
            
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=event_data.working_dir
            )
            
            # Send input and wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_json.encode()),
                    timeout=hook_config.timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                
                return HookExecutionResult(
                    hook_name=hook_config.name,
                    success=False,
                    exit_code=-1,
                    error=f"Hook execution timed out after {hook_config.timeout} seconds",
                    execution_time=time.time() - start_time,
                    blocked=hook_config.blocking
                )
            
            # Decode output
            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()
            
            # Check if hook blocked execution
            blocked = process.returncode != 0 and hook_config.blocking
            
            logger.debug(f"Hook '{hook_config.name}' completed with exit code {process.returncode}")
            if stdout_str:
                logger.debug(f"  stdout: {stdout_str[:200]}")
            if stderr_str:
                logger.debug(f"  stderr: {stderr_str[:200]}")
            
            return HookExecutionResult(
                hook_name=hook_config.name,
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time=time.time() - start_time,
                blocked=blocked
            )
            
        except Exception as e:
            logger.error(f"Error executing hook '{hook_config.name}': {e}")
            return HookExecutionResult(
                hook_name=hook_config.name,
                success=False,
                exit_code=-1,
                error=str(e),
                execution_time=time.time() - start_time,
                blocked=hook_config.blocking
            )


class HookManager:
    """Manages hook registration and execution."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize hook manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_path = config_path
        self.config = self._load_configuration()
        self.executor = HookExecutor()
        
        # Detect execution context
        self.context = self._detect_context()
        
        logger.info(f"HookManager initialized with context: {self.context}")
        if self.config.enabled:
            logger.info(f"Hooks enabled with {len(self.config.hooks)} event types configured")
        else:
            logger.info("Hooks are disabled")
    
    def _detect_context(self) -> str:
        """Detect if running in CLI or MCP context.
        
        Returns:
            "cli" or "mcp"
        """
        # Check various indicators for MCP context
        if any([
            os.getenv("MCP_SERVER_NAME") == "nano-agent",
            os.getenv("CLAUDE_DESKTOP"),
            "nano-agent" in (os.getenv("_", "") or ""),
            # Check if running as MCP server (via FastMCP)
            any("mcp" in str(arg).lower() for arg in os.sys.argv)
        ]):
            return "mcp"
        return "cli"
    
    def _load_configuration(self) -> HooksConfiguration:
        """Load and merge hook configurations.
        
        Returns:
            Merged hooks configuration
        """
        configs = []
        
        # 1. Load global configuration
        global_config_path = Path.home() / ".nano-cli" / "hooks.json"
        if global_config_path.exists():
            try:
                with open(global_config_path, 'r') as f:
                    data = json.load(f)
                configs.append(data)
                logger.debug(f"Loaded global hooks from {global_config_path}")
            except Exception as e:
                logger.error(f"Error loading global hooks: {e}")
        
        # 2. Load project-specific configuration
        project_config_path = Path.cwd() / ".nano-cli" / "hooks.json"
        if project_config_path.exists():
            try:
                with open(project_config_path, 'r') as f:
                    data = json.load(f)
                configs.append(data)
                logger.debug(f"Loaded project hooks from {project_config_path}")
            except Exception as e:
                logger.error(f"Error loading project hooks: {e}")
        
        # 3. Load from specified path if provided
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                configs.append(data)
                logger.debug(f"Loaded hooks from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading hooks from {self.config_path}: {e}")
        
        # Merge configurations (later configs override earlier ones)
        merged = self._merge_configs(configs)
        
        # Convert to HooksConfiguration object
        if merged:
            return HooksConfiguration.from_dict(merged)
        else:
            # Return empty configuration if no configs found
            return HooksConfiguration(enabled=False)
    
    def _merge_configs(self, configs: List[Dict]) -> Dict:
        """Merge multiple configuration dictionaries.
        
        Args:
            configs: List of configuration dictionaries
            
        Returns:
            Merged configuration
        """
        if not configs:
            return {}
        
        # Start with first config
        merged = configs[0].copy()
        
        # Merge subsequent configs
        for config in configs[1:]:
            # Override top-level settings
            for key in ["version", "enabled", "timeout_seconds", "parallel_execution"]:
                if key in config:
                    merged[key] = config[key]
            
            # Merge hooks (project hooks override global)
            if "hooks" in config:
                if "hooks" not in merged:
                    merged["hooks"] = {}
                
                for event_name, hook_list in config["hooks"].items():
                    # Replace entire hook list for this event
                    merged["hooks"][event_name] = hook_list
        
        return merged
    
    async def trigger_hook(
        self,
        event: HookEvent,
        data: HookEventData,
        blocking: bool = False
    ) -> HookResult:
        """Trigger hooks for a specific event.
        
        Args:
            event: Hook event type
            data: Event data to pass to hooks
            blocking: Whether to wait for blocking hooks
            
        Returns:
            HookResult with execution details
        """
        # Skip if hooks are disabled
        if not self.config.enabled:
            return HookResult(
                event=event,
                hooks_executed=0,
                results=[]
            )
        
        # Ensure context is set in data
        data.context = self.context
        data.timestamp = datetime.now().isoformat()
        
        # Get hooks for this event
        event_hooks = self.config.hooks.get(event.value, [])
        
        # Filter hooks based on matcher and condition
        applicable_hooks = [
            hook for hook in event_hooks
            if hook.matches(data)
        ]
        
        if not applicable_hooks:
            return HookResult(
                event=event,
                hooks_executed=0,
                results=[]
            )
        
        logger.debug(f"Triggering {len(applicable_hooks)} hooks for event {event.value}")
        
        # Execute hooks
        results = []
        total_time = 0.0
        blocked = False
        
        if self.config.parallel_execution and not blocking:
            # Execute hooks in parallel (for non-blocking hooks)
            tasks = [
                self.executor.execute_hook(hook, data)
                for hook in applicable_hooks
                if not hook.blocking
            ]
            
            if tasks:
                parallel_results = await asyncio.gather(*tasks)
                results.extend(parallel_results)
                total_time = max(r.execution_time for r in parallel_results)
            
            # Execute blocking hooks sequentially
            for hook in applicable_hooks:
                if hook.blocking:
                    result = await self.executor.execute_hook(hook, data)
                    results.append(result)
                    total_time += result.execution_time
                    
                    if result.blocked:
                        blocked = True
                        break  # Stop on first blocking hook
        else:
            # Execute all hooks sequentially
            for hook in applicable_hooks:
                result = await self.executor.execute_hook(hook, data)
                results.append(result)
                total_time += result.execution_time
                
                if result.blocked:
                    blocked = True
                    break  # Stop on first blocking hook
        
        return HookResult(
            event=event,
            hooks_executed=len(results),
            results=results,
            blocked=blocked,
            total_time=total_time
        )
    
    def reload_configuration(self):
        """Reload hook configuration from files."""
        logger.info("Reloading hook configuration")
        self.config = self._load_configuration()


# Global singleton instance
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get the global hook manager instance.
    
    Returns:
        Global HookManager instance
    """
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager