import requests
import json

def get_current_weather(location,format=json):
    return f"Today is sunny in {location} {format}"

url = "http://localhost:11434/api/chat"

payload = {
        "model": "phi4-mini:3.8b-fp16",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant with some tools."
            },
            {
                "role": "user",
                "content": "What is the weather today in Paris?"
            }
        ],
        "stream": False,
        "options": {
            "max_new_tokens": 1024,
            "return_full_text": False,
            "temperature": 0.00001,
            "top_p": 1.0,
            "do_sample": False
        },
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The location to get the weather for, e.g. San Francisco, CA"
                            },
                            "format": {
                                "type": "string",
                                "description": "The format to return the weather in, e.g. celsius or fahrenheit",
                                "enum": ["celsius", "fahrenheit"]
                            }
                        },
                        "required": ["location", "format"]
                    }
                }
            }
        ]
    }

response = requests.post(url, json=payload)
response.raise_for_status()  # Raise an exception for bad status codes
        
# Parse and print the response
result = response.json()
print("Response:")
print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Print just the assistant's message
if "message" in result:
    print("\nAssistant's message:")
    print(result["message"]["tool_calls"])