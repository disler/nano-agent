"""
Coordinator Agent System for Nano CLI.

The coordinator acts as an intermediary between users and specialized agents,
handling agent selection, command processing, and response routing.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from .agent_loader import AgentLoader, Agent
from .command_loader import CommandLoader
from .nano_agent import _execute_nano_agent
from .data_types import PromptNanoAgentRequest, ChatMessage
from .constants import DEFAULT_MODEL, DEFAULT_PROVIDER

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorRequest:
    """Represents a request processed by the coordinator."""
    original_input: str
    target_agent: Optional[str] = None
    command_name: Optional[str] = None
    command_args: Optional[str] = None
    processed_prompt: Optional[str] = None
    chat_context: Optional[List[ChatMessage]] = None


class CoordinatorAgent:
    """
    Coordinator agent that manages interactions between users and specialized agents.
    
    Flow: User -> Coordinator -> Agent -> Coordinator -> User
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, provider: str = DEFAULT_PROVIDER):
        """Initialize the coordinator agent."""
        self.model = model
        self.provider = provider
        self.agent_loader = AgentLoader()
        self.command_loader = CommandLoader()
        self.current_agent: Optional[Agent] = None
        self.chat_history: List[ChatMessage] = []
        
        # Load all agents metadata for intelligent selection
        self.agents_metadata = self.agent_loader.get_all_agents_metadata()
        
        # Load coordinator agent personality if it exists
        self.coordinator_personality = self._load_coordinator_personality()
    
    def _load_coordinator_personality(self) -> str:
        """Load the coordinator agent's personality from agents directory."""
        coordinator_path = Path.home() / ".nano-cli" / "agents" / "coordinator.md"
        
        if coordinator_path.exists():
            try:
                return coordinator_path.read_text()
            except Exception as e:
                logger.warning(f"Failed to load coordinator personality: {e}")
        
        # Default coordinator personality
        return """# Coordinator Agent

You are a coordinator agent responsible for:
1. Analyzing user requests to determine the best specialized agent
2. Routing requests to the appropriate agent
3. Processing and formatting agent responses for users
4. Managing command templates and argument substitution

## Agent Selection Criteria

- **coder**: Programming tasks, code review, debugging
- **analyst**: Data analysis, research, investigation
- **creative**: Brainstorming, creative writing, ideas
- **h4x0r**: Fun interactions, l33t speak responses
- **default**: General purpose tasks

## Command Processing

When users invoke commands (e.g., /analyze), you:
1. Load the command template
2. Substitute $ARGUMENTS and special tags
3. Pass the processed prompt to the selected agent
4. Format and return the agent's response

## Important Rules

- Always respect explicit agent selection via @agentname
- Choose the most appropriate agent based on task context
- Maintain conversation context across interactions
- Provide clear, well-formatted responses
"""
    
    def parse_user_input(self, user_input: str, chat_history: Optional[List[ChatMessage]] = None) -> CoordinatorRequest:
        """
        Parse user input to extract agent directives and commands.
        
        Args:
            user_input: Raw user input
            chat_history: Optional chat history for context
            
        Returns:
            Parsed coordinator request
        """
        request = CoordinatorRequest(
            original_input=user_input,
            chat_context=chat_history
        )
        
        # Check for explicit agent selection (@agentname)
        agent_match = re.match(r'^@(\w+)\s*(.*)', user_input)
        if agent_match:
            request.target_agent = agent_match.group(1)
            request.processed_prompt = agent_match.group(2).strip()
            return request
        
        # Check for command syntax (/command arguments)
        command_match = re.match(r'^/(\w+)\s*(.*)', user_input)
        if command_match:
            request.command_name = command_match.group(1)
            request.command_args = command_match.group(2).strip()
            return request
        
        # Regular prompt - coordinator will select agent
        request.processed_prompt = user_input
        return request
    
    def select_agent(self, request: CoordinatorRequest) -> str:
        """
        Select the most appropriate agent for the request using metadata.
        
        Args:
            request: Parsed coordinator request
            
        Returns:
            Name of the selected agent
        """
        # If agent explicitly specified, use it
        if request.target_agent:
            # Validate the agent exists
            if request.target_agent in self.agents_metadata:
                return request.target_agent
            else:
                logger.warning(f"Requested agent '{request.target_agent}' not found, using keyword matching")
        
        # Check command-specific agent preferences first
        if request.command_name:
            command = self.command_loader.load_command(request.command_name)
            if command and command.metadata:
                if 'preferred_agent' in command.metadata:
                    preferred = command.metadata['preferred_agent']
                    if preferred in self.agents_metadata:
                        return preferred
        
        # Analyze the request to determine best agent using metadata
        prompt_lower = (request.processed_prompt or request.original_input).lower()
        
        # Score each agent based on keyword matches
        agent_scores = {}
        for agent_name, agent in self.agents_metadata.items():
            if agent_name == 'coordinator':
                continue  # Skip coordinator agent
            
            score = 0
            # Check keywords from agent metadata
            for keyword in agent.keywords:
                if keyword.lower() in prompt_lower:
                    score += 1
            
            if score > 0:
                agent_scores[agent_name] = score
        
        # Select agent with highest score
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"Selected agent '{best_agent}' with score {agent_scores[best_agent]}")
            return best_agent
        
        # Fallback to legacy keyword matching for backward compatibility
        if any(keyword in prompt_lower for keyword in ['code', 'debug', 'function', 'class', 'implement', 'fix']):
            return 'coder'
        elif any(keyword in prompt_lower for keyword in ['analyze', 'data', 'investigate', 'research', 'pattern']):
            return 'analyst'
        elif any(keyword in prompt_lower for keyword in ['creative', 'idea', 'brainstorm', 'story', 'design']):
            return 'creative'
        elif any(keyword in prompt_lower for keyword in ['h4x', 'l33t', '1337', 'hack']):
            return 'h4x0r'
        
        # Default to general agent
        return 'default'
    
    def process_command(self, request: CoordinatorRequest) -> str:
        """
        Process a command by loading template and substituting arguments.
        
        Args:
            request: Coordinator request with command details
            
        Returns:
            Processed prompt with substitutions
        """
        if not request.command_name:
            return request.original_input
        
        # Load command template
        command = self.command_loader.load_command(request.command_name)
        if not command:
            return f"Command '/{request.command_name}' not found. {request.original_input}"
        
        # Start with the template
        processed = command.prompt_template
        
        # Substitute $ARGUMENTS
        if '$ARGUMENTS' in processed:
            processed = processed.replace('$ARGUMENTS', request.command_args or '')
        
        # Process special tags from chat context
        if request.chat_context:
            # Extract relevant context
            context_info = self._extract_context_info(request.chat_context)
            
            # Substitute context tags
            for tag, value in context_info.items():
                processed = processed.replace(f'${{{tag}}}', value)
        
        # Handle file references (@filename)
        processed = self._process_file_references(processed)
        
        return processed
    
    def _extract_context_info(self, chat_history: List[ChatMessage]) -> Dict[str, str]:
        """
        Extract relevant information from chat history for tag substitution.
        
        Args:
            chat_history: List of chat messages
            
        Returns:
            Dictionary of tag replacements
        """
        context = {}
        
        # Extract last mentioned file
        for msg in reversed(chat_history):
            if '@' in msg.content:
                file_match = re.search(r'@([\w./\-]+)', msg.content)
                if file_match:
                    context['LAST_FILE'] = file_match.group(1)
                    break
        
        # Extract last error
        for msg in reversed(chat_history):
            if 'error' in msg.content.lower() or 'exception' in msg.content.lower():
                context['LAST_ERROR'] = msg.content[:200]
                break
        
        # Extract current topic/context
        if chat_history:
            recent_messages = chat_history[-3:]
            context['CONTEXT'] = '\n'.join([f"{msg.role}: {msg.content[:100]}..." 
                                           for msg in recent_messages])
        
        return context
    
    def _process_file_references(self, prompt: str) -> str:
        """
        Process @filename references in the prompt.
        
        Args:
            prompt: Prompt with potential file references
            
        Returns:
            Prompt with file contents substituted
        """
        # Find all @filename references
        file_refs = re.findall(r'@([\w./\-]+)', prompt)
        
        for file_ref in file_refs:
            file_path = Path(file_ref)
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text()
                    # Limit file content to avoid token overflow
                    if len(content) > 1000:
                        content = content[:1000] + "\n... (truncated)"
                    prompt = prompt.replace(f'@{file_ref}', f"\nFile: {file_ref}\n```\n{content}\n```\n")
                except Exception as e:
                    logger.warning(f"Failed to read file {file_ref}: {e}")
                    prompt = prompt.replace(f'@{file_ref}', f"[Error reading {file_ref}]")
        
        return prompt
    
    def coordinate_request(self, user_input: str, 
                          chat_history: Optional[List[ChatMessage]] = None,
                          model: Optional[str] = None,
                          provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Main coordination method - routes request through appropriate agent.
        
        Args:
            user_input: User's input message
            chat_history: Optional conversation history
            model: Optional model override
            provider: Optional provider override
            
        Returns:
            Response dictionary with agent's response
        """
        # Parse the user input
        request = self.parse_user_input(user_input, chat_history)
        
        # Process command if present
        if request.command_name:
            request.processed_prompt = self.process_command(request)
        
        # Select the appropriate agent
        agent_name = self.select_agent(request)
        
        # Build coordinator context message
        coordinator_context = f"""
[Coordinator Routing]
Selected Agent: {agent_name}
Command: {request.command_name or 'direct'}
Original Input: {request.original_input}

Please process this request:
{request.processed_prompt or request.original_input}
"""
        
        # Create the agent request
        agent_request = PromptNanoAgentRequest(
            agentic_prompt=request.processed_prompt or request.original_input,
            model=model or self.model,
            provider=provider or self.provider,
            agent_name=agent_name,
            chat_history=chat_history
        )
        
        # Execute through the selected agent
        response = _execute_nano_agent(agent_request, enable_rich_logging=True)
        
        # Add coordinator metadata to response
        if response.success:
            response.metadata = response.metadata or {}
            response.metadata['coordinator'] = {
                'selected_agent': agent_name,
                'command': request.command_name,
                'original_input': request.original_input
            }
        
        return response.model_dump()
    
    def format_response(self, agent_response: Dict[str, Any]) -> str:
        """
        Format agent response for user presentation.
        
        Args:
            agent_response: Raw agent response
            
        Returns:
            Formatted response string
        """
        if agent_response.get('success'):
            result = agent_response.get('result', '')
            
            # Add agent attribution if available
            metadata = agent_response.get('metadata', {})
            coordinator_info = metadata.get('coordinator', {})
            
            if coordinator_info.get('selected_agent') and coordinator_info['selected_agent'] != 'default':
                attribution = f"\n[via {coordinator_info['selected_agent']} agent]"
                return result + attribution
            
            return result
        else:
            return f"Error: {agent_response.get('error', 'Unknown error')}"