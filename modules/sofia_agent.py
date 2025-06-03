import asyncio
import json
import os
import re
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination,TokenUsageTermination
from autogen_agentchat.teams import BaseGroupChat, RoundRobinGroupChat
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core import CancellationToken
import skills.nmap_scan as nmap
import skills.keyvaultcheck as keyvaultchekc
import banner
from colorama import Fore,Back,Style,init

init(autoreset=True)

osClear = ""
if(os.name == "posix"):
    osClear = "clear"
elif(os.name == "nt"):
    osClear = "cls"  


class Chatbot:
    def __init__(self):
        model_info = {
            "name": "phi4-mini:3.8b-fp16",
            "context_length": 8192,
            "max_tokens": 4096,
            "temperature": 0.3,
            "function_calling": True,
            "vision": False,
            "json_output": False,
            "family": "ollama",
        }
        model_info_reason = {
            "name": "phi4-mini-reasoning:latest",
            "context_length": 8192,
            "max_tokens": 4096,
            "temperature": 0.3,
            "function_calling": False,
            "vision": False,
            "json_output": False,
            "family": "ollama",
        }

        self.model_client = OllamaChatCompletionClient(model="phi4-mini:3.8b-fp16",model_info=model_info)
        self.model_client_reason = OllamaChatCompletionClient(model="phi4-mini-reasoning:latest",model_info=model_info_reason)

    def keyvault_check(self,akvName:str,subscription:str) -> str:
        print(Fore.RED + f"Running keyvault check on {akvName}...")
        result = keyvaultchekc.getConfig(akvName,subscription)
        print(result)
        
    def nmap_scan(self, network: str) -> str:
        print(Fore.RED + f"Running network scan on {network}...")
        result = nmap.run_nmap(network)
        print(Fore.RED + f"Scan complete, sending to results agent...")
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
            model_client=self.model_client_reason,
            system_message= system_message,
            reflect_on_tool_use=False,
            model_client_stream=False)

        text_termination = TextMentionTermination("TERMINATE")
        token_termination = TokenUsageTermination(5000)

        team = RoundRobinGroupChat([nmap_agent, results_agent], termination_condition=text_termination)

        print(Fore.RED + "\nProcessing your request...")
        stream = team.run_stream(task=user_input,cancellation_token=CancellationToken())
            
        async for message in stream:
            if hasattr(message,'stop_reason'):
                break

            content = str(message.content) if message.content is not None else ""
            think_content = None
            actual_response = content

            match = re.search(r"<think>(.*?)</think>", content, re.DOTALL | re.IGNORECASE) 

            if match:
                think_content = match.group(1).strip()
                actual_response = content.replace(match.group(0), "").strip()
        
            if think_content:
                print(Fore.YELLOW + "CoT (from netsec_agent):")
                print(Fore.YELLOW + think_content)
            
            if actual_response: 
                print(f"\nnetsec_agent: {actual_response}")
            elif not think_content and not actual_response: 
                print("netsec_agent: [Empty message received]")
            #print(f"netsec_agent: {message.content}")
        
        #await team.reset()
        
    async def run(self):
        os.system(osClear)
        print(banner.bannerText("SOFIA Local"))
        print(Fore.GREEN + "Welcome to SOFIA Local! Type 'exit' to quit.")
        
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