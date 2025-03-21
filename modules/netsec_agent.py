import asyncio
import json
import os
from autogen_agentchat.teams import BaseGroupChat
from autogen_core import CancellationToken

class Chatbot:
    async def netsec_agent(self, user_input: str) -> str:
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
            print(f"Error in netsec_agent: {str(e)}")

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