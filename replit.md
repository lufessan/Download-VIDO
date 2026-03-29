# Multi-Tool Arabic Platform (منصة الأدوات الذكية)

## Overview
The Multi-Tool Arabic Platform is a comprehensive web application offering ten powerful tools. Its primary purpose is to provide a suite of utilities for media processing, AI-driven content analysis, and document manipulation, all within a modern, Arabic RTL, glassmorphism-designed interface. The platform aims to serve users with efficient and intelligent tools for tasks like speech-to-text conversion, video cutting, anime and podcast detection, universal media downloading, PDF to Word conversion, video transcription, and AI-powered document formatting. It leverages advanced AI models and various APIs to deliver robust functionality, catering to both general users and those requiring specialized Arabic language support.

## Recent Changes (December 19, 2025)
- **Removed Smart Audio Cutter Tool:**
  - Deleted the audio cutter feature from the tools hub
  - Removed all related routes and frontend components
  - Streamlined the application to focus on core tools
- **Enhanced YouTube Video Cutter:**
  - Added new download option: "فيديو + صوت" (Video + Audio)
  - Users can now download both the video file and audio file after cutting
  - Maintains original video quality selection
  - Better support for multi-format downloads

## Previous Changes (December 7, 2025)
- **AI Provider Migration (Gemini → Groq + HuggingFace):**
  - Replaced Google Gemini with Groq API for text/audio/vision operations
  - Added HuggingFace Hub as secondary provider
  - New abstraction layer in `services/ai_providers.py` for multi-provider support
  - Automatic failover between providers
  - Session-based rate limiting (15 requests per 20 minutes)
  - 1-hour automatic cooldown for exhausted API keys
  - Manual enable/disable for individual keys via admin dashboard
- **Admin Dashboard for AI Providers:**
  - Access at `/admin/keys` (protected by admin login)
  - Default credentials: username=admin, password=admin123
  - Summary cards showing total providers, active, cooldown, and disabled counts
  - Hourly usage chart (last 24 hours) with Chart.js
  - Request type breakdown (text, vision, audio, video)
  - Provider table with filters (all, active, cooldown, disabled)
  - Sorting options (by index, usage, cooldown count, last used)
  - Enable/disable toggles for each provider
  - Auto-refresh every 30 seconds
- **Video Transcription Extended:**
  - Increased limit from 15 minutes to 2 hours (120 minutes)
  - Long video rate limiting (3 long videos per session)
- **Database Integration:**
  - PostgreSQL database for key state persistence and usage logging
  - Models: AdminUser, AIKeyState, AIUsageLog, DailyStats
- **Previous Changes (December 6, 2025):**
  - Mobile/Tablet Responsive Improvements
  - Sidebar Menu Button Fixes with debounce
- **Status:** Application is fully functional with new AI provider system

## User Preferences
I prefer simple language and clear explanations. I want iterative development where I can provide feedback at each stage. Ask before making major changes to the project's architecture or core functionalities. Ensure the application maintains its Arabic RTL design and glassmorphism aesthetic. All new features should seamlessly integrate with the existing UI/UX. Do not make changes to the `replit.md` file without explicit instruction.

## System Architecture
The platform is built on a Python Flask backend with a responsive frontend using HTML5, Tailwind CSS, and JavaScript.

**UI/UX Decisions:**
- **Design:** Modern glassmorphism aesthetic with a focus on Arabic Right-to-Left (RTL) layout.
- **Responsiveness:** Mobile-first design with a floating menu toggle for small screens.
- **Authentication:** Supabase integration for user login/registration and session management, blocking tool access until authentication.

**Technical Implementations & Feature Specifications:**
- **Speech-to-Text Live:** Utilizes `webkitSpeechRecognition` for real-time Arabic transcription, including continuous listening with wake lock and automatic restarts.
- **YouTube Video Cutter:** Extracts and cuts video segments using `yt-dlp` and `ffmpeg`.
- **Anime Detector:** Dual mode (Image/Name search) leveraging `trace.moe` and Anilist GraphQL API, with AI Vision for enhanced image analysis and strict similarity thresholds.
- **Podcast Detector:** Dual mode (Image/Audio) using Tesseract OCR, SpeechRecognition, and AI for identification, featuring smart links to streaming platforms and advanced prompt engineering for host/platform hints.
- **Audio File Transcription:** Transcribes audio files (various formats) to text using Google Speech API.
- **OCR - Extract Text from Image:** Extracts text from images (PNG, JPG, etc.) using Tesseract, supporting Arabic and English.
- **Universal Media Downloader:** Downloads video/audio from multiple platforms via `yt-dlp`, converting to MP4/MP3, with size and duration limits.
- **Smart PDF to Word Converter:** Converts PDFs to DOCX using `pdf2docx`, offering translation to Arabic or English via `deep_translator`.
- **Video to Text Transcription:** Transcribes video content (file upload or URL) to text using Groq AI, supporting multiple languages, and optimized for large files and slow connections.
- **AI Document Formatter:** Formats Word/PDF documents using Groq AI, allowing formatting specification via text description or reference files, and supporting features like heading styling, margins, and line spacing.
- **Smart Audio Cutter:** Cuts audio files without AI dependency, using ffmpeg for efficient processing. Supports both file uploads and video URL conversion to MP3, with precise time-based trimming.

**System Design Choices:**
- **AI Integration:** Multi-provider AI engine with Groq (primary) and HuggingFace (secondary), automatic failover, smart cooldown for exhausted keys, admin dashboard for key management, and database persistence for usage analytics.
- **Media Processing:** Extensive use of `ffmpeg` for audio/video manipulation and `yt-dlp` for media extraction.
- **Backend Infrastructure:** Flask application served by Gunicorn with extended timeouts (1800s) for long-running tasks, configured for Replit deployment.
- **Concurrency:** 2 Gunicorn workers with 4 threads each for improved concurrency.
- **File Handling:** Temporary files are managed and deleted post-processing to conserve server space.
- **Proxy Configuration:** Flask app uses ProxyFix middleware to properly handle Replit's proxy setup.

## External Dependencies
- **Backend Framework:** Flask
- **Frontend Technologies:** HTML5, Tailwind CSS, JavaScript
- **Core Libraries:** `yt-dlp`, `ffmpeg` (system-level), `SpeechRecognition`, `pytesseract`, `pydub`, `Pillow`, `fuzzywuzzy`, `python-Levenshtein`, `pdf2docx`, `python-docx`, `deep_translator`, `groq`, `huggingface-hub`
- **APIs & Services:**
    - `trace.moe` (Anime detection)
    - `Anilist GraphQL API` (Anime information)
    - `iTunes Search API` (Podcast detection)
    - `Groq API` (Primary AI - Text, Vision, Audio operations)
    - `HuggingFace Hub` (Secondary AI provider)
    - `Supabase Auth` (User authentication and management)
- **OCR Engine:** `Tesseract` (system-level)

## Environment Variables
**Required:**
- `SESSION_SECRET` - Flask session secret (already configured in Replit)
- `GROQ_API_KEY` - Groq API key for AI features (primary provider)

**Optional (for additional features):**
- `HUGGINGFACE_API_KEY` - HuggingFace API key (secondary provider)
- `SUPABASE_URL` - Supabase project URL for authentication
- `SUPABASE_ANON_KEY` - Supabase anonymous key for authentication
- `COOKIE_CONTENT` - YouTube cookies for downloading age-restricted content

**Notes:**
- Groq is the primary AI provider, HuggingFace is secondary/fallback
- Without Supabase credentials, app runs in development mode (authentication disabled)
- Get Groq API key from: https://console.groq.com/keys
- Get HuggingFace API key from: https://huggingface.co/settings/tokens

## Replit Environment Setup
- **Database:** PostgreSQL (Neon-backed) - automatically configured via DATABASE_URL
- **System Dependencies:** ffmpeg, tesseract (for OCR)
- **Python Version:** 3.11
- **Server:** Gunicorn on port 5000 (2 workers, 300s timeout)
- **Workflow:** Flask Server runs gunicorn for the web application
