from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

ollama = OpenAIChatCompletionClient(
        model="phi4-mini:3.8b-fp16",
        base_url="http://localhost:11434/v1",
        model_info=ModelInfo(vision=False, function_calling=True, json_output=False, family="ollama"),api_key='none'
    )
print(ollama.dump_component().model_dump_json())
