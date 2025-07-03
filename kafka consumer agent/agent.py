from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from .consumer import consume
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

ollama_model = LiteLlm(model="ollama_chat/llama3.2")

root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/llama3.2"),
    name='kiosk_management_agent',
    instruction='Run the consume function and return how many people using kiosk and queuing for kiosk',
    tools=[consume],
)

# params = StdioServerParameters(
#     command='uv',
#     args=["--directory", "/home/sysadmin/AI-manageability-/kafka consumer agent/", "run", "kafka_consumer.py"]
# )


# root_agent = LlmAgent(
#     model=LiteLlm(model="ollama_chat/llama3.2"),
#     name='kafka_agent',
#     description='A helpful assistant that help to consume kafka messages',
#     instruction='Consume kafka message and determine how many people queuing and using',
#     tools=[
#         MCPToolset(
#         connection_params=params,
#     )],
# )
