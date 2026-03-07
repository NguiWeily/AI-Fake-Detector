import os
import sys

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

# Import your custom tools from your tools.py script, or place in this script
from .tools import searxng_search

# Import your specialised agent from your agent's script, or place in this script
from .translator import root_agent as translator

load_dotenv()

try:
   root_agent = Agent(
      name="root_agent",
      model=LiteLlm(
         model=f"openai/{os.getenv('MODEL', 'aisingapore/Llama-SEA-LION-v3-70B-IT')}"
      ),
      description="Agent to answer questions using search and translation tools.",
      instruction="You are a helpful assistant who answers questions in a concise and informative manner. " \
      "You can use tools to assist with searches (`searxng_search`) and translations (`translator`). "\
      "If using `searxng_search`, make sure to provide the links you use at the end of your response, if not already provided",
      tools=[searxng_search, AgentTool(agent=translator)],
   )
except Exception as e:
   print(f"An error occurred while creating the root agent: {e}")
   sys.exit(1)