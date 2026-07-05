import abc
import json
import urllib.request
import urllib.error
import os
from typing import Generator, Dict, Any

class BaseLLMAdapter(abc.ABC):
    @abc.abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass
        
    @abc.abstractmethod
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        pass

class OllamaAdapter(BaseLLMAdapter):
    """Local LLM adapter for Ollama"""
    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False
        }
        req = urllib.request.Request(f"{self.base_url}/api/generate", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "")
        except Exception as e:
            return f"Error communicating with local LLM: {str(e)}"
            
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": True
        }
        req = urllib.request.Request(f"{self.base_url}/api/generate", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if "response" in chunk:
                            yield chunk["response"]
        except Exception as e:
            yield f"[LLM Error: {str(e)}]"

class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI API"""
    def __init__(self, model_name: str = "gpt-4o", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return "Error: OPENAI_API_KEY not configured."
            
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Error communicating with OpenAI: {str(e)}"
            
    def generate_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not self.api_key:
            yield "Error: OPENAI_API_KEY not configured."
            return
            
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": True
        }
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}'})
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
        except Exception as e:
            yield f"[LLM Error: {str(e)}]"

def get_llm_adapter() -> BaseLLMAdapter:
    """Factory method to get the configured adapter."""
    # For now, default to Ollama since it doesn't require keys
    # But could be configured via env vars
    provider = os.environ.get("AIEVER_LLM_PROVIDER", "ollama")
    if provider == "openai":
        return OpenAIAdapter()
    return OllamaAdapter()
