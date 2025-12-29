# Production-Grade Flask + Groq Conversational AI

A production-ready conversational AI web application using Flask backend and Groq API for inference.

## Features

- **Groq API Integration**: Streaming token-by-token responses using Server-Sent Events (SSE)
- **Language Detection**: Automatic detection of English, Hindi, and Hinglish (code-mixed)
- **Session Management**: Persistent sessions with SQLite storage
- **Modern UI**: Black background with neon cyan accents and Matrix-style animated particles
- **Real-time Metrics**: Latency, tokens/sec, and error rate tracking
- **Health Monitoring**: Built-in health check endpoint

## Prerequisites

- Python 3.8+
- Groq API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd s
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variable:
```bash
# Option 1: Copy .env.example to .env and edit it
cp .env.example .env
# Then edit .env and add your Groq API key

# Option 2: Export directly in your shell
export GROQ_API_KEY="your-groq-api-key-here"
```

## Configuration

Edit `config/default.json` to customize:
- Groq models (llama3-70b, llama3-8b, mixtral)
- Temperature, max_tokens, top_p
- Server host and port
- Session timeout
- TTS settings

## Running the Application

```bash
python run.py
```

Or:
```bash
python -m app.app
```

Or:
```bash
python app/app.py
```

The application will start on `http://0.0.0.0:5000` (or as configured).

## API Endpoints

### Health Check
```
GET /health
```

### Create Session
```
POST /api/session
Content-Type: application/json

{}
```

### Get Session
```
GET /api/session/<session_id>
```

### Chat (Streaming)
```
POST /api/chat
Content-Type: application/json

{
    "message": "Hello",
    "session_id": "uuid",
    "model": "llama3-8b" (optional),
    "temperature": 0.7 (optional),
    "max_tokens": 2048 (optional),
    "top_p": 0.9 (optional)
}
```

### Get Available Models
```
GET /api/models
```

## Architecture

```
app/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── routes/
│   ├── chat.py           # Chat endpoints with SSE
│   ├── health.py         # Health check endpoint
│   └── session.py        # Session management endpoints
├── services/
│   ├── groq_inference.py # Groq API integration
│   ├── language_detect.py # Language detection
│   ├── session_manager.py # SQLite session management
│   ├── metrics.py        # Metrics collection
│   ├── tts_piper.py      # TTS service (structure)
│   └── audio_cache.py    # Audio caching
├── storage/
│   └── sessions.sqlite   # SQLite database (auto-created)
└── utils/
    ├── logger.py         # Logging configuration
    └── exceptions.py     # Custom exceptions
```

## Production Considerations

- **Error Handling**: All endpoints have comprehensive error handling
- **Logging**: Structured logging throughout the application
- **Session Cleanup**: Automatic cleanup of expired sessions
- **Metrics**: Built-in metrics collection for monitoring
- **Memory Safety**: Proper resource management and cleanup

## License

MIT

