# Fake Media Detector API

This project detects suspicious or fake **text, images, and videos** commonly shared on WhatsApp or Telegram.

## Features

- AI misinformation detection
- Image manipulation detection
- OCR text extraction from images
- Video frame analysis
- REST API using FastAPI

## Installation

1. Install Python 3.10+

2. Install dependencies

pip install -r requirements.txt

3. Add your Gemini API key in `config.py` or environment

GEMINI_API_KEY = "YOUR_GEMINI_KEY"

4. Run the server

uvicorn app:app --reload

Server runs at:

http://localhost:8000

## API Endpoints

### Detect Text

POST /detect-text

Example:

{
"text": "Forwarded many times: Government giving $5000 grant..."
}

### Detect Image

POST /detect-image

Upload image file.

### Detect Video

POST /detect-video

Upload video file.

## Integration

You can connect this API with:

- Telegram Bot
- WhatsApp Business API
- Mobile apps
- Web dashboards

## Telegram Bot
Install dependencies:
python -m pip install -r requirements.txt

Set bot token in terminal:
$env:TELEGRAM_TOKEN = "123:ABC-your-token-here"

Run the bot:
python telegram_bot.py --cli "TEXT_HERE"

## AI Provider (Gemini)
This project uses Google Gemini via the `google-generativeai` package.

Set `GEMINI_API_KEY` in your environment (or in `config.py`) and run the CLI:

```powershell
set GEMINI_API_KEY=your_gemini_key_here
python detect_cli.py "Some text to analyze"
```

If the `google-generativeai` package or `GEMINI_API_KEY` is missing, the CLI will print a clear error.