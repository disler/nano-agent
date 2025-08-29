#!/usr/bin/env python
"""
Nano Agent CLI - Direct command-line interface for testing the nano agent.

This provides a simple command-line interface to test the nano agent functionality
with various commands and interactive modes.
"""

import asyncio
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .modules.nano_agent import prompt_nano_agent, _execute_nano_agent
from .modules.data_types import PromptNanoAgentRequest
from .modules.constants import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ERROR_NO_API_KEY,
    DEMO_PROMPTS
)
from .modules.command_loader import CommandLoader, parse_command_syntax

app = typer.Typer()
console = Console()

def check_api_key():
    """Check if OpenAI API key is set."""
    if not os.getenv("OPENAI_API_KEY"):
        console.print(f"[red]Error: {ERROR_NO_API_KEY}[/red]")
        console.print("Please set it with: export OPENAI_API_KEY=your-api-key")
        sys.exit(1)

@app.command()
def test_tools():
    """Test individual tool functions."""
    # Import the raw tool functions from nano_agent_tools
    from .modules.nano_agent_tools import (
        read_file_raw,
        list_directory_raw,
        write_file_raw,
        get_file_info_raw,
        edit_file_raw
    )
    
    console.print(Panel("[cyan]Testing Nano Agent Tools[/cyan]", expand=False))
    
    # Test list_directory (call the raw function, not the FunctionTool)
    console.print("\n[yellow]1. Testing list_directory:[/yellow]")
    result = list_directory_raw(".")
    console.print(result[:500] + "..." if len(result) > 500 else result)
    
    # Test write_file
    console.print("\n[yellow]2. Testing write_file:[/yellow]")
    test_file = "test_nano_agent.txt"
    result = write_file_raw(test_file, "Hello from Nano Agent CLI!\nThis is line 2\nThis is line 3")
    console.print(result)
    
    # Test read_file
    console.print("\n[yellow]3. Testing read_file:[/yellow]")
    result = read_file_raw(test_file)
    console.print(f"Content: {result}")
    
    # Test edit_file
    console.print("\n[yellow]4. Testing edit_file:[/yellow]")
    result = edit_file_raw(test_file, "This is line 2", "This is the EDITED line 2")
    console.print(f"Edit result: {result}")
    result = read_file_raw(test_file)
    console.print(f"Content after edit: {result}")
    
    # Test get_file_info
    console.print("\n[yellow]5. Testing get_file_info:[/yellow]")
    result = get_file_info_raw(test_file)
    info = json.loads(result)
    console.print(json.dumps(info, indent=2))
    
    # Clean up
    Path(test_file).unlink(missing_ok=True)
    console.print("\n[green]✓ All tool tests completed successfully![/green]")

@app.command()
def run(
    prompt: str,
    model: str = typer.Option(None, help="Model to use"),
    provider: str = typer.Option(None, help="Provider to use"),
    agent: str = typer.Option(None, help="Agent personality to use"),
    api_base: str = typer.Option(None, help="API base URL (overrides environment variables)"),
    api_key: str = typer.Option(None, help="API key (overrides environment variables)"),
    verbose: bool = typer.Option(False, help="Show detailed output")
):
    """Run the nano agent with a prompt. Supports /command syntax for command files."""
    check_api_key()
    
    # Load config defaults if not specified
    config_file = Path.home() / ".nano-cli" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if model is None:
                    model = config.get('default_model', DEFAULT_MODEL)
                if provider is None:
                    provider = config.get('default_provider', DEFAULT_PROVIDER)
                if agent is None:
                    agent = config.get('default_agent')
        except Exception:
            pass
    
    # Final fallbacks
    if model is None:
        model = DEFAULT_MODEL
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    # Check if this is a command syntax
    command_name, arguments = parse_command_syntax(prompt)
    
    if command_name:
        # Load and execute command
        loader = CommandLoader()
        final_prompt = loader.execute_command(command_name, arguments)
        
        if final_prompt is None:
            console.print(f"[red]Command '/{command_name}' not found.[/red]")
            console.print(f"[dim]Available commands can be listed with: nano-cli commands list[/dim]")
            sys.exit(1)
        
        console.print(Panel(
            f"[cyan]Running Command: /{command_name}[/cyan]\n"
            f"Arguments: {arguments if arguments else '(none)'}\n"
            f"Model: {model}\n"
            f"Provider: {provider}", 
            expand=False
        ))
    else:
        final_prompt = prompt
        console.print(Panel(f"[cyan]Running Nano Agent[/cyan]\nModel: {model}\nProvider: {provider}", expand=False))
    
    console.print(f"\n[yellow]Prompt:[/yellow] {final_prompt}\n")
    
    # Create request with the final prompt (either direct or from command)
    request = PromptNanoAgentRequest(
        agentic_prompt=final_prompt,
        model=model,
        provider=provider,
        agent_name=agent,
        api_base=api_base,
        api_key=api_key
    )
    
    # Execute agent without progress spinner (rich logging will show progress)
    response = _execute_nano_agent(request)
    
    # Display results in panels
    if response.success:
        console.print(Panel(
            f"[green]{response.result}[/green]",
            title="📋 Agent Result",
            border_style="green",
            expand=False
        ))
        
        if verbose:
            # Format metadata as a single JSON object
            metadata_display = response.metadata.copy()
            
            # Add execution time to metadata
            metadata_display["execution_time_seconds"] = round(response.execution_time_seconds, 2)
            
            # Format token usage fields if present
            if "token_usage" in metadata_display:
                usage = metadata_display["token_usage"]
                # Flatten key metrics for better display
                metadata_display["token_usage"] = {
                    "total_tokens": f"{usage['total_tokens']:,}",
                    "input_tokens": f"{usage['input_tokens']:,}",
                    "output_tokens": f"{usage['output_tokens']:,}",
                    "cached_tokens": f"{usage['cached_tokens']:,}",
                    "total_cost": f"${usage['total_cost']:.4f}"
                }
            
            # Pretty print the combined metadata
            metadata_json = json.dumps(metadata_display, indent=2)
            
            console.print(Panel(
                Syntax(metadata_json, "json", theme="monokai", line_numbers=False),
                title="🔍 Metadata & Usage",
                border_style="dim",
                expand=False
            ))
    else:
        console.print(Panel(
            f"[red]{response.error}[/red]",
            title="❌ Agent Failed",
            border_style="red",
            expand=False
        ))
        if verbose and response.metadata:
            console.print(Panel(
                json.dumps(response.metadata, indent=2),
                title="🔍 Error Details",
                border_style="dim",
                expand=False
            ))

@app.command()
def demo():
    """Run a demo showing various agent capabilities."""
    check_api_key()
    
    console.print(Panel("[cyan]Nano Agent Demo[/cyan]", expand=False))
    
    for i, (prompt, model) in enumerate(DEMO_PROMPTS, 1):
        console.print(f"\n[yellow]Demo {i}:[/yellow] {prompt}")
        
        request = PromptNanoAgentRequest(
            agentic_prompt=prompt,
            model=model,
            provider=DEFAULT_PROVIDER
        )
        
        # Execute without progress spinner
        response = _execute_nano_agent(request)
        
        if response.success:
            console.print(f"[green]✓[/green] {response.result[:200]}...")
        else:
            console.print(f"[red]✗[/red] {response.error}")
    
    # Clean up
    Path("demo.txt").unlink(missing_ok=True)
    console.print("\n[green]✓ Demo completed![/green]")

@app.command()
def interactive(
    model: str = typer.Option(None, help="Initial model to use"),
    provider: str = typer.Option(None, help="Initial provider to use"),
    agent: str = typer.Option(None, help="Initial agent personality to use"),
    api_base: str = typer.Option(None, help="API base URL (overrides environment variables)"),
    api_key: str = typer.Option(None, help="API key (overrides environment variables)"),
    simple: bool = typer.Option(False, help="Use simple mode without autocompletion")
):
    """Run the agent in enhanced interactive mode with autocompletion."""
    check_api_key()
    
    # Load config defaults if not specified
    config_file = Path.home() / ".nano-cli" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if model is None:
                    model = config.get('default_model', DEFAULT_MODEL)
                if provider is None:
                    provider = config.get('default_provider', DEFAULT_PROVIDER)
                if agent is None:
                    agent = config.get('default_agent')
        except Exception:
            pass
    
    # Final fallbacks
    if model is None:
        model = DEFAULT_MODEL
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    # Use simple mode if requested or if prompt_toolkit is not available
    if simple:
        _run_simple_interactive(model, provider, api_base, api_key)
    else:
        try:
            from .modules.interactive_mode import InteractiveSession
            session = InteractiveSession(initial_model=model, initial_provider=provider, initial_agent=agent, 
                                        api_base=api_base, api_key=api_key)
            session.run()
        except ImportError:
            console.print("[yellow]Enhanced interactive mode not available. Install with: uv sync[/yellow]")
            console.print("[dim]Falling back to simple mode...[/dim]\n")
            _run_simple_interactive(model, provider, api_base, api_key)

def _run_simple_interactive(model: str, provider: str, api_base: str = None, api_key: str = None):
    """Run simple interactive mode without autocompletion."""
    console.print(Panel("[cyan]Nano Agent Interactive Mode (Simple)[/cyan]\nType 'exit' to quit", expand=False))
    
    loader = CommandLoader()
    
    while True:
        try:
            prompt = typer.prompt("\n[yellow]Enter prompt[/yellow]")
            
            if prompt.lower() in ["exit", "quit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break
            
            # Handle special commands (both slash and non-slash)
            if prompt.lower() in ["help", "/help"]:
                console.print("[cyan]Built-in Commands:[/cyan]")
                console.print("  /help           - Show this help")
                console.print("  /commands       - List available command files")
                console.print("  /clear          - Clear the screen")
                console.print("  /<command> args - Run a command file")
                console.print("")
                console.print("[cyan]Shell Commands:[/cyan]")
                console.print("  !<command>      - Execute shell command (e.g., !ls)")
                console.print("")
                console.print("[cyan]Other Commands:[/cyan]")
                console.print("  exit/quit/q     - Exit interactive mode")
                console.print("")
                console.print("[dim]Type any text to send directly to the agent[/dim]")
                continue
            
            if prompt.lower() in ["commands", "/commands"]:
                loader.display_commands_table()
                continue
            
            # Handle /commands show
            if prompt.lower().startswith("/commands show ") or prompt.lower().startswith("commands show "):
                parts = prompt.split()
                if len(parts) >= 3:
                    cmd_to_show = parts[2]
                    if cmd_to_show.startswith('/'):
                        cmd_to_show = cmd_to_show[1:]
                    
                    command = loader.load_command(cmd_to_show)
                    if command:
                        try:
                            content = command.path.read_text()
                            console.print(Panel(
                                content,
                                title=f"📋 Command File: /{command.name}",
                                subtitle=str(command.path),
                                border_style="cyan",
                                expand=False
                            ))
                        except Exception as e:
                            console.print(f"[red]Error reading command file: {e}[/red]")
                    else:
                        console.print(f"[red]Command '{cmd_to_show}' not found.[/red]")
                else:
                    console.print("[yellow]Usage: /commands show <command_name>[/yellow]")
                continue
            
            if prompt.lower() in ["clear", "/clear"]:
                console.clear()
                continue
            
            # Handle shell commands with ! prefix
            if prompt.startswith('!'):
                shell_cmd = prompt[1:].strip()
                if shell_cmd:
                    user_shell = os.environ.get('SHELL', '/bin/bash')
                    console.print(f"[dim]Executing: {shell_cmd} (using {user_shell})[/dim]")
                    try:
                        import subprocess
                        result = subprocess.run(
                            [user_shell, '-c', shell_cmd],
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if result.stdout:
                            console.print("[green]Output:[/green]")
                            console.print(result.stdout)
                        if result.stderr:
                            console.print("[yellow]Error output:[/yellow]")
                            console.print(result.stderr)
                        console.print(f"[dim]Exit code: {result.returncode}[/dim]")
                    except subprocess.TimeoutExpired:
                        console.print("[red]Command timed out after 30 seconds[/red]")
                    except Exception as e:
                        console.print(f"[red]Error: {e}[/red]")
                else:
                    console.print("[yellow]Usage: !<shell command>[/yellow]")
                continue
            
            # Check for /command syntax
            command_name, arguments = parse_command_syntax(prompt)
            
            if command_name:
                final_prompt = loader.execute_command(command_name, arguments)
                if final_prompt is None:
                    console.print(f"[red]Command '/{command_name}' not found.[/red]")
                    continue
                console.print(f"[dim]Using command: /{command_name}[/dim]")
            else:
                final_prompt = prompt
            
            request = PromptNanoAgentRequest(
                agentic_prompt=final_prompt,
                model=model,
                provider=provider,
                api_base=api_base,
                api_key=api_key
            )
            
            # Execute without progress spinner
            response = _execute_nano_agent(request)
            
            if response.success:
                console.print(Panel(
                    response.result,
                    title="💬 Agent Response",
                    border_style="cyan",
                    expand=False
                ))
            else:
                console.print(Panel(
                    response.error,
                    title="❌ Error",
                    border_style="red",
                    expand=False
                ))
                
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {str(e)}")

# Create a sub-app for command management
commands_app = typer.Typer()
app.add_typer(commands_app, name="commands", help="Manage nano-cli command files")

@commands_app.command("list")
def list_commands():
    """List all available command files."""
    loader = CommandLoader()
    loader.display_commands_table()

@commands_app.command("create")
def create_command(
    name: str = typer.Argument(..., help="Name of the command to create"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing command")
):
    """Create a new command template file."""
    loader = CommandLoader()
    success = loader.create_command_template(name, overwrite)
    if not success:
        sys.exit(1)

@commands_app.command("show")
def show_command(
    name: str = typer.Argument(..., help="Name of the command to show")
):
    """Show the content of a command file."""
    loader = CommandLoader()
    command = loader.load_command(name)
    
    if command is None:
        console.print(f"[red]Command '{name}' not found.[/red]")
        sys.exit(1)
    
    console.print(Panel(
        f"[green]{command.description}[/green]",
        title=f"📋 Command: /{command.name}",
        border_style="cyan"
    ))
    
    console.print("\n[yellow]Prompt Template:[/yellow]")
    console.print(Panel(command.prompt_template, border_style="dim"))
    
    if command.metadata:
        console.print("\n[yellow]Metadata:[/yellow]")
        for key, value in command.metadata.items():
            console.print(f"  {key}: {value}")
    
    console.print(f"\n[dim]File: {command.path}[/dim]")
    console.print(f"[dim]Usage: nano-cli /{command.name} \"arguments\"[/dim]")

@commands_app.command("edit")
def edit_command(
    name: str = typer.Argument(..., help="Name of the command to edit")
):
    """Open a command file in the default editor."""
    loader = CommandLoader()
    command = loader.load_command(name)
    
    if command is None:
        console.print(f"[red]Command '{name}' not found.[/red]")
        console.print(f"[dim]Create it with: nano-cli commands create {name}[/dim]")
        sys.exit(1)
    
    # Try to open in default editor
    import subprocess
    import platform
    
    if platform.system() == "Windows":
        os.startfile(command.path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(["open", command.path])
    else:  # Linux and others
        # Try common editors in order of preference
        editors = ["nano", "vim", "vi", "emacs"]
        editor = os.environ.get("EDITOR")
        
        if editor:
            subprocess.call([editor, command.path])
        else:
            for ed in editors:
                if subprocess.call(["which", ed], stdout=subprocess.DEVNULL) == 0:
                    subprocess.call([ed, command.path])
                    break
            else:
                console.print(f"[yellow]No editor found. Please edit manually: {command.path}[/yellow]")

def main():
    """Main entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()