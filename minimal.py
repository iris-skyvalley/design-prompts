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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "No API key"}
        
        client = openai.OpenAI(api_key=api_key)
        
        system_prompt = """You are a diverse, creative WEB DESIGN generator. Create varied design concepts from many different aesthetic families. Be creative and draw from a wide range of design inspirations.

Your task:
1. Generate 3 completely unique aesthetic vibe titles from DIFFERENT style families 
2. Create 1 detailed design prompt with creative but IMPLEMENTABLE features

STYLE VARIETY - Draw from diverse aesthetics like:
- Warm earthy tones and natural textures
- Bright, cheerful, candy-colored palettes  
- Retro 70s/80s/90s nostalgic vibes
- Hand-drawn, organic, craft-inspired looks
- Minimalist Scandinavian clean designs
- Tropical, beach, vacation aesthetics
- Vintage paper, bookstore, library feels
- Playful toy-like, children's book styles
- Space/cosmic themes (occasionally)
- Art deco, brutalist, or other architectural styles

IMPORTANT: Vary your aesthetic choices! Don't default to the same style patterns. Mix light and dark, warm and cool, minimal and maximalist approaches.

AVOID impossible features like:
- Scents, sounds, or physical sensations
- Real-world physics beyond CSS transforms
- Features that require hardware not available in browsers

Be varied, colorful, and draw from many different design traditions!"""

        user_prompt = """Create a WEB DESIGN concept from a NON-SPACE aesthetic family. Be creative but avoid cosmic/celestial/galaxy themes.

BANNED WORDS/CONCEPTS (do not use):
- Celestial, cosmic, galaxy, space, stars, nebula, universe
- Dreamscape, ethereal, mystical, otherworldly  
- Dark backgrounds with glowing elements
- Purple/blue gradient combinations

REQUIRED: Choose from these aesthetic inspirations:
- Warm embrace of morning light filtering through steam
- Vibrant coral reef energy with electric blues and living greens
- Neon rebellion of underground scenes and electric nights
- Moss-covered wisdom with ancient bark and mushroom softness  
- Sugar rush dreamscape in pastel candy clouds
- Gilded age opulence meets geometric precision
- Nordic clarity where light meets natural wood grain
- Sun-baked earth meeting rose-tinted horizons
- Fire season intensity with burnished golds
- Cabin fever comfort wrapped in evergreen shadows
- Zen tranquility with blossoms floating on stone
- Festival explosion of citrus and magenta celebration
- Mediterranean warmth where olive trees meet golden hour
- Velvet luxury from forgotten grand ballrooms
- Atomic age optimism in mustard and teal
- Urban decay poetry in rust and weathered steel
- Market day abundance in fresh greens and sunset reds
- Literary sanctuary wrapped in leather and lamplight
- Salt air serenity with weathered wood and sea glass
- Vineyard mystery in deep purples and cork shadows
- Childhood wonder in strawberry cream dreams
- Artist's palette chaos in primary boldness
- Revolution era passion in blood red proclamations
- Watercolor accident beauty in soft lavender spills
- Kiln-fired earth in glaze-blue surprises

Format:
**Style:** [One specific aesthetic from the approved families above - but make it feel MODERN and CONTEMPORARY]
**Layout:** [One experimental layout approach using modern CSS/JS techniques]  
**Colors:** [One bold color approach from your chosen aesthetic family with a modern twist]
**Typography:** [One experimental typography treatment that feels current and fresh]
**Mood:** [One specific emotional feeling that matches your chosen aesthetic but feels relevant today]

**IMPLEMENTABLE Creative Wildcards:**
Generate 3 fun wildcards that match your chosen aesthetic family and can be built with modern web technologies.

CRITICAL: Make everything feel MODERN and CONTEMPORARY. Avoid dated references or old-fashioned approaches. Think current design trends with your chosen aesthetic inspiration."""

        import time
        import random
        
        # Add randomization to prevent caching/repetition
        timestamp = int(time.time())
        random_seed = random.randint(1000, 9999)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{user_prompt}\n\nGenerate something completely unique for request #{random_seed} at {timestamp}"},
            ],
            temperature=0.9,  # High creativity
            max_tokens=800
        )
        
        result = response.choices[0].message.content
        
        # Parse similar to the regular prompts
        import re
        prompts = []
        
        # Try to extract vibe titles
        title_matches = re.findall(r'^\d+\.\s*(.+?)$', result, re.MULTILINE)
        if title_matches:
            prompts = [title.strip() for title in title_matches[:3]]
        else:
            # Fallback parsing
            quoted_matches = re.findall(r'["\']([^"\']+)["\']', result)
            if quoted_matches:
                prompts = quoted_matches[:3]
            else:
                prompts = ['Experimental Wildcard Design', 'Creative Surprise Aesthetic', 'Bold Unconventional Concept']
        
        # Create JSON output
        json_obj = {
            "landing_page_prompt": result,
            "vibe_titles": prompts,
            "style": "Surprise me - creative experimental design",
            "usage": "Use this creative prompt to build something completely unexpected and unique"
        }
        
        return {"prompt_variations": prompts, "json_variation": json_obj}
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}

@app.post("/generate-prompt/")
def generate_prompt():
    return {"message": "generate works", "prompt_variations": ["test prompt"], "json_variation": {"landing_page_prompt": "Test landing page prompt"}}