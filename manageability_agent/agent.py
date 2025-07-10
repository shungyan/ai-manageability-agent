from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

params = StdioServerParameters(
    command='uv',
    args=["--directory", "/home/sysadmin/AI-manageability-/manageability_agent/", "run", "mcp_consumer.py"]
)


root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/llama3.2"),
    name='ai_agent',
    description='A helpful assistant that help to get latest queue count',
    instruction='Get the latest queue count',
    tools=[
        MCPToolset(
        connection_params=params,
    )],
)
