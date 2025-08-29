"""
Test native Ollama provider support.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nano_agent.modules.provider_config import ProviderConfig
from nano_agent.modules.constants import AVAILABLE_MODELS, PROVIDER_REQUIREMENTS


class TestOllamaNativeProvider:
    """Test native Ollama provider functionality."""
    
    def test_create_agent_ollama_native(self):
        """Test creating an Ollama-native agent."""
        with patch('nano_agent.modules.ollama_wrapper.AsyncOllamaOpenAIWrapper') as MockWrapper, \
             patch('nano_agent.modules.provider_config.OpenAIChatCompletionsModel') as MockModel, \
             patch('nano_agent.modules.provider_config.Agent') as MockAgent, \
             patch.dict(os.environ, {}, clear=True):
            
            mock_wrapper = Mock()
            MockWrapper.return_value = mock_wrapper
            
            mock_model = Mock()
            MockModel.return_value = mock_model
            
            mock_agent = Mock()
            MockAgent.return_value = mock_agent
            
            agent = ProviderConfig.create_agent(
                name="TestAgent",
                instructions="Test instructions",
                tools=[],
                model="gpt-oss:20b",
                provider="ollama-native",
                model_settings=None
            )
            
            # Should use default values when env vars not set
            MockWrapper.assert_called_once_with(
                host="http://localhost:11434",
                headers=None
            )
            
            MockModel.assert_called_once_with(
                model="gpt-oss:20b",
                openai_client=mock_wrapper
            )
            
            assert agent == mock_agent
    
    def test_create_agent_ollama_native_with_custom_params(self):
        """Test creating an Ollama-native agent with custom parameters."""
        with patch('nano_agent.modules.ollama_wrapper.AsyncOllamaOpenAIWrapper') as MockWrapper, \
             patch('nano_agent.modules.provider_config.OpenAIChatCompletionsModel') as MockModel, \
             patch('nano_agent.modules.provider_config.Agent') as MockAgent:
            
            mock_wrapper = Mock()
            MockWrapper.return_value = mock_wrapper
            
            mock_model = Mock()
            MockModel.return_value = mock_model
            
            mock_agent = Mock()
            MockAgent.return_value = mock_agent
            
            agent = ProviderConfig.create_agent(
                name="TestAgent",
                instructions="Test instructions",
                tools=[],
                model="llama3.2:3b",
                provider="ollama-native",
                model_settings=None,
                api_base="https://custom-ollama.com",
                api_key="custom-auth-token"
            )
            
            # Should use custom values
            MockWrapper.assert_called_once_with(
                host="https://custom-ollama.com",
                headers={'Authorization': 'custom-auth-token'}
            )
            
            assert agent == mock_agent
    
    def test_create_agent_ollama_native_strips_v1_suffix(self):
        """Test that /v1 suffix is stripped from host URL."""
        with patch('nano_agent.modules.ollama_wrapper.AsyncOllamaOpenAIWrapper') as MockWrapper, \
             patch('nano_agent.modules.provider_config.OpenAIChatCompletionsModel'), \
             patch('nano_agent.modules.provider_config.Agent'):
            
            ProviderConfig.create_agent(
                name="TestAgent",
                instructions="Test instructions",
                tools=[],
                model="gpt-oss:20b",
                provider="ollama-native",
                api_base="http://localhost:11434/v1"
            )
            
            # Should strip /v1 from the URL
            MockWrapper.assert_called_once_with(
                host="http://localhost:11434",
                headers=None
            )
    
    def test_validate_provider_setup_ollama_native(self):
        """Test validation of Ollama-native provider setup."""
        with patch('ollama.Client') as MockClient:
            # Mock successful model list - should return ListResponse-like object
            mock_client = Mock()
            mock_models = [Mock(model="gpt-oss:20b"), Mock(model="llama3.2:3b")]
            mock_response = Mock()
            mock_response.models = mock_models
            mock_client.list.return_value = mock_response
            MockClient.return_value = mock_client
            
            is_valid, error = ProviderConfig.validate_provider_setup(
                "ollama-native",
                "gpt-oss:20b", 
                AVAILABLE_MODELS,
                PROVIDER_REQUIREMENTS
            )
            
            assert is_valid is True
            assert error is None
            MockClient.assert_called_once_with(host="http://localhost:11434")
    
    def test_validate_provider_setup_ollama_native_model_not_found(self):
        """Test validation when model is not available in Ollama-native."""
        with patch('ollama.Client') as MockClient:
            # Mock model list without the requested model
            mock_client = Mock()
            mock_models = [Mock(model="llama3.2:3b")]
            mock_response = Mock()
            mock_response.models = mock_models
            mock_client.list.return_value = mock_response
            MockClient.return_value = mock_client
            
            is_valid, error = ProviderConfig.validate_provider_setup(
                "ollama-native",
                "gpt-oss:20b",
                AVAILABLE_MODELS,
                PROVIDER_REQUIREMENTS
            )
            
            assert is_valid is False
            assert "Model gpt-oss:20b not pulled in Ollama" in error
    
    def test_validate_provider_setup_ollama_native_import_error(self):
        """Test validation when Ollama package is not installed."""
        with patch('builtins.__import__', side_effect=ImportError):
            is_valid, error = ProviderConfig.validate_provider_setup(
                "ollama-native",
                "gpt-oss:20b",
                AVAILABLE_MODELS,
                PROVIDER_REQUIREMENTS
            )
            
            assert is_valid is False
            assert "Ollama Python package not installed" in error
    
    def test_setup_provider_ollama_native(self):
        """Test that tracing is disabled for Ollama-native provider."""
        with patch('nano_agent.modules.provider_config.set_tracing_disabled') as mock_disable:
            ProviderConfig.setup_provider("ollama-native")
            mock_disable.assert_called_once_with(True)