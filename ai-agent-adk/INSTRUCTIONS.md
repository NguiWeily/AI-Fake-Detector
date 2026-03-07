# instructions.md — Context Engineering Guide
## Multimodal AI-Generated Content Detection Agent

---

## 1. Project Overview

This project is a **multimodal agentic AI system** that detects AI-generated content across text, image, audio, and video. It serves users across Singapore's multilingual landscape (English, Mandarin, Malay, Tamil, Singlish) via a Telegram Bot frontend and a Google ADK multi-agent backend.

### Core Objectives

| Objective | Description |
|---|---|
| **Clarify content** | Explain what the submitted content is and what was detected |
| **Explain why** | Surface reasoning behind detection verdicts, not just scores |
| **Surface useful context** | Provide background, sources, and related information |
| **Work across Singapore's languages** | Support EN, ZH, MS, TA, and Singlish inputs/outputs |
| **Reduce harm without over-censoring** | Flag harmful AI-generated content while preserving legitimate use |

---

## 2. Tech Stack

| Service | Role | Notes |
|---|---|---|
| **Google ADK** | Multi-agent orchestration framework | Manages agent routing, tool-calling, session state |
| **SEA-LION GUARD** | AI-content detection | HuggingFace Inference API — binary/score detection |
| **SEA-LION v4** | Insights & explanation | HuggingFace Inference API — multilingual reasoning |
| **Telegram Bot API** | Frontend — multimodal input | Accepts text, image, audio, video |
| **ClickHouse** | Real-time analytics & logging | Stores detection events, model outputs, user sessions |
| **MCP Subagents** | Web crawling & summarisation | Uses `.md` context files for grounded responses |

---

## 3. Project Structure

```
parent_folder/
└── adk_agent/
    ├── __init__.py       # Exposes root_agent for ADK
    ├── agent.py          # Root orchestrator agent
    ├── tools.py          # Custom tools (SEA-LION API, ClickHouse, Telegram handlers)
    ├── translator.py     # Subagent: multilingual translation (SEA-LION v4 small model)
    ├── chat-cli.py       # CLI runner for local testing
    └── .env              # API keys and environment config
```

---

## 4. Environment Setup

Create a `.env` file in `adk_agent/`:

```env
# SEA-LION API (via OpenAI-compatible LiteLLM)
OPENAI_API_KEY=your-sea-lion-api-key-here
OPENAI_API_BASE=https://api.sea-lion.ai/v1

# Primary model for orchestration and reasoning
MODEL=aisingapore/Llama-SEA-LION-v3-70B-IT

# SEA-LION GUARD model for AI-content detection
GUARD_MODEL=aisingapore/SEA-LION-GUARD

# Google ADK — disable Vertex AI if using SEA-LION API directly
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here

# ClickHouse
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DB=agent_logs

# MCP / Web Search
SEARXNG_URL=https://your-searxng-instance-url-here
```

---

## 5. Agent Architecture

### Agent Pipeline

```
[Telegram User Input]
   │
   ├── text / image / audio / video
   │
   ▼
[Root Orchestrator Agent]  ←─── agent.py
   │                              (SEA-LION 70B-IT via LiteLLM)
   │
   ├──► [GUARD Detection Tool]    ←── tools.py
   │       SEA-LION GUARD API
   │       Returns: {is_ai_generated, confidence, label}
   │
   ├──► [Insights Tool]           ←── tools.py
   │       SEA-LION v4 API
   │       Returns: explanation, reasoning, context
   │
   ├──► [Translator Subagent]     ←── translator.py
   │       SEA-LION Gemma 9B-IT
   │       Handles: EN, ZH, MS, TA, Singlish
   │
   ├──► [MCP Web Crawl Subagent]  ←── MCP tool / .md context files
   │       SearXNG search + summarisation
   │       Returns: grounded context, source links
   │
   └──► [ClickHouse Logger]       ←── tools.py
           Logs: input, verdict, model output, timestamp
```

---

## 6. Core Agent Files

### `agent.py` — Root Orchestrator

```python
import os
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from .tools import run_guard_detection, run_insights, log_to_clickhouse, searxng_search
from .translator import root_agent as translator

load_dotenv()

SYSTEM_INSTRUCTION = """
You are a multimodal AI-generated content detection assistant designed for users in Singapore.

Your responsibilities:
1. Receive user-submitted content (text, image, audio, video description).
2. Use `run_guard_detection` to check if content is AI-generated.
3. Use `run_insights` to generate a clear, human-readable explanation of the verdict.
4. Use `searxng_search` to surface relevant context or background if needed.
5. Use `translator` to handle or respond in the user's language (EN, ZH, MS, TA, Singlish).
6. Log all results using `log_to_clickhouse`.

Tone and behaviour:
- Be factual, neutral, and non-alarmist.
- Always explain WHY content may be AI-generated, not just the verdict.
- Never over-censor. If confidence is low, say so clearly.
- Respond in the same language the user used.
- Provide source links when using web search results.
"""

try:
    root_agent = Agent(
        name="content_detection_agent",
        model=LiteLlm(
            model=f"openai/{os.getenv('MODEL', 'aisingapore/Llama-SEA-LION-v3-70B-IT')}"
        ),
        description="Multimodal AI-generated content detection agent for Singapore users.",
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            run_guard_detection,
            run_insights,
            searxng_search,
            log_to_clickhouse,
            AgentTool(agent=translator),
        ],
    )
except Exception as e:
    print(f"Failed to initialise root agent: {e}")
    sys.exit(1)
```

---

### `tools.py` — Custom Tools

```python
import os
import requests
from typing import Dict, Any, Optional
from clickhouse_driver import Client
from dotenv import load_dotenv

load_dotenv()

# ── SEA-LION GUARD Detection ──────────────────────────────────────────────────

def run_guard_detection(content: str, content_type: str = "text") -> Dict[str, Any]:
    """
    Run SEA-LION GUARD to detect if content is AI-generated.

    Args:
        content: The text content to analyse (or transcribed text for audio/video).
        content_type: One of 'text', 'image_caption', 'audio_transcript', 'video_transcript'.

    Returns:
        Dictionary with keys: is_ai_generated (bool), confidence (float), label (str), raw_response (dict).
    """
    api_base = os.getenv("OPENAI_API_BASE", "https://api.sea-lion.ai/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    guard_model = os.getenv("GUARD_MODEL", "aisingapore/SEA-LION-GUARD")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": guard_model,
        "messages": [{"role": "user", "content": content}],
    }

    try:
        response = requests.post(f"{api_base}/chat/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        is_ai = "ai-generated" in raw_text.lower()
        return {
            "is_ai_generated": is_ai,
            "confidence": None,  # parse from raw_text if model returns score
            "label": raw_text.strip(),
            "raw_response": data,
        }
    except Exception as e:
        return {"error": str(e), "is_ai_generated": None, "confidence": None, "label": "detection_failed"}


# ── SEA-LION Insights ─────────────────────────────────────────────────────────

def run_insights(content: str, detection_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use SEA-LION v4 to generate a plain-language explanation of the detection result.

    Args:
        content: The original user-submitted content.
        detection_result: Output from run_guard_detection.

    Returns:
        Dictionary with keys: explanation (str), suggested_action (str).
    """
    api_base = os.getenv("OPENAI_API_BASE", "https://api.sea-lion.ai/v1")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("MODEL", "aisingapore/Llama-SEA-LION-v3-70B-IT")

    prompt = f"""
You are analysing the following content for AI-generation signals.

Content: {content}
Detection verdict: {detection_result.get('label', 'Unknown')}

Provide:
1. A clear explanation of why this content may or may not be AI-generated.
2. Specific linguistic/visual/structural signals observed.
3. A recommended action for the user (e.g. verify source, treat as AI-generated, inconclusive).

Be concise. Do not over-censor. If evidence is weak, say so.
"""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
    }

    try:
        response = requests.post(f"{api_base}/chat/completions", json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        explanation = response.json()["choices"][0]["message"]["content"]
        return {"explanation": explanation, "suggested_action": "See explanation above."}
    except Exception as e:
        return {"error": str(e), "explanation": "Insights unavailable.", "suggested_action": "Manual review recommended."}


# ── ClickHouse Logger ─────────────────────────────────────────────────────────

def log_to_clickhouse(
    user_id: str,
    content_type: str,
    content_preview: str,
    detection_label: str,
    confidence: Optional[float],
    explanation: str,
) -> Dict[str, Any]:
    """
    Log a detection event to ClickHouse for real-time analytics.

    Args:
        user_id: Telegram user ID.
        content_type: 'text', 'image', 'audio', 'video'.
        content_preview: First 200 chars of submitted content.
        detection_label: Verdict label from GUARD model.
        confidence: Confidence score (0.0-1.0) or None.
        explanation: Insights explanation text.

    Returns:
        Status dictionary.
    """
    try:
        client = Client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", 9000)),
            user=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
            database=os.getenv("CLICKHOUSE_DB", "agent_logs"),
        )
        client.execute(
            "INSERT INTO detection_events (user_id, content_type, content_preview, detection_label, confidence, explanation) VALUES",
            [(user_id, content_type, content_preview[:200], detection_label, confidence, explanation)],
        )
        return {"status": "logged"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# ── SearXNG Web Search ────────────────────────────────────────────────────────

def searxng_search(query: str, language: Optional[str] = "en") -> Dict[str, Any]:
    """
    Search the web using SearXNG for contextual grounding.

    Args:
        query: Search query string.
        language: Language code (default: 'en').

    Returns:
        Dictionary with search results list.
    """
    searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8080")
    try:
        response = requests.get(
            f"{searxng_url}/search",
            params={"q": query, "format": "json", "language": language, "safesearch": 1},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "results": []}
```

---

### `translator.py` — Multilingual Subagent

```python
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

TRANSLATOR_PROMPT = """
You are a translation engine optimised for Singapore's multilingual context.

Supported languages: English, Mandarin Chinese (Simplified), Malay, Tamil, Singlish.

Rules:
- Translate the input to the target language specified.
- If no target language is specified, default to English.
- Preserve technical terms (e.g. "AI-generated", "deepfake") in English within translations.
- Output ONLY the translated text. No preamble, notes, or formatting.
"""

root_agent = LlmAgent(
    name="translator_agent",
    model=LiteLlm(
        model=f"openai/{os.getenv('MODEL', 'aisingapore/Gemma-SEA-LION-v3-9B-IT')}"
    ),
    description="Translates content across Singapore's languages: EN, ZH, MS, TA, Singlish.",
    instruction=TRANSLATOR_PROMPT,
    tools=[],
)
```

---

## 7. Telegram Bot Integration

The Telegram Bot acts as the multimodal frontend, routing inputs to the ADK agent:

| Input Type | Handling |
|---|---|
| **Text** | Passed directly to `run_guard_detection` |
| **Image** | Caption extracted; image metadata passed for visual analysis |
| **Audio** | Transcribed via STT (Deepgram); transcript passed to GUARD |
| **Video** | Frame-sampled and transcribed; combined input passed to GUARD |

Key Telegram handlers to implement in `tools.py`:
- `handle_text_message(update, context)`
- `handle_photo_message(update, context)`
- `handle_audio_message(update, context)`
- `handle_video_message(update, context)`

Each handler should: (1) extract content, (2) call the ADK `root_agent` runner, (3) return the formatted response to the user in their language.

---

## 8. ClickHouse Schema

```sql
CREATE TABLE detection_events (
    event_id        UUID DEFAULT generateUUIDv4(),
    timestamp       DateTime DEFAULT now(),
    user_id         String,
    content_type    Enum('text', 'image', 'audio', 'video'),
    content_preview String,
    detection_label String,
    confidence      Nullable(Float32),
    explanation     String
) ENGINE = MergeTree()
ORDER BY (timestamp, user_id);
```

---

## 9. MCP Subagent — Web Crawl & Context

MCP subagents use `.md` context files to ground responses. Structure your context files as:

```
adk_agent/
└── context/
    ├── ai_detection_signals.md     # Known signals of AI-generated content
    ├── singapore_languages.md      # Notes on Singlish, code-switching patterns
    └── harm_reduction_policy.md    # Guidelines on what to flag vs. not flag
```

The MCP subagent should be called when: GUARD confidence is below threshold (< 0.7), the user requests more context or sources, or content touches sensitive topics requiring grounded evidence.

---

## 10. Model Selection Guide

| Task | Model | Reason |
|---|---|---|
| AI-content detection | `aisingapore/SEA-LION-GUARD` | Specialised safety/detection model |
| Orchestration & reasoning | `aisingapore/Llama-SEA-LION-v3-70B-IT` | Complex multilingual reasoning |
| Translation subagent | `aisingapore/Gemma-SEA-LION-v3-9B-IT` | Lightweight, fast, single-purpose |
| Insights generation | `aisingapore/Llama-SEA-LION-v3-70B-IT` | Nuanced explanation quality |

---

## 11. Running the Agent

### Web Interface (Development)
```bash
cd parent_folder
adk web
# Access at http://localhost:8000
```

### CLI Interface (Testing)
```bash
cd parent_folder
python -m adk_agent.chat-cli
```

### Telegram Bot (Production)
```bash
cd parent_folder
python -m adk_agent.telegram_bot
```

---

## 12. Best Practices

- **Confidence thresholds**: Only return definitive verdicts above 0.85 confidence. Below this, surface uncertainty clearly to the user.
- **Avoid over-censoring**: Always show the reasoning. A low-confidence flag should never silently block content.
- **Language detection**: Auto-detect input language before routing to translator. Use `langdetect` or SEA-LION itself.
- **Session management**: Use `InMemorySessionService` for development; implement persistent ClickHouse-backed sessions for production.
- **Tool docstrings**: Always include parameter types, return format, and example usage — ADK uses these for tool-calling decisions.
- **Error fallbacks**: Every tool must return a structured error dict, never raise uncaught exceptions.

---

## 13. Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| Tool not being called | Instruction doesn't mention tool name | Add explicit tool reference in `SYSTEM_INSTRUCTION` |
| LiteLLM connection error | Wrong API base or key | Check `.env` values |
| `GOOGLE_GENAI_USE_VERTEXAI` error | Using SEA-LION API without Vertex | Set `GOOGLE_GENAI_USE_VERTEXAI=TRUE` |
| ClickHouse insert failure | Schema mismatch or connection issue | Check `detection_events` table schema |
| Translation not triggering | Translator not wrapped in `AgentTool` | Ensure `AgentTool(agent=translator)` in tools list |
| Telegram bot not receiving media | Missing file handler or bot permissions | Enable all message types in BotFather settings |