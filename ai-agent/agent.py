from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

param1 = StdioServerParameters(
    command='uv',
    args=["--directory", "/home/sysadmin/AI-manageability-agent/ai-agent/", "run", "mcp_consumer.py"]
)

param2 = StdioServerParameters(
    command='uv',
    args=["--directory", "/home/sysadmin/AI-manageability-agent/ai-agent/", "run", "app.py"],
    env={"DMT_username":"standalone","DMT_password":"G@ppm0ym"},
    timeout=150,
)



root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/llama3.2"),
    name='ai_agent',
    description='A helpful assistant that help to get latest queue count and discover devices connected',
    instruction='Get the latest queue count, and check the discover all the device connected',
    tools=[
    MCPToolset(
        connection_params=param1,
    ),
    MCPToolset(
        connection_params=param2,
    ),
    ],
)
