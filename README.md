# Design Prompt Generator

A web application that analyzes design screenshots and generates creative design prompts for developers and designers.

## Features

- 📸 **Image Analysis**: Upload design screenshots to extract aesthetic patterns
- 🎲 **Surprise Me**: Generate creative design prompts from diverse aesthetic families
- 🔒 **Secure**: Rate limiting, file validation, and proper error handling
- ⚡ **Fast**: Real-time prompt generation with OpenAI Vision API

## Architecture

- **Backend**: FastAPI + OpenAI Vision API
- **Frontend**: React + Vite
- **Security**: Rate limiting, file validation, request logging

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
ALLOWED_ORIGINS=http://localhost:5173
```

Run backend:
```bash
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### Backend
```bash
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
npm run build
# Deploy dist/ folder to your hosting service
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Security Features

- File content validation beyond MIME types
- Rate limiting (10 requests per minute)
- Request logging with IP tracking
- No source maps in production builds
- Environment-based CORS configuration

## License

Private Project - All Rights Reserved