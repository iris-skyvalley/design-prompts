from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import openai

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

@app.post("/surprise-me/")
def surprise_me():
    try:
        # Minimal OpenAI test
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "No API key"}
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Generate 3 creative web design prompt titles"}],
            temperature=0.8,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        
        return {
            "prompt_variations": ["Test 1", "Test 2", "Test 3"], 
            "json_variation": {"landing_page_prompt": result}
        }
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}

@app.post("/generate-prompt/")
def generate_prompt():
    return {"message": "generate works", "prompt_variations": ["test prompt"], "json_variation": {"landing_page_prompt": "Test landing page prompt"}}