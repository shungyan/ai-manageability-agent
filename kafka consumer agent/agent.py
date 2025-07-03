# from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from .consumer import consume

ollama_model = LiteLlm(model="ollama_chat/llama3.2")

# root_agent = Agent(
#     name = "OllamaLocalAgent",
#     model = ollama_model,
#     description = "An agent powered by Ollama local model",
#     instruction = "You are a helpful assistant.",
#     tools = []
# )

root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/llama3.2"),
    name='kiosk_management_agent',
    instruction='Run the consume function and return how many people using kiosk and queuing for kiosk',
    tools=[consume],
)
