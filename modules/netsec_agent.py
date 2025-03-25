import asyncio
import json
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core import CancellationToken
import skills.nmap_scan as nmap


class Chatbot:
    def __init__(self):
        model_info = {
            "name": "phi4-mini:3.8b-fp16",
            "context_length": 8192,
            "max_tokens": 4096,
            "temperature": 0.7,
            "function_calling": True,
            "vision": False,
            "json_output": False,
            "family": "ollama",
        }
        self.model_client = OllamaChatCompletionClient(model="phi4-mini:3.8b-fp16",model_info=model_info)

    """async def netsec_agent(self, user_input: str) -> str:
        try:
            wd = os.getcwd() 
            file_path = f"{wd}/skills/netsec_agent.json"
            if not os.path.exists(file_path):
                print(os.path.abspath(file_path))
                return f"Error: Config file not found at {os.path(file_path)}"
                
            with open(file_path) as f:
                config = json.load(f)
            
            team = BaseGroupChat.load_component(config)
            
            print("\nProcessing your request...")
            stream = team.run_stream(task=user_input,cancellation_token=CancellationToken())
            
            async for message in stream:
                if hasattr(message,'stop_reason'):
                    break
                print(f"netsec_agent: {message.content}")
            
            
        except Exception as e:
            print(f"Error in netsec_agent: {str(e)}")"""
    
    def nmap_scan(self, network: str) -> str:
        result = nmap.run_nmap(network)
        return(result)
    
    async def netsec_agent(self,user_input):
        wd = os.getcwd() 
        try:
            with open(f"{wd}/system_messages/nmap_agent") as f:
                system_message = f.read()
                f.close()
        except Exception as e:
            print(f"Error: {e}")
        
        nmap_agent = AssistantAgent(
            name="nmap_scan",
            model_client=self.model_client,
            tools=[self.nmap_scan],
            system_message= system_message,
            reflect_on_tool_use=False,
            model_client_stream=False
        )

        try:
            with open(f"{wd}/system_messages/result_agent") as f:
                system_message = f.read()
                f.close()
        except Exception as e:
            print(f"Error: {e}")

        results_agent = AssistantAgent(
            name="results",
            model_client=self.model_client,
            system_message= system_message,
            reflect_on_tool_use=False,
            model_client_stream=False)

        text_termination = TextMentionTermination("TERMINATE")

        team = RoundRobinGroupChat([nmap_agent, results_agent], termination_condition=text_termination)

        print("\nProcessing your request...")
        stream = team.run_stream(task=user_input,cancellation_token=CancellationToken())
            
        async for message in stream:
            if hasattr(message,'stop_reason'):
                break
            print(f"netsec_agent: {message.content}")
        
        #await team.reset()
        
    async def run(self):
        print("Welcome to the Network Security Assistant! Type 'exit' to quit.")
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break

            try:
                await self.netsec_agent(user_input)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    chatbot = Chatbot()
    asyncio.run(chatbot.run())