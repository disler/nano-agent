"""
Agent Loader Module for Nano Agent CLI.

This module manages loading and switching between different agent personalities
from markdown files in ~/.nano-cli/agents/ directory.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging
import yaml
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class Agent:
    """Represents an agent personality."""
    name: str
    path: Path
    content: str
    description: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def system_prompt_extension(self) -> str:
        """Get the content to append to the base system prompt."""
        return self.content


class AgentLoader:
    """Manages loading and switching agent personalities."""
    
    def __init__(self):
        """Initialize the agent loader."""
        self.agents_dir = Path.home() / ".nano-cli" / "agents"
        self._ensure_agents_dir()
        self.current_agent: Optional[Agent] = None
        self._agents_cache: Dict[str, Agent] = {}
    
    def _ensure_agents_dir(self):
        """Ensure the agents directory exists."""
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a default agent if none exists
        default_agent_path = self.agents_dir / "default.md"
        if not default_agent_path.exists():
            self._create_default_agent(default_agent_path)
    
    def _create_default_agent(self, path: Path):
        """Create the default agent file."""
        default_content = """# Default Agent

This is the default nano-agent with no special modifications.
The base system prompt is used as-is.

## Behavior
- Standard nano-agent behavior
- No additional specialization
- General-purpose assistant
"""
        path.write_text(default_content)
        logger.info(f"Created default agent at {path}")
    
    def _parse_agent_file(self, path: Path) -> Agent:
        """Parse an agent markdown file with optional YAML frontmatter."""
        content = path.read_text()
        
        # Check for YAML frontmatter
        metadata = {}
        prompt_content = content
        
        # Pattern to detect YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if frontmatter_match:
            # Parse YAML frontmatter
            yaml_content = frontmatter_match.group(1)
            prompt_content = frontmatter_match.group(2)
            
            try:
                metadata = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Error parsing YAML frontmatter in {path}: {e}")
                metadata = {}
        
        # Extract values from metadata or use defaults
        name = metadata.get('name', path.stem)
        description = metadata.get('description', None)
        keywords = metadata.get('keywords', '')
        tools = metadata.get('tools', '')
        
        # Convert keywords and tools to lists
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        elif not isinstance(keywords, list):
            keywords = []
            
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(',') if t.strip()]
        elif not isinstance(tools, list):
            tools = []
        
        # If no description in metadata, try to extract from content
        if not description:
            lines = prompt_content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    description = line.strip()
                    break
        
        # Clean up the prompt content (remove leading title if present)
        lines = prompt_content.split('\n')
        if lines and lines[0].startswith('# '):
            # Skip the title line for the system prompt extension
            prompt_lines = lines[1:]
            prompt_content = '\n'.join(prompt_lines).strip()
        else:
            prompt_content = prompt_content.strip()
        
        return Agent(
            name=name,
            path=path,
            content=prompt_content,
            description=description,
            keywords=keywords,
            tools=tools,
            metadata=metadata
        )
    
    def load_agent(self, agent_name: str) -> Optional[Agent]:
        """
        Load an agent by name.
        
        Args:
            agent_name: Name of the agent (without .md extension)
            
        Returns:
            Agent object if found, None otherwise
        """
        # Check cache first
        if agent_name in self._agents_cache:
            return self._agents_cache[agent_name]
        
        # Try to load from file
        agent_path = self.agents_dir / f"{agent_name}.md"
        
        if not agent_path.exists():
            logger.warning(f"Agent '{agent_name}' not found at {agent_path}")
            return None
        
        try:
            agent = self._parse_agent_file(agent_path)
            self._agents_cache[agent_name] = agent
            logger.info(f"Loaded agent '{agent_name}' from {agent_path}")
            return agent
        except Exception as e:
            logger.error(f"Error loading agent '{agent_name}': {e}")
            return None
    
    def switch_agent(self, agent_name: str) -> bool:
        """
        Switch to a different agent.
        
        Args:
            agent_name: Name of the agent to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        agent = self.load_agent(agent_name)
        if agent:
            self.current_agent = agent
            logger.info(f"Switched to agent '{agent_name}'")
            return True
        return False
    
    def list_agents(self) -> List[Agent]:
        """
        List all available agents.
        
        Returns:
            List of Agent objects
        """
        agents = []
        
        for agent_file in self.agents_dir.glob("*.md"):
            try:
                agent = self._parse_agent_file(agent_file)
                agents.append(agent)
                self._agents_cache[agent.name] = agent
            except Exception as e:
                logger.error(f"Error parsing agent file {agent_file}: {e}")
        
        return sorted(agents, key=lambda a: a.name)
    
    def display_agents_table(self):
        """Display a formatted table of available agents."""
        agents = self.list_agents()
        
        if not agents:
            console.print("[yellow]No agents found.[/yellow]")
            console.print(f"[dim]Create agent files in {self.agents_dir}[/dim]")
            return
        
        table = Table(title="📤 Available Agents", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green", width=20)
        table.add_column("Description", style="white", width=60)
        table.add_column("Status", style="yellow", width=10)
        
        for agent in agents:
            status = "✓ Active" if self.current_agent and self.current_agent.name == agent.name else ""
            description = agent.description or "[dim]No description[/dim]"
            if len(description) > 57:
                description = description[:57] + "..."
            table.add_row(
                agent.name,
                description,
                status
            )
        
        console.print(table)
        if self.current_agent:
            console.print(f"\n[cyan]Current agent: {self.current_agent.name}[/cyan]")
    
    def create_agent_template(self, agent_name: str, overwrite: bool = False) -> bool:
        """
        Create a new agent template file.
        
        Args:
            agent_name: Name for the new agent
            overwrite: Whether to overwrite if file exists
            
        Returns:
            True if created successfully, False otherwise
        """
        agent_path = self.agents_dir / f"{agent_name}.md"
        
        if agent_path.exists() and not overwrite:
            console.print(f"[red]Agent '{agent_name}' already exists.[/red]")
            console.print("[dim]Use --overwrite to replace it.[/dim]")
            return False
        
        template = f"""# {agent_name.replace('_', ' ').title()} Agent

Specialized agent for [describe purpose].

## Personality
[Describe the agent's personality, tone, and communication style]

## Expertise
[List the agent's areas of expertise and specialization]

## Behavioral Guidelines
- [Guideline 1]
- [Guideline 2]
- [Guideline 3]

## Response Style
[Describe how the agent should format and structure responses]

## Examples
[Provide examples of typical interactions or responses]

## Notes
[Any additional context or requirements for this agent]
"""
        
        try:
            agent_path.write_text(template)
            console.print(f"[green]✓ Created agent template: {agent_path}[/green]")
            console.print(f"[dim]Edit the file to customize the agent's behavior.[/dim]")
            return True
        except Exception as e:
            console.print(f"[red]Error creating agent template: {e}[/red]")
            return False
    
    def get_extended_system_prompt(self, base_prompt: str) -> str:
        """
        Get the extended system prompt with agent personality.
        
        Args:
            base_prompt: The base system prompt
            
        Returns:
            Extended prompt with agent personality appended
        """
        if not self.current_agent or self.current_agent.name == "default":
            return base_prompt
        
        # Append agent personality to base prompt
        extended_prompt = f"{base_prompt}\n\n# Agent Personality Extension\n\n{self.current_agent.system_prompt_extension}"
        return extended_prompt
    
    def show_agent(self, agent_name: str):
        """Display the content of an agent file."""
        agent = self.load_agent(agent_name)
        if agent:
            console.print(Panel(
                agent.content,
                title=f"🤖 Agent: {agent.name}",
                subtitle=f"[dim]{agent.path}[/dim]",
                border_style="cyan",
                expand=False
            ))
        else:
            console.print(f"[red]Agent '{agent_name}' not found.[/red]")
            self.display_agents_table()
    
    def get_all_agents_metadata(self) -> Dict[str, Agent]:
        """
        Get metadata for all available agents.
        
        Returns:
            Dictionary mapping agent names to Agent objects with metadata
        """
        agents_dict = {}
        
        for agent_file in self.agents_dir.glob("*.md"):
            try:
                agent = self._parse_agent_file(agent_file)
                agents_dict[agent.name] = agent
                self._agents_cache[agent.name] = agent
            except Exception as e:
                logger.error(f"Error parsing agent file {agent_file}: {e}")
        
        return agents_dict