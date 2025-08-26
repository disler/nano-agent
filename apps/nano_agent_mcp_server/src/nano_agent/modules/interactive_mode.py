"""
Enhanced Interactive Mode for Nano Agent CLI.

This module provides an interactive shell with autocompletion,
command history, and support for /command syntax.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import sys
import subprocess
import json
from datetime import datetime
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion, PathCompleter, merge_completers
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .command_loader import CommandLoader, parse_command_syntax
from .agent_loader import AgentLoader
from .nano_agent import _execute_nano_agent
from .data_types import PromptNanoAgentRequest, ChatMessage
from .constants import DEFAULT_MODEL, DEFAULT_PROVIDER, AVAILABLE_MODELS

console = Console()


class NanoAgentCompleter(Completer):
    """Custom completer for nano-agent interactive mode."""
    
    def __init__(self):
        """Initialize the completer with commands and models."""
        self.loader = CommandLoader()
        self.commands = []
        self.models = list(AVAILABLE_MODELS.keys())
        # Built-in slash commands (embedded)
        self.embedded_commands = [
            '/help', '/commands', '/clear', '/history', '/exit', '/quit',
            '/model', '/provider', '/verbose'
        ]
        # Legacy non-slash commands (for backward compatibility, but not advertised)
        self.special_commands = [
            'exit', 'quit', 'q'
        ]
        self._refresh_commands()
    
    def _refresh_commands(self):
        """Refresh the list of available commands."""
        try:
            command_objs = self.loader.list_commands()
            self.commands = [f"/{cmd.name}" for cmd in command_objs]
        except Exception:
            self.commands = []
    
    def get_completions(self, document, complete_event):
        """Get completions based on current input."""
        text = document.text_before_cursor
        
        # Refresh commands periodically
        if text.startswith('/'):
            self._refresh_commands()
        
        # Complete /commands (both user commands and embedded commands)
        if text.startswith('/'):
            # Add embedded commands
            for cmd in self.embedded_commands:
                if cmd.startswith(text):
                    # Provide descriptions for embedded commands
                    descriptions = {
                        '/help': 'Show help and usage information',
                        '/commands': 'List all available commands',
                        '/clear': 'Clear the screen',
                        '/history': 'Show command history',
                        '/exit': 'Exit interactive mode',
                        '/quit': 'Exit interactive mode',
                        '/model': 'Change the AI model',
                        '/provider': 'Change the provider',
                        '/verbose': 'Toggle verbose output'
                    }
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=cmd,
                        display_meta=descriptions.get(cmd, "Built-in command")
                    )
            
            # Add user-defined commands
            for cmd in self.commands:
                if cmd.startswith(text):
                    # Get command description for display
                    cmd_name = cmd[1:]  # Remove leading /
                    command_obj = self.loader.load_command(cmd_name)
                    display_meta = command_obj.description if command_obj else ""
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=cmd,
                        display_meta=display_meta[:50] + "..." if len(display_meta) > 50 else display_meta
                    )
        
        # Complete special commands
        elif text and not text.startswith('/'):
            # Check for special command completion (legacy, not advertised)
            for cmd in self.special_commands:
                if cmd.startswith(text.lower()):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display_meta="Exit command"
                    )
            
            # Model completion after "/model" command
            if text.startswith('/model '):
                model_part = text[7:]
                for model in self.models:
                    if model.startswith(model_part):
                        yield Completion(
                            model,
                            start_position=-len(model_part),
                            display_meta="Model name"
                        )
            # Legacy model completion
            elif text.startswith('model '):
                model_part = text[6:]
                for model in self.models:
                    if model.startswith(model_part):
                        yield Completion(
                            model,
                            start_position=-len(model_part),
                            display_meta="Model name"
                        )


class InteractiveSession:
    """Enhanced interactive session for nano-agent."""
    
    def __init__(self, initial_model: str = DEFAULT_MODEL, initial_provider: str = DEFAULT_PROVIDER, 
                 initial_agent: Optional[str] = None):
        """Initialize the interactive session."""
        self.model = initial_model
        self.provider = initial_provider
        self.verbose = False
        self.loader = CommandLoader()
        self.agent_loader = AgentLoader()
        self.completer = NanoAgentCompleter()
        self.history_file = Path.home() / ".nano-cli" / "history.txt"
        self._ensure_history_dir()
        
        # Chat history for maintaining conversation context
        self.chat_history = []  # List of {"role": "user/assistant", "content": str}
        
        # Mark if model/provider were explicitly set via CLI
        if initial_model != DEFAULT_MODEL:
            self._model_override = True
        if initial_provider != DEFAULT_PROVIDER:
            self._provider_override = True
        
        # PS1 configuration (set defaults first)
        self.ps1_format = "{time} {agent}@{model} > "  # Default format
        self.ps1_variables = {
            'name': 'nano-agent',
            'time': lambda: datetime.now().strftime('%H:%M:%S'),
            'agent': lambda: self.agent_loader.current_agent.name if self.agent_loader.current_agent else 'default',
            'model': lambda: self.model,
            'pwd': lambda: os.getcwd().replace(str(Path.home()), '~'),
        }
        
        # Load configuration from file (including default_agent)
        self._load_ps1_config()
        
        # Override with CLI-specified agent if provided
        if initial_agent:
            if self.agent_loader.switch_agent(initial_agent):
                console.print(f"[green]✓ Loaded agent: {initial_agent}[/green]")
            else:
                console.print(f"[yellow]Warning: Agent '{initial_agent}' not found, using default[/yellow]")
        elif self.agent_loader.current_agent:
            # Config file loaded an agent successfully
            console.print(f"[green]✓ Loaded default agent: {self.agent_loader.current_agent.name}[/green]")
        
        # Prompt style
        self.style = Style.from_dict({
            'prompt': '#ansigreen bold',
            'model': '#ansiblue',
            'command': '#ansiyellow',
            'agent': '#ansicyan',
            'time': '#ansigray',
            'path': '#ansimagenta',
        })
    
    def _ensure_history_dir(self):
        """Ensure the history directory exists."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_ps1_config(self):
        """Load configuration from file."""
        config_file = Path.home() / ".nano-cli" / "config.json"
        self.show_welcome = True  # Default to showing welcome
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    # Load PS1 format
                    if 'ps1_format' in config:
                        self.ps1_format = config['ps1_format']
                    
                    # Load default model if not overridden
                    if 'default_model' in config and not hasattr(self, '_model_override'):
                        self.model = config['default_model']
                    
                    # Load default provider if not overridden
                    if 'default_provider' in config and not hasattr(self, '_provider_override'):
                        self.provider = config['default_provider']
                    
                    # Load default agent if not already set
                    if 'default_agent' in config and not self.agent_loader.current_agent:
                        self.agent_loader.switch_agent(config['default_agent'])
                    
                    # Load welcome message preference
                    if 'show_welcome' in config:
                        self.show_welcome = config['show_welcome']
                        
            except Exception as e:
                # Log error but continue with defaults
                import logging
                logging.debug(f"Error loading config: {e}")
    
    def _save_ps1_config(self):
        """Save configuration to file."""
        config_file = Path.home() / ".nano-cli" / "config.json"
        config = {}
        
        # Load existing config if it exists
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
            except Exception:
                pass
        
        # Update all configuration values
        config['ps1_format'] = self.ps1_format
        config['default_model'] = self.model
        config['default_provider'] = self.provider
        config['show_welcome'] = self.show_welcome
        
        # Save current agent as default if one is loaded
        if self.agent_loader.current_agent:
            config['default_agent'] = self.agent_loader.current_agent.name
        
        # Save config
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
    
    def _get_prompt_message(self) -> HTML:
        """Get the formatted prompt message."""
        # Evaluate dynamic variables
        format_dict = {}
        for key, value in self.ps1_variables.items():
            if callable(value):
                format_dict[key] = value()
            else:
                format_dict[key] = value
        
        # Format the prompt string
        try:
            prompt_str = self.ps1_format.format(**format_dict)
        except KeyError as e:
            # Fallback to default if format is invalid
            prompt_str = "{time} {agent}@{model} > ".format(**format_dict)
        
        # Apply styling to known patterns in the prompt
        styled_prompt = prompt_str
        
        # Replace known values with styled versions
        if format_dict.get('time') in styled_prompt:
            styled_prompt = styled_prompt.replace(
                format_dict['time'], 
                f'<time>{format_dict["time"]}</time>'
            )
        
        if format_dict.get('agent') in styled_prompt:
            styled_prompt = styled_prompt.replace(
                format_dict['agent'],
                f'<agent>{format_dict["agent"]}</agent>'
            )
        
        if format_dict.get('model') in styled_prompt:
            styled_prompt = styled_prompt.replace(
                format_dict['model'],
                f'<model>{format_dict["model"]}</model>'
            )
        
        if format_dict.get('pwd') in styled_prompt:
            styled_prompt = styled_prompt.replace(
                format_dict['pwd'],
                f'<path>{format_dict["pwd"]}</path>'
            )
        
        if 'nano-agent' in styled_prompt:
            styled_prompt = styled_prompt.replace(
                'nano-agent',
                '<prompt>nano-agent</prompt>'
            )
        
        # Style command prompt characters (must be done last to avoid breaking XML)
        # Only replace standalone prompt characters at the end
        import re
        # Match prompt characters at the end with optional whitespace
        styled_prompt = re.sub(r'(\s*)([>$#])(\s*)$', r'\1<command>\2</command>\3', styled_prompt)
        
        return HTML(styled_prompt)
    
    def _handle_shell_command(self, command: str) -> bool:
        """
        Execute a shell command and display results.
        
        Returns True if handled, False otherwise.
        """
        if not command.startswith('!'):
            return False
        
        # Extract the shell command (everything after !)
        shell_cmd = command[1:].strip()
        
        if not shell_cmd:
            console.print("[yellow]Usage: !<shell command>[/yellow]")
            console.print("[dim]Example: !ls -la[/dim]")
            return True
        
        # Get user's default shell
        user_shell = os.environ.get('SHELL', '/bin/bash')
        console.print(f"[dim]Executing: {shell_cmd} (using {user_shell})[/dim]")
        
        try:
            # Execute the command using user's default shell
            result = subprocess.run(
                [user_shell, '-c', shell_cmd],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            # Display stdout if present
            if result.stdout:
                console.print(Panel(
                    result.stdout,
                    title="[green]Output[/green]",
                    border_style="green",
                    expand=False
                ))
            
            # Display stderr if present
            if result.stderr:
                console.print(Panel(
                    result.stderr,
                    title="[yellow]Error Output[/yellow]",
                    border_style="yellow",
                    expand=False
                ))
            
            # Display exit code
            if result.returncode == 0:
                console.print(f"[green]✓ Exit code: {result.returncode}[/green]")
            else:
                console.print(f"[red]✗ Exit code: {result.returncode}[/red]")
            
        except subprocess.TimeoutExpired:
            console.print("[red]Command timed out after 30 seconds[/red]")
        except Exception as e:
            console.print(f"[red]Error executing command: {e}[/red]")
        
        return True
    
    def _handle_special_command(self, command: str) -> bool:
        """
        Handle special interactive commands (both slash and non-slash).
        
        Returns True if command was handled, False otherwise.
        """
        # First check for shell commands
        if self._handle_shell_command(command):
            return True
        
        # Check for @agent switching
        if command.startswith('@'):
            agent_name = command[1:].strip()
            if not agent_name:
                # Show current agent
                if self.agent_loader.current_agent:
                    console.print(f"[cyan]Current agent: {self.agent_loader.current_agent.name}[/cyan]")
                else:
                    console.print("[cyan]No agent loaded (using default)[/cyan]")
                self.agent_loader.display_agents_table()
            else:
                # Switch to specified agent
                if self.agent_loader.switch_agent(agent_name):
                    console.print(f"[green]✓ Switched to agent: {agent_name}[/green]")
                    self._save_ps1_config()  # Save the new default agent
                    # Add a system message to chat history to indicate agent switch
                    self.chat_history.append(ChatMessage(
                        role="system",
                        content=f"[Agent switched to: {agent_name}]"
                    ))
                else:
                    console.print(f"[red]Agent '{agent_name}' not found.[/red]")
                    console.print("[dim]Available agents:[/dim]")
                    self.agent_loader.display_agents_table()
            return True
        
        cmd = command.lower().strip()
        
        # Handle both slash and non-slash versions for compatibility
        if cmd in ['exit', 'quit', 'q', '/exit', '/quit']:
            console.print("[dim]Goodbye![/dim]")
            # Return a special value to signal exit
            return 'EXIT'
        
        elif cmd in ['help', '/help']:
            self._show_help()
            return True
        
        elif cmd in ['commands', '/commands']:
            self.loader.display_commands_table()
            return True
        
        elif cmd in ['agents', '/agents']:
            self.agent_loader.display_agents_table()
            return True
        
        elif cmd.startswith('/commands show ') or cmd.startswith('commands show '):
            # Extract the command name to show
            parts = cmd.split()
            if len(parts) >= 3:
                cmd_to_show = parts[2]
                if cmd_to_show.startswith('/'):
                    cmd_to_show = cmd_to_show[1:]  # Remove leading slash
                
                command = self.loader.load_command(cmd_to_show)
                if command:
                    # Read and display the full content of the command file
                    try:
                        content = command.path.read_text()
                        console.print(Panel(
                            content,
                            title=f"📋 Command File: /{command.name}",
                            subtitle=f"[dim]{command.path}[/dim]",
                            border_style="cyan",
                            expand=False
                        ))
                    except Exception as e:
                        console.print(f"[red]Error reading command file: {e}[/red]")
                else:
                    console.print(f"[red]Command '{cmd_to_show}' not found.[/red]")
                    console.print(f"[dim]Type '/commands' to see available commands.[/dim]")
            else:
                console.print("[yellow]Usage: /commands show <command_name>[/yellow]")
                console.print("[dim]Example: /commands show summarize[/dim]")
            return True
        
        elif cmd.startswith('/agents show ') or cmd.startswith('agents show '):
            # Extract the agent name to show
            parts = cmd.split()
            if len(parts) >= 3:
                agent_to_show = parts[2]
                self.agent_loader.show_agent(agent_to_show)
            else:
                console.print("[yellow]Usage: /agents show <agent_name>[/yellow]")
                console.print("[dim]Example: /agents show coder[/dim]")
            return True
        
        elif cmd in ['clear', '/clear']:
            console.clear()
            return True
        
        elif cmd in ['history', '/history']:
            self._show_history()
            return True
        
        elif cmd in ['/reset', '/new']:
            # Clear chat history for a fresh conversation
            self.chat_history = []
            console.print("[green]✓ Chat history cleared. Starting fresh conversation.[/green]")
            return True
        
        elif cmd.startswith('/model ') or cmd.startswith('model '):
            # Support both /model and model for backward compatibility
            if cmd.startswith('/'):
                new_model = cmd[7:].strip()  # /model
            else:
                new_model = cmd[6:].strip()   # model
            
            if new_model in AVAILABLE_MODELS:
                self.model = new_model
                self._save_ps1_config()  # Save the new default
                console.print(f"[green]✓ Model changed to: {self.model}[/green]")
            else:
                console.print(f"[red]Unknown model: {new_model}[/red]")
                console.print(f"[dim]Available models: {', '.join(AVAILABLE_MODELS.keys())}[/dim]")
            return True
        
        elif cmd.startswith('/provider ') or cmd.startswith('provider '):
            # Support both /provider and provider for backward compatibility
            if cmd.startswith('/'):
                new_provider = cmd[10:].strip()  # /provider
            else:
                new_provider = cmd[9:].strip()   # provider
            
            self.provider = new_provider
            self._save_ps1_config()  # Save the new default
            console.print(f"[green]✓ Provider changed to: {self.provider}[/green]")
            return True
        
        elif cmd in ['/verbose on', 'verbose on']:
            self.verbose = True
            console.print("[green]✓ Verbose mode enabled[/green]")
            return True
        
        elif cmd in ['/verbose off', 'verbose off']:
            self.verbose = False
            console.print("[green]✓ Verbose mode disabled[/green]")
            return True
        
        elif cmd in ['/verbose', 'verbose']:
            status = "on" if self.verbose else "off"
            console.print(f"[cyan]Verbose mode is {status}[/cyan]")
            return True
        
        elif cmd.startswith('/welcome'):
            parts = cmd.split()
            if len(parts) > 1:
                setting = parts[1].lower()
                if setting == 'off':
                    self.show_welcome = False
                    self._save_ps1_config()
                    console.print("[green]✓ Welcome message disabled[/green]")
                elif setting == 'on':
                    self.show_welcome = True
                    self._save_ps1_config()
                    console.print("[green]✓ Welcome message enabled[/green]")
                else:
                    console.print("[yellow]Usage: /welcome [on|off][/yellow]")
            else:
                # Show the welcome message
                self._show_welcome_message()
            return True
        
        elif cmd.startswith('/ps1'):
            parts = cmd.split(maxsplit=1)
            if len(parts) == 1:
                # Show current PS1 and help
                console.print(Panel(
                    f"[bold cyan]PS1 Prompt Configuration[/bold cyan]\n\n"
                    f"[yellow]Current format:[/yellow]\n"
                    f"  {self.ps1_format}\n\n"
                    f"[yellow]Available variables:[/yellow]\n"
                    f"  {{name}}   - Application name (nano-agent)\n"
                    f"  {{time}}   - Current time (HH:MM:SS)\n"
                    f"  {{agent}}  - Current agent name\n"
                    f"  {{model}}  - Current model\n"
                    f"  {{pwd}}    - Current working directory\n\n"
                    f"[yellow]Examples:[/yellow]\n"
                    f"  /ps1 {{name}} [{{model}}] >       # Default\n"
                    f"  /ps1 [{{time}}] {{pwd}} $         # Time and path\n"
                    f"  /ps1 {{agent}}@{{model}} >        # Agent and model\n"
                    f"  /ps1 {{pwd}} [{{agent}}:{{model}}] > # Full info\n\n"
                    f"[dim]Changes are saved automatically[/dim]",
                    border_style="cyan",
                    expand=False
                ))
            else:
                # Set new PS1 format
                new_format = parts[1].strip()
                # Validate the format
                try:
                    test_dict = {k: 'test' for k in ['name', 'time', 'agent', 'model', 'pwd']}
                    new_format.format(**test_dict)
                    self.ps1_format = new_format
                    self._save_ps1_config()
                    console.print(f"[green]✓ PS1 format updated: {self.ps1_format}[/green]")
                except KeyError as e:
                    console.print(f"[red]Invalid PS1 format: Unknown variable {e}[/red]")
                    console.print("[dim]Use /ps1 without arguments to see available variables[/dim]")
                except Exception as e:
                    console.print(f"[red]Invalid PS1 format: {e}[/red]")
            return True
        
        return False
    
    def _show_welcome_message(self):
        """Display the welcome message from the data directory."""
        try:
            # Get the path to the welcome.md file
            import importlib.resources as pkg_resources
            
            # Try to read from package data
            try:
                from .. import data
                welcome_content = pkg_resources.read_text(data, 'welcome.md')
            except (ImportError, FileNotFoundError):
                # Fallback to file system path
                welcome_path = Path(__file__).parent.parent / 'data' / 'welcome.md'
                if welcome_path.exists():
                    welcome_content = welcome_path.read_text()
                else:
                    welcome_content = "Welcome to Nano Agent Interactive Mode!\nType /help for available commands."
            
            # Display the welcome message
            console.print(Panel(
                welcome_content,
                title="🚀 Welcome",
                border_style="cyan",
                expand=False
            ))
        except Exception as e:
            # If anything fails, show a simple welcome
            console.print(Panel(
                "[bold cyan]Welcome to Nano Agent Interactive Mode![/bold cyan]\n"
                "Type /help for available commands.",
                border_style="cyan",
                expand=False
            ))
    
    def _show_help(self):
        """Display help information."""
        current_agent = self.agent_loader.current_agent.name if self.agent_loader.current_agent else "default"
        help_panel = Panel(
            "[bold cyan]Nano Agent Interactive Mode Help[/bold cyan]\n\n"
            "[yellow]Command Files:[/yellow]\n"
            "  /summarize      - Generate summaries\n"
            "  /analyze        - Perform detailed analysis\n"
            "  /explain        - Get clear explanations\n"
            "  /refactor       - Suggest code improvements\n"
            "  /test           - Generate test cases\n"
            "  /<custom>       - Your custom commands\n\n"
            "[yellow]Built-in Commands:[/yellow]\n"
            "  /help           - Show this help message\n"
            "  /help <cmd>     - Show help for specific command\n"
            "  /commands       - List all available commands\n"
            "  /commands show <cmd> - Display full command file content\n"
            "  /clear          - Clear the screen\n"
            "  /history        - Show command history\n"
            "  /reset, /new    - Clear chat history (start fresh)\n"
            "  /exit, /quit    - Exit interactive mode\n\n"
            "[yellow]Agent Management:[/yellow]\n"
            "  @<agent>        - Switch to a different agent personality\n"
            "  @               - Show current agent and list available\n"
            "  /agents         - List all available agents\n"
            "  /agents show <name> - Display agent file content\n\n"
            "[yellow]Shell Commands:[/yellow]\n"
            "  !<command>      - Execute shell command (e.g., !ls -la)\n"
            "                    Shows stdout, stderr, and exit code\n\n"
            "[yellow]Settings:[/yellow]\n"
            "  /model <name>   - Change the model (e.g., /model gpt-5)\n"
            "  /provider <name>- Change the provider (e.g., /provider anthropic)\n"
            "  /verbose [on/off] - Toggle verbose output\n"
            "  /ps1 [format]   - Customize prompt (e.g., /ps1 {pwd} [{agent}] >)\n"
            "  /welcome [on/off] - Toggle or show welcome message\n\n"
            "[yellow]Tips:[/yellow]\n"
            "  • Press Tab to autocomplete any /command\n"
            "  • Use ↑/↓ arrows for command history\n"
            "  • Type any text to send directly to the agent\n"
            "  • Commands can take arguments: /summarize <text>\n"
            "  • Shell commands: !pwd, !git status, !echo hello\n"
            "  • Switch agents: @coder, @analyst, @creative\n\n"
            f"[dim]Current: Model={self.model}, Provider={self.provider}, Agent={current_agent}, Verbose={self.verbose}[/dim]",
            border_style="cyan",
            expand=False
        )
        console.print(help_panel)
    
    def _show_history(self):
        """Display command history."""
        if not self.history_file.exists():
            console.print("[yellow]No history yet.[/yellow]")
            return
        
        try:
            with open(self.history_file, 'r') as f:
                lines = f.readlines()
                
            if not lines:
                console.print("[yellow]No history yet.[/yellow]")
                return
            
            # Show last 20 commands
            recent = lines[-20:]
            console.print(Panel(
                "".join(recent),
                title="[cyan]Recent Commands[/cyan]",
                border_style="dim"
            ))
        except Exception as e:
            console.print(f"[red]Error reading history: {e}[/red]")
    
    def _process_prompt(self, user_input: str) -> Optional[str]:
        """
        Process user input and return the final prompt.
        
        Returns None if the command was handled internally.
        Returns 'EXIT' to signal exit.
        """
        # Check for special commands first
        result = self._handle_special_command(user_input)
        if result == 'EXIT':
            return 'EXIT'
        elif result:
            return None
        
        # Special handling for /help <command> to show command details
        if user_input.lower().startswith('/help '):
            cmd_to_help = user_input[6:].strip()
            if cmd_to_help.startswith('/'):
                cmd_to_help = cmd_to_help[1:]  # Remove leading slash if provided
            
            command = self.loader.load_command(cmd_to_help)
            if command:
                console.print(Panel(
                    f"[green]{command.description}[/green]\n\n"
                    f"[yellow]Usage:[/yellow]\n"
                    f"  /{command.name} <arguments>\n\n"
                    f"[yellow]Template:[/yellow]\n"
                    f"{command.prompt_template[:200]}{'...' if len(command.prompt_template) > 200 else ''}",
                    title=f"📋 Help: /{command.name}",
                    border_style="cyan"
                ))
            else:
                console.print(f"[red]Command '{cmd_to_help}' not found.[/red]")
                console.print(f"[dim]Type '/commands' to see available commands.[/dim]")
            return None
        
        # Check for /command syntax
        command_name, arguments = parse_command_syntax(user_input)
        
        if command_name:
            # Check if it's an embedded command that wasn't handled
            if f"/{command_name}" in ['/help', '/commands', '/clear', '/history', '/exit', '/quit']:
                # These should have been handled by _handle_special_command
                # If we're here, handle them explicitly
                return self._handle_special_command(user_input)
            
            # Load and execute user command
            final_prompt = self.loader.execute_command(command_name, arguments)
            
            if final_prompt is None:
                console.print(f"[red]Command '/{command_name}' not found.[/red]")
                console.print(f"[dim]Type '/commands' to see available commands or '/help' for help.[/dim]")
                return None
            
            console.print(f"[dim]Using command: /{command_name}[/dim]")
            return final_prompt
        
        # Regular prompt
        return user_input
    
    def run(self):
        """Run the interactive session."""
        # Show welcome message if enabled
        if self.show_welcome:
            self._show_welcome_message()
        else:
            console.print(Panel(
                "[bold cyan]Nano Agent Interactive Mode[/bold cyan]\n"
                "Type 'help' for commands, 'exit' to quit\n"
                "Tab for autocompletion, ↑/↓ for history",
                expand=False
            ))
        
        # Show current settings
        console.print(f"\n[dim]Model: {self.model}, Provider: {self.provider}[/dim]\n")
        
        # Create history object
        history = FileHistory(str(self.history_file))
        
        while True:
            try:
                # Get user input with autocompletion
                user_input = prompt(
                    self._get_prompt_message(),
                    completer=self.completer,
                    history=history,
                    auto_suggest=AutoSuggestFromHistory(),
                    style=self.style,
                    complete_while_typing=True,
                    enable_history_search=True,
                )
                
                # Skip empty input
                if not user_input.strip():
                    continue
                
                # Process the prompt
                final_prompt = self._process_prompt(user_input)
                
                # Check for exit signal
                if final_prompt == 'EXIT':
                    break
                    
                if final_prompt is None:
                    continue
                
                # Add user message to chat history
                self.chat_history.append(ChatMessage(role="user", content=final_prompt))
                
                # Create request with chat history and agent
                request = PromptNanoAgentRequest(
                    agentic_prompt=final_prompt,
                    model=self.model,
                    provider=self.provider,
                    chat_history=self.chat_history if len(self.chat_history) > 1 else None,
                    agent_name=self.agent_loader.current_agent.name if self.agent_loader.current_agent else None
                )
                
                # Execute agent
                response = _execute_nano_agent(request)
                
                # Display response
                if response.success:
                    # Add assistant response to chat history
                    self.chat_history.append(ChatMessage(role="assistant", content=response.result))
                    
                    console.print(Panel(
                        response.result,
                        title="💬 Agent Response",
                        border_style="cyan",
                        expand=False
                    ))
                    
                    if self.verbose and response.metadata:
                        import json
                        metadata = response.metadata.copy()
                        metadata["execution_time_seconds"] = round(response.execution_time_seconds, 2)
                        
                        console.print(Panel(
                            json.dumps(metadata, indent=2),
                            title="🔍 Metadata",
                            border_style="dim",
                            expand=False
                        ))
                else:
                    console.print(Panel(
                        response.error,
                        title="❌ Error",
                        border_style="red",
                        expand=False
                    ))
                    
                    if self.verbose and response.metadata:
                        import json
                        console.print(Panel(
                            json.dumps(response.metadata, indent=2),
                            title="🔍 Error Details",
                            border_style="dim",
                            expand=False
                        ))
                
            except KeyboardInterrupt:
                console.print("\n[dim]Use 'exit' to quit or Ctrl+C again to force exit.[/dim]")
                continue
            except EOFError:
                # Handle Ctrl+D
                console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {str(e)}")
                if self.verbose:
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")