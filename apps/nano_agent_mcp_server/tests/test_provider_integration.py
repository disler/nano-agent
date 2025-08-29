"""
Integration tests for multi-provider support.

These tests make real API calls to test provider functionality.
Run with: pytest tests/test_provider_integration.py -v -s
"""

import pytest
import os
import asyncio
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nano_agent.modules.nano_agent import prompt_nano_agent


class TestOllamaIntegration:
    """Test Ollama provider with real model."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.path.exists("/usr/local/bin/ollama") and not os.path.exists("/usr/bin/ollama"),
        reason="Ollama not installed"
    )
    async def test_ollama_gpt_oss_20b(self):
        """Test Ollama with gpt-oss:20b model."""
        # Check if Ollama is running
        import requests
        try:
            ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            api_url = ollama_url.rstrip('/').removesuffix('/v1')
            response = requests.get(f"{api_url}/api/tags", timeout=1)
            models = [m["name"] for m in response.json().get("models", [])]
            if "gpt-oss:20b" not in models:
                pytest.skip("Model gpt-oss:20b not pulled. Run: ollama pull gpt-oss:20b")
        except:
            pytest.skip("Ollama not running. Start with: ollama serve")
        
        # Test file creation with Ollama
        test_file = Path("ollama_test.txt")
        try:
            result = await prompt_nano_agent(
                agentic_prompt="Create a file called ollama_test.txt with exactly this content: 'Hello from Ollama GPT-OSS 20B model!'",
                model="gpt-oss:20b",
                provider="ollama"
            )
            
            assert result["success"], f"Failed: {result.get('error', 'Unknown error')}"
            
            # Verify file was created
            assert test_file.exists(), "File was not created"
            
            # Verify content
            content = test_file.read_text()
            assert "Hello from Ollama" in content or "Ollama" in content.upper(), f"Unexpected content: {content}"
            
            print(f"✅ Ollama test successful")
            print(f"   Result: {result.get('result', '')[:200]}")
            print(f"   File content: {content}")
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()


class TestAnthropicIntegration:
    """Test Anthropic provider with real model."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    async def test_anthropic_claude_haiku(self):
        """Test Anthropic with Claude 3 Haiku model."""
        
        # Test file creation with Claude Haiku
        test_file = Path("haiku_test.txt")
        try:
            result = await prompt_nano_agent(
                agentic_prompt="Create a file called haiku_test.txt with exactly this content: 'Hello from Claude 3 Haiku!'",
                model="claude-3-haiku-20240307",
                provider="anthropic"
            )
            
            assert result["success"], f"Failed: {result.get('error', 'Unknown error')}"
            
            # Verify file was created
            assert test_file.exists(), "File was not created"
            
            # Verify content
            content = test_file.read_text()
            assert "Hello from Claude" in content or "Claude" in content or "Haiku" in content, f"Unexpected content: {content}"
            
            print(f"✅ Claude Haiku test successful")
            print(f"   Result: {result.get('result', '')[:200]}")
            print(f"   File content: {content}")
            
            # Check token tracking
            metadata = result.get("metadata", {})
            token_usage = metadata.get("token_usage", {})
            if token_usage:
                print(f"   Tokens used: {token_usage.get('total_tokens', 0)}")
                print(f"   Cost: ${token_usage.get('total_cost', 0):.6f}")
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()


class TestProviderComparison:
    """Compare outputs across providers."""
    
    @pytest.mark.asyncio
    async def test_compare_providers(self):
        """Compare the same task across available providers."""
        prompt = "List all files in the current directory and tell me how many there are"
        results = {}
        
        # Test OpenAI if available
        if os.getenv("OPENAI_API_KEY"):
            try:
                result = await prompt_nano_agent(
                    agentic_prompt=prompt,
                    model="gpt-5-mini",
                    provider="openai"
                )
                if result["success"]:
                    results["openai"] = result["result"][:200]
                    print(f"OpenAI: {results['openai']}")
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        # Test Anthropic if available
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                result = await prompt_nano_agent(
                    agentic_prompt=prompt,
                    model="claude-3-haiku-20240307",
                    provider="anthropic"
                )
                if result["success"]:
                    results["anthropic"] = result["result"][:200]
                    print(f"Anthropic: {results['anthropic']}")
            except Exception as e:
                print(f"Anthropic error: {e}")
        
        # Test Ollama if available
        try:
            import requests
            ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            api_url = ollama_url.rstrip('/').removesuffix('/v1')
            response = requests.get(f"{api_url}/api/tags", timeout=1)
            models = [m["name"] for m in response.json().get("models", [])]
            if "gpt-oss:20b" in models:
                result = await prompt_nano_agent(
                    agentic_prompt=prompt,
                    model="gpt-oss:20b",
                    provider="ollama"
                )
                if result["success"]:
                    results["ollama"] = result["result"][:200]
                    print(f"Ollama: {results['ollama']}")
        except Exception as e:
            print(f"Ollama error: {e}")
        
        # At least one provider should work
        assert len(results) > 0, "No providers available for testing"
        print(f"\n✅ Tested {len(results)} provider(s) successfully")


if __name__ == "__main__":
    # Run specific tests
    import sys
    if len(sys.argv) > 1:
        pytest.main([__file__, "-v", "-s", "-k", sys.argv[1]])
    else:
        pytest.main([__file__, "-v", "-s"])