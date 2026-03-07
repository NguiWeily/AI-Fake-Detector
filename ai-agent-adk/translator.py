import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

TRANSLATOR_PROMPT = """
You are a translation engine. Your sole purpose is to translate text. You do not have any tools or additional capabilities.

- Translate the input text provided to the target language instructed to you.
- If the target language is not specified or unclear, default to English.

You must only output the translated text. Do not include any additional explanations, notes, formatting, or any other text besides the translated content.
"""

root_agent = LlmAgent(
   name="translator_agent",
   model=LiteLlm(
        model=f"openai/{os.getenv('MODEL', 'aisingapore/Gemma-SEA-LION-v3-9B-IT')}"
    ),
   description="Agent that translates text to a specified language.",
   instruction=TRANSLATOR_PROMPT,
   tools=[]
)