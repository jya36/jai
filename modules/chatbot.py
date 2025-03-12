import requests
import json
import time
import sys
from typing import List, Dict, Any, Optional, Generator, Union

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", debug: bool = False):
        self.base_url = base_url
        self.generate_endpoint = f"{base_url}/api/generate"
        self.chat_endpoint = f"{base_url}/api/chat"
        self.debug = debug
        
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return True
        except Exception as e:
            if self.debug:
                print(f"Connection test failed: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """List available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return [model["name"] for model in response.json().get("models", [])]
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
        
    def chat(self, messages: List[Dict[str, str]], model: str, options: Optional[Dict[str, Any]] = None) -> Dict:
        """Send a chat message to Ollama."""
        if not self.test_connection():
            return {"error": "Cannot connect to Ollama server. Is it running?"}
            
        payload = {
            "model": model,
            "messages": messages,
            "stream": False  # Explicitly request non-streaming response
        }
        
        if options:
            payload.update(options)
            
        if self.debug:
            print(f"Request to {self.chat_endpoint}:")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
        try:
            response = requests.post(self.chat_endpoint, json=payload)
            
            if self.debug:
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Raw response: {response.text[:200]}...")
                
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError as e:
                if self.debug:
                    print(f"JSON decode error: {e}")
                    
                # Fallback to generate API if chat API fails
                return self.generate_fallback(messages, model, options)
                
        except Exception as e:
            print(f"Error in chat request: {e}")
            return {"error": str(e)}
            
    def generate_fallback(self, messages: List[Dict[str, str]], model: str, options: Optional[Dict[str, Any]] = None) -> Dict:
        """Fallback to generate API if chat API fails."""
        # Convert chat messages to a single prompt
        prompt = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            prompt += f"{role.upper()}: {content}\n"
        
        prompt += "ASSISTANT: "
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        if options:
            # Only copy options that are valid for generate API
            valid_keys = ["temperature", "top_p", "top_k", "num_predict", "seed"]
            filtered_options = {k: v for k, v in options.items() if k in valid_keys}
            payload.update(filtered_options)
            
        try:
            response = requests.post(self.generate_endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Format response to match chat API format
            return {
                "message": {
                    "role": "assistant",
                    "content": result.get("response", "")
                }
            }
        except Exception as e:
            return {"error": f"Fallback generate also failed: {e}"}

    def chat_stream(self, messages: List[Dict[str, str]], model: str, options: Optional[Dict[str, Any]] = None) -> Generator[str, None, Dict]:
        """Send a chat message to Ollama with streaming response."""
        if not self.test_connection():
            yield "Error: Cannot connect to Ollama server. Is it running?"
            return {"error": "Cannot connect to Ollama server. Is it running?"}
            
        payload = {
            "model": model,
            "messages": messages,
            "stream": True  # Enable streaming
        }
        
        if options:
            payload.update(options)
            
        try:
            with requests.post(self.chat_endpoint, json=payload, stream=True) as response:
                response.raise_for_status()
                
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                full_response += content
                                yield content
                        except json.JSONDecodeError:
                            if self.debug:
                                print(f"Failed to parse chunk: {line}")
                
                # Return the complete response object for history
                return {
                    "message": {
                        "role": "assistant",
                        "content": full_response
                    }
                }
        except Exception as e:
            error_msg = f"Error in streaming chat: {e}"
            yield error_msg
            return {"error": error_msg}


class ChatBot:
    """Simple chatbot that interacts with Ollama LLM API."""
    
    def __init__(self, model: str = "phi4:latest", debug: bool = False, 
                 system_prompt: str = None, system_prompt_file: str = 'llm_config.txt'):
        self.client = OllamaClient(debug=debug)
        self.model = model
        self.debug = debug
        self.system_prompt = None
        self.conversation_history = []
        
        # Initialize with system prompt if provided
        if system_prompt_file:
            try:
                with open(system_prompt_file, 'r') as f:
                    self.system_prompt = f.read().strip()
                    if self.debug:
                        print(f"Loaded system prompt from file: {system_prompt_file}")
            except Exception as e:
                print(f"Error reading system prompt file: {e}")
        
        # Override file prompt if direct prompt is provided
        if system_prompt:
            self.system_prompt = system_prompt
            
        # Apply system prompt to conversation history
        if self.system_prompt:
            self.conversation_history.append({
                "role": "system",
                "content": self.system_prompt
            })
            self.client.chat(self.conversation_history, self.model)
            if self.debug:
                print(f"Added system prompt to conversation history")
        
        self._verify_model()
        
    def _verify_model(self):
        """Verify the model exists and suggest alternatives if it doesn't."""
        available_models = self.client.list_models()
        if not available_models:
            print("Warning: Could not connect to Ollama or no models found.")
            return
            
        if self.model not in available_models:
            print(f"Warning: Model '{self.model}' not found in Ollama.")
            print(f"Available models: {', '.join(available_models)}")
            print(f"Using the requested model anyway, but it may fail if not pulled.")
    
    def reset_conversation(self):
        """Clear the conversation history but preserve system prompt."""
        old_history = self.conversation_history
        self.conversation_history = []
        
        # Re-add system message if it was present
        if old_history and old_history[0].get("role") == "system":
            self.conversation_history.append(old_history[0])
            
        return "Conversation history has been reset."
    
    def chat(self, message: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Send a message and get a response."""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        if self.debug:
            print(f"Sending conversation with {len(self.conversation_history)} messages")
            if len(self.conversation_history) > 0 and self.conversation_history[0].get("role") == "system":
                print(f"System prompt is present: {self.conversation_history[0]['content'][:50]}...")
        
        # Send conversation to Ollama
        start_time = time.time()
        response = self.client.chat(self.conversation_history, self.model, options)
        end_time = time.time()
        
        if self.debug:
            print(f"Response time: {end_time - start_time:.2f} seconds")
            
        # Check for errors
        if "error" in response:
            return f"Error: {response['error']}"
            
        # Add assistant response to history
        if "message" in response:
            self.conversation_history.append(response["message"])
            return response["message"]["content"]
        
        return "No response received"
    
    def chat_stream(self, message: str, options: Optional[Dict[str, Any]] = None) -> Generator[str, None, str]:
        """Send a message and stream the response."""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Send conversation to Ollama and stream the response
        full_response = {"message": {"content": ""}}
        
        for content in self.client.chat_stream(self.conversation_history, self.model, options):
            # If a complete response object was returned (end of stream or error)
            if isinstance(content, dict):
                full_response = content
                break
                
            yield content
        
        # Check for errors
        if "error" in full_response:
            yield f"\nError: {full_response['error']}"
        else:
            # Add assistant response to history
            if "message" in full_response:
                self.conversation_history.append(full_response["message"])
                
        return full_response.get("message", {}).get("content", "")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history


# Example usage
if __name__ == "__main__":
    chatbot = ChatBot(model="phi4:latest", debug=False)  # Set debug=True to see detailed logs
    
    print("Chat with Ollama LLM (type 'exit' to quit, 'reset' to clear history)")
    while True:
        user_input = input("\nCommand: ")
        
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "reset":
            result = chatbot.reset_conversation()
            print(f"System: {result}")
            continue
            
        # Print "Bot: " before streaming starts
        print("\nJAI: ", end="", flush=True)
        
        # Stream the response token by token
        for token in chatbot.chat_stream(user_input):
            print(token, end="", flush=True)
        
        # Print a newline at the end

        print()