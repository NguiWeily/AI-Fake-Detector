
from openai import OpenAI
from config import OPENAI_API_KEY, MODEL_NAME

client = OpenAI(api_key=OPENAI_API_KEY)

def detect_fake_text(text):
    prompt = f'''
Analyze the following WhatsApp or Telegram message.

Determine:
- Is it misinformation?
- Does it look like a scam/hoax?
- Give fake probability (0-100%).

Message:
{text}
'''
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI analysis error: {e}"
