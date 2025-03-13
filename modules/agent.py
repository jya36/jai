from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core import CancellationToken
import asyncio
import requests
# Assuming your Ollama server is running locally on port 11434.

model_info = {
    "name": "phi4-mini:3.8b-fp16",
    "context_length": 8192,
    "max_tokens": 4096,
    "temperature": 0.7,
    "function_calling": True,
    "vision": False,
    "json_output": True,
}
ollama_model_client = OllamaChatCompletionClient(model="phi4-mini:3.8b-fp16",model_info=model_info)

async def get_weather(longitude: str, latitude: str) -> str:
    return requests.get(f"https://api.weather.gov/points/{latitude},{longitude}").json()


agentWeather = AssistantAgent(
    name="JAIAGENT",
    model_client=ollama_model_client,
    tools=[get_weather],
    system_message="You are a helpful assistant who has some tools that can get and summerize the weather for a given location.",
    reflect_on_tool_use=False,
    model_client_stream=False,
)

async def main() -> None:
 await Console(
        agentWeather.on_messages_stream(
            [TextMessage(content="Get the current weather using the get_weather agent for bothell washington using lonitude and latitude, summerize the json results into a sentence", source="user")], CancellationToken()
        )
    )


if __name__ == "__main__":
    asyncio.run(main())