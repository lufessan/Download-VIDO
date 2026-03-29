---
title: Humata-rec
emoji: 📎
colorFrom: purple
colorTo: pink
sdk: docker
pinned: false
---

# Humata-rec

(اكتب تحت هنا أي شرح للمشروع لو حابب)

# Multi-Tool Platform | منصة الأدوات المتعددة

A comprehensive Flask-based web application with AI-powered audio/video processing tools, optimized for Arabic language processing.

## Features

### 1. Live Speech to Text (تحويل الصوت لنص مباشر)
- Real-time speech recognition using Web Speech API
- Supports Arabic and multiple languages
- Continuous listening mode for long recordings
- Word and character count tracking

### 2. YouTube Video Cutter (قص فيديو يوتيوب)
- Cut specific portions from YouTube videos
- Download clips with custom start/end times
- Video information preview

### 3. Anime Finder (كاشف الأنمي)
- Identify anime from screenshots using trace.moe API
- Search anime by name with AniList integration
- Episode and timestamp detection

### 4. Podcast Finder (كاشف البودكاست)
- Search podcasts using iTunes Search API
- Find podcasts by keywords or topics
- Display podcast details and episodes

### 5. Audio File Transcription (تحويل ملف صوتي)
- Convert audio files to text using Google Gemini AI
- Supports 14+ languages including Arabic
- Handles long audio files (up to 2 hours)
- Smart API key rotation with load balancing

### 6. OCR - Extract Text from Images (استخراج النص من الصورة)
- Extract text from images using Tesseract OCR
- AI-powered image analysis with Google Gemini
- Supports Arabic and English text

### 7. Universal Video Downloader (تحميل فيديو من أي موقع)
- Download videos from multiple platforms
- Powered by yt-dlp

### 8. PDF Converter (محول PDF الذكي)
- Convert PDF to Word documents
- Arabic text support
- Translation capabilities

### 9. Video to Text (تحويل الفيديو إلى نص)
- Transcribe videos up to 2 hours
- Upload video files or paste URLs
- AI-powered transcription with Gemini

## Requirements

### System Dependencies
- Python 3.11+
- FFmpeg
- Tesseract OCR

### Python Dependencies
See `requirements.txt` for the complete list.

## Environment Variables

Required environment variables:

```
GEMINI_API_KEY=your_gemini_api_key
GEMINI_KEY_1=optional_additional_key
GEMINI_KEY_2=optional_additional_key
...
GEMINI_KEY_11=optional_additional_key
SESSION_SECRET=your_session_secret
DATABASE_URL=your_postgresql_database_url
```

The application supports up to 11 Gemini API keys for load balancing with automatic rotation and 1-hour cooldown for exhausted keys.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multi-tool-platform.git
cd multi-tool-platform
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg tesseract-ocr tesseract-ocr-ara

# macOS
brew install ffmpeg tesseract tesseract-lang
```

4. Set up environment variables (create a `.env` file or export them)

5. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload --timeout 1800 --workers 2 --threads 4 main:app
```

## Deployment

### Recommended Free Hosting Platforms

1. **Render.com** (Recommended)
   - Free tier with 750 hours/month
   - Supports Python/Flask
   - Easy deployment from GitHub
   - Free PostgreSQL database
   - Automatic HTTPS

2. **Railway.app**
   - $5 free credit monthly
   - Easy GitHub integration
   - PostgreSQL support
   - Good for Python apps

3. **Koyeb.com**
   - Free tier available
   - Global deployment
   - GitHub integration

4. **Fly.io**
   - Generous free tier
   - Global CDN
   - PostgreSQL support

### Deployment Notes
- Set all environment variables in the hosting platform
- Configure the start command: `gunicorn --bind 0.0.0.0:$PORT --timeout 1800 --workers 2 --threads 4 main:app`
- Ensure FFmpeg and Tesseract are available (most platforms support buildpacks)

## API Keys

### Google Gemini API
Get your API key from: https://aistudio.google.com/app/apikey

The application supports multiple API keys for load balancing:
- `GEMINI_API_KEY` - Primary key
- `GEMINI_KEY_1` through `GEMINI_KEY_11` - Additional keys

## License

MIT License

## Author

Developed by Mahmoud Adel (المبرمج محمود عادل)
