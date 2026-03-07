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

3. Add your OpenAI API key in `config.py`

OPENAI_API_KEY = "YOUR_API_KEY"

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