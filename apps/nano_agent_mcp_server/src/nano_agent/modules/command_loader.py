"""
Command Loader for Nano Agent CLI.

This module handles loading and managing command files from ~/.nano-cli/commands/
similar to how Claude Code uses .claude/commands/.
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class Command:
    """Represents a loaded command."""
    name: str
    path: Path
    description: str
    prompt_template: str
    metadata: Dict[str, str]


class CommandLoader:
    """Manages loading and executing command files."""
    
    def __init__(self, commands_dir: Optional[Path] = None):
        """
        Initialize the command loader.
        
        Args:
            commands_dir: Optional custom commands directory. 
                         Defaults to ~/.nano-cli/commands/
        """
        if commands_dir is None:
            self.commands_dir = Path.home() / ".nano-cli" / "commands"
        else:
            self.commands_dir = Path(commands_dir)
        
        self._commands_cache: Dict[str, Command] = {}
        self._ensure_commands_dir()
    
    def _ensure_commands_dir(self):
        """Ensure the commands directory exists."""
        self.commands_dir.mkdir(parents=True, exist_ok=True)
    
    def load_command(self, command_name: str) -> Optional[Command]:
        """
        Load a command file by name.
        
        Args:
            command_name: Name of the command (without .md extension)
            
        Returns:
            Command object if found, None otherwise
        """
        # Check cache first
        if command_name in self._commands_cache:
            return self._commands_cache[command_name]
        
        # Look for command file
        command_path = self.commands_dir / f"{command_name}.md"
        if not command_path.exists():
            return None
        
        # Parse command file
        try:
            content = command_path.read_text()
            command = self._parse_command_file(command_name, command_path, content)
            self._commands_cache[command_name] = command
            return command
        except Exception as e:
            console.print(f"[red]Error loading command '{command_name}': {e}[/red]")
            return None
    
    def _parse_command_file(self, name: str, path: Path, content: str) -> Command:
        """
        Parse a command file's content.
        
        Args:
            name: Command name
            path: Path to command file
            content: File content
            
        Returns:
            Parsed Command object
        """
        lines = content.strip().split('\n')
        
        # Extract description from first heading or first paragraph
        description = ""
        prompt_template = ""
        metadata = {}
        
        in_prompt_section = False
        in_metadata_section = False
        
        for line in lines:
            # Skip the main heading
            if line.startswith('# ') and not description:
                # Use heading as description if no description yet
                description = line[2:].strip()
                continue
            
            # Check for section markers
            if line.startswith('## '):
                section = line[3:].strip().lower()
                in_prompt_section = 'prompt' in section or 'template' in section
                in_metadata_section = 'metadata' in section or 'variables' in section
                continue
            
            # Collect prompt template
            if in_prompt_section and line.strip():
                if prompt_template:
                    prompt_template += "\n" + line
                else:
                    prompt_template = line
            
            # Collect metadata
            elif in_metadata_section and ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
            
            # Get description from first non-heading paragraph if not set
            elif not description and line.strip() and not line.startswith('#'):
                description = line.strip()
        
        # If no prompt template found, use entire content as template
        if not prompt_template:
            prompt_template = content
        
        return Command(
            name=name,
            path=path,
            description=description or f"Command: {name}",
            prompt_template=prompt_template,
            metadata=metadata
        )
    
    def list_commands(self) -> List[Command]:
        """
        List all available commands.
        
        Returns:
            List of Command objects
        """
        commands = []
        
        if not self.commands_dir.exists():
            return commands
        
        for file_path in self.commands_dir.glob("*.md"):
            command_name = file_path.stem
            command = self.load_command(command_name)
            if command:
                commands.append(command)
        
        return sorted(commands, key=lambda c: c.name)
    
    def execute_command(self, command_name: str, arguments: str = "") -> Optional[str]:
        """
        Execute a command by substituting arguments.
        
        Args:
            command_name: Name of the command to execute
            arguments: Arguments to substitute for $ARGUMENTS
            
        Returns:
            Final prompt with substitutions, or None if command not found
        """
        command = self.load_command(command_name)
        if not command:
            return None
        
        # Substitute $ARGUMENTS in the prompt template
        prompt = command.prompt_template.replace("$ARGUMENTS", arguments)
        
        # Also handle ${ARGUMENTS} syntax
        prompt = prompt.replace("${ARGUMENTS}", arguments)
        
        # Handle escaped dollar signs
        prompt = prompt.replace("\\$", "$")
        
        return prompt.strip()
    
    def create_command_template(self, command_name: str, overwrite: bool = False) -> bool:
        """
        Create a new command template file.
        
        Args:
            command_name: Name for the new command
            overwrite: Whether to overwrite existing command
            
        Returns:
            True if created successfully, False otherwise
        """
        command_path = self.commands_dir / f"{command_name}.md"
        
        if command_path.exists() and not overwrite:
            console.print(f"[yellow]Command '{command_name}' already exists. Use --overwrite to replace.[/yellow]")
            return False
        
        template = f"""# {command_name.title().replace('_', ' ')}

Brief description of what this command does.

## Prompt Template

Perform the following task: $ARGUMENTS

Please be thorough and provide detailed output.

## Usage

```bash
nano-cli /{command_name} "your arguments here"
```

## Examples

```bash
nano-cli /{command_name} "example input"
```

## Notes

Add any additional context or requirements here.
"""
        
        try:
            command_path.write_text(template)
            console.print(f"[green]✓ Created command template: {command_path}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error creating command template: {e}[/red]")
            return False
    
    def display_commands_table(self):
        """Display available commands in a formatted table."""
        commands = self.list_commands()
        
        if not commands:
            console.print(Panel(
                "[yellow]No commands found.[/yellow]\n\n"
                f"Create your first command with:\n"
                f"  nano-cli commands create <name>\n\n"
                f"Commands directory: {self.commands_dir}",
                title="📋 Nano CLI Commands",
                border_style="yellow"
            ))
            return
        
        table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("File", style="dim")
        
        for cmd in commands:
            # Make path relative to home if possible
            try:
                display_path = cmd.path.relative_to(Path.home())
                display_path = f"~/{display_path}"
            except ValueError:
                display_path = str(cmd.path)
            
            table.add_row(
                f"/{cmd.name}",
                cmd.description[:60] + "..." if len(cmd.description) > 60 else cmd.description,
                display_path
            )
        
        console.print(table)
        console.print(f"\n[dim]Commands directory: {self.commands_dir}[/dim]")
        console.print(f"[dim]Usage: nano-cli /<command> \"arguments\"[/dim]")


def parse_command_syntax(input_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse input to detect command syntax.
    
    Args:
        input_str: Input string to parse
        
    Returns:
        Tuple of (command_name, arguments) if command syntax detected,
        (None, None) otherwise
    """
    # Check for /command syntax
    if input_str.startswith('/'):
        parts = input_str[1:].split(None, 1)
        command_name = parts[0] if parts else ""
        arguments = parts[1] if len(parts) > 1 else ""
        return command_name, arguments
    
    return None, None