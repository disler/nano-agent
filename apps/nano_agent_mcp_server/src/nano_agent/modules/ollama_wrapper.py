"""
Ollama native client wrapper for OpenAI Agent SDK compatibility.

This wrapper adapts the native Ollama Python client to work with OpenAI Agent SDK
by implementing the required OpenAI-compatible interface.
"""

from typing import Any, Dict, List, Optional, Union, Iterator, AsyncIterator
import asyncio
import logging
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.chat.chat_completion import Choice
from openai.types import CompletionUsage
import ollama

logger = logging.getLogger(__name__)


class OllamaOpenAIWrapper:
    """
    Wrapper that makes native Ollama client compatible with OpenAI Agent SDK.
    
    This class implements the OpenAI client interface expected by the Agent SDK
    while using the native Ollama Python client under the hood.
    """
    
    def __init__(self, host: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        """Initialize the Ollama wrapper.
        
        Args:
            host: Ollama server host (default: http://localhost:11434)
            headers: Optional headers for authentication
        """
        # Initialize native Ollama client
        if host:
            self.client = ollama.Client(host=host, headers=headers or {})
        else:
            self.client = ollama.Client()
        
        self.host = host or "http://localhost:11434"
        self.headers = headers or {}
        
        # Add attributes expected by OpenAI Agent SDK
        self.base_url = self.host
        self.api_key = headers.get('Authorization') if headers else None
    
    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Convert OpenAI format messages to Ollama format."""
        ollama_messages = []
        for msg in messages:
            # Ollama expects role and content
            if isinstance(msg, dict):
                ollama_messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })
        return ollama_messages
    
    def _create_chat_completion_response(
        self, 
        response: Dict[str, Any], 
        model: str, 
        messages: List[Dict[str, Any]]
    ) -> ChatCompletion:
        """Convert Ollama response to OpenAI ChatCompletion format."""
        
        # Extract content from Ollama response
        content = response.get('message', {}).get('content', '')
        
        # Create OpenAI-compatible response
        completion = ChatCompletion(
            id=f"chatcmpl-{hash(content) % 10**10}",
            object="chat.completion",
            created=int(asyncio.get_event_loop().time()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=content
                    ),
                    finish_reason="stop"
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=response.get('prompt_eval_count', 0),
                completion_tokens=response.get('eval_count', 0),
                total_tokens=response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
            )
        )
        
        return completion
    
    def _create_chat_completion_chunk(
        self, 
        chunk: Dict[str, Any], 
        model: str, 
        index: int = 0
    ) -> ChatCompletionChunk:
        """Convert Ollama streaming chunk to OpenAI ChatCompletionChunk format."""
        
        content = chunk.get('message', {}).get('content', '')
        is_done = chunk.get('done', False)
        
        return ChatCompletionChunk(
            id=f"chatcmpl-{hash(str(chunk)) % 10**10}",
            object="chat.completion.chunk",
            created=int(asyncio.get_event_loop().time()),
            model=model,
            choices=[
                {
                    "index": index,
                    "delta": ChoiceDelta(
                        role="assistant" if index == 0 else None,
                        content=content if not is_done else None
                    ),
                    "finish_reason": "stop" if is_done else None
                }
            ]
        )

    class Chat:
        """Chat completions interface compatible with OpenAI."""
        
        def __init__(self, wrapper: 'OllamaOpenAIWrapper'):
            self.wrapper = wrapper
        
        class Completions:
            """Completions interface."""
            
            def __init__(self, wrapper: 'OllamaOpenAIWrapper'):
                self.wrapper = wrapper
            
            def create(
                self,
                model: str,
                messages: List[Dict[str, Any]],
                stream: bool = False,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                **kwargs
            ) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]:
                """Create chat completion (sync)."""
                try:
                    ollama_messages = self.wrapper._convert_messages(messages)
                    
                    # Prepare options
                    options = {}
                    if temperature is not None:
                        options['temperature'] = temperature
                    if max_tokens is not None:
                        options['num_predict'] = max_tokens
                    
                    if stream:
                        # Streaming response
                        def stream_generator():
                            for chunk in self.wrapper.client.chat(
                                model=model,
                                messages=ollama_messages,
                                stream=True,
                                options=options
                            ):
                                yield self.wrapper._create_chat_completion_chunk(chunk, model)
                        return stream_generator()
                    else:
                        # Non-streaming response
                        response = self.wrapper.client.chat(
                            model=model,
                            messages=ollama_messages,
                            stream=False,
                            options=options
                        )
                        return self.wrapper._create_chat_completion_response(response, model, messages)
                
                except Exception as e:
                    logger.error(f"Ollama chat completion error: {e}")
                    raise
        
        def __init__(self, wrapper: 'OllamaOpenAIWrapper'):
            self.completions = self.Completions(wrapper)
    
    @property
    def chat(self) -> Chat:
        """Get chat interface."""
        return self.Chat(self)


class AsyncOllamaOpenAIWrapper(OllamaOpenAIWrapper):
    """Async version of the Ollama OpenAI wrapper."""
    
    def __init__(self, host: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        super().__init__(host, headers)
        # For async, we'll use asyncio to wrap the sync calls
        
        # Ensure base_url and api_key are available for Agent SDK
        self.base_url = self.host
        self.api_key = headers.get('Authorization') if headers else None
        
    class Chat:
        """Async chat completions interface."""
        
        def __init__(self, wrapper: 'AsyncOllamaOpenAIWrapper'):
            self.wrapper = wrapper
        
        class Completions:
            """Async completions interface."""
            
            def __init__(self, wrapper: 'AsyncOllamaOpenAIWrapper'):
                self.wrapper = wrapper
            
            async def create(
                self,
                model: str,
                messages: List[Dict[str, Any]],
                stream: bool = False,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                **kwargs
            ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
                """Create chat completion (async)."""
                try:
                    ollama_messages = self.wrapper._convert_messages(messages)
                    
                    # Prepare options
                    options = {}
                    if temperature is not None:
                        options['temperature'] = temperature
                    if max_tokens is not None:
                        options['num_predict'] = max_tokens
                    
                    if stream:
                        # Async streaming response
                        async def async_stream_generator():
                            # Run the sync streaming in a thread pool
                            def sync_stream():
                                for chunk in self.wrapper.client.chat(
                                    model=model,
                                    messages=ollama_messages,
                                    stream=True,
                                    options=options
                                ):
                                    return chunk
                            
                            # Since Ollama client doesn't have async streaming yet,
                            # we'll collect all chunks and yield them
                            loop = asyncio.get_event_loop()
                            chunks = await loop.run_in_executor(
                                None,
                                lambda: list(self.wrapper.client.chat(
                                    model=model,
                                    messages=ollama_messages,
                                    stream=True,
                                    options=options
                                ))
                            )
                            
                            for chunk in chunks:
                                yield self.wrapper._create_chat_completion_chunk(chunk, model)
                        
                        return async_stream_generator()
                    else:
                        # Non-streaming response
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            lambda: self.wrapper.client.chat(
                                model=model,
                                messages=ollama_messages,
                                stream=False,
                                options=options
                            )
                        )
                        return self.wrapper._create_chat_completion_response(response, model, messages)
                
                except Exception as e:
                    logger.error(f"Async Ollama chat completion error: {e}")
                    raise
        
        def __init__(self, wrapper: 'AsyncOllamaOpenAIWrapper'):
            self.completions = self.Completions(wrapper)
    
    @property
    def chat(self) -> Chat:
        """Get async chat interface."""
        return self.Chat(self)