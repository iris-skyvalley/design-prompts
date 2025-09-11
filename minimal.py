from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS
ALLOWED_ORIGINS = ["http://localhost:5173", "https://design-prompts.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test")
def test():
    return {"message": "test works"}

@app.post("/generate-prompt/")
def generate_prompt():
    return {"message": "generate works", "prompt_variations": ["test prompt"], "json_variation": {"landing_page_prompt": "Test landing page prompt"}}

@app.post("/surprise-me/")
def surprise_me():
    return {"message": "surprise works", "prompt_variations": ["surprise prompt"], "json_variation": {"landing_page_prompt": "Surprise landing page prompt"}}