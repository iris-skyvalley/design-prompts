from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import openai
import base64
from PIL import Image
import io

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
async def generate_prompt(files: List[UploadFile] = File(...)):
    try:
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "No API key"}
        
        client = openai.OpenAI(api_key=api_key)
        
        # Convert uploaded files to base64 for OpenAI Vision API
        base64_images = []
        for file in files:
            # Read file data
            contents = await file.read()
            
            # Resize image for faster processing
            img = Image.open(io.BytesIO(contents))
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            resized_data = output.getvalue()
            
            base64_img = base64.b64encode(resized_data).decode('utf-8')
            base64_images.append(base64_img)
        
        # Analyze images using Vision API
        messages = [
            {
                "role": "system",
                "content": """You are a design analysis expert. Analyze these images to extract both SPECIFIC visual details AND overall aesthetic patterns.

FOR SINGLE WEBSITE SCREENSHOTS - Focus on SPECIFIC DETAILS:
1. EXACT COLOR DETAILS:
   - Primary background color (white, black, specific color)
   - Text colors (black text on white, white on dark, etc.)
   - Accent colors and their specific usage
   - Gradients, shadows, borders, effects

2. SPECIFIC TYPOGRAPHY:
   - Font weight (thin, regular, bold, black)
   - Font style (serif, sans-serif, rounded, angular)
   - Text hierarchy and sizing
   - Letter spacing and positioning

3. PRECISE LAYOUT STRUCTURE:
   - Element positioning (centered, left-aligned, grid)
   - Spacing patterns (tight, generous, specific gaps)
   - Background treatments and containers
   - Visual hierarchy and emphasis

FOR MULTIPLE DIFFERENT WEBSITES - Focus on COMMON PATTERNS:
4. SHARED AESTHETIC VIBE:
   - Overall feeling (minimalist, bold, playful, corporate)
   - Common color temperature patterns
   - Shared typography approaches
   - Similar layout philosophies

5. UNIFIED DESIGN LANGUAGE:
   - Consistent visual themes across images
   - Common component styling approaches
   - Shared spatial relationship patterns

IMPORTANT: Be specific about observable details (like "white background with black text") while also capturing the overall aesthetic direction."""
            }
        ]
        
        # Add user message with images
        user_content = [
            {
                "type": "text", 
                "text": "Analyze this screenshot and describe the EXACT visual details you can observe. Be specific about colors (e.g., 'white background with purple accents'), typography styles, layout structure, and spacing. If multiple screenshots, focus on common patterns. Describe what you actually see, not abstract design concepts."
            }
        ]
        
        for base64_img in base64_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_img}"
                }
            })
        
        messages.append({"role": "user", "content": user_content})
        
        # Call Vision API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        analysis = response.choices[0].message.content
        
        # Generate design prompts based on analysis
        system_prompt = """You are an anti-generic design expert. Your job is to create prompts that force AI to avoid typical patterns like center-aligned heroes, purple/blue gradients, and standard card layouts.

Your task:
1. Generate 3 short aesthetic vibe titles that capture the visual personality
2. Create a SIMPLE, SPECIFIC prompt with wildcards that breaks AI defaults

AVOID mentioning:
- Purple, blue, or gradient backgrounds
- Center-aligned hero sections
- Standard card grids
- "Clean and modern" descriptions
- Generic layout structures

INSTEAD, focus on:
- Unusual layout approaches (asymmetric, grid-breaking, unconventional navigation)
- Unexpected color combinations and approaches
- Distinctive typography treatments
- Specific wildcard alternatives that force variation

Create prompts that are concise but force unique, non-generic outputs."""

        user_prompt = f"""Based on this design analysis:

{analysis}

First, DESCRIBE the exact aesthetic from the screenshot analysis, then add enhancement wildcards.

Format (DESCRIBE what you see, don't change it):
**Style:** [Describe the EXACT aesthetic from the analysis - if it's purple/minimal/elegant, say that]
**Layout:** [Describe the layout approach you observe in the screenshot]  
**Colors:** [List the EXACT colors from the screenshot - background, text, and accent colors as they actually appear]
**Typography:** [Describe the typography style you observe in the screenshot]
**Mood:** [Describe the EXACT mood from the screenshot analysis]

**Enhancement Wildcards:**
Create 3 unique wildcards (1 from each category) that enhance this specific aesthetic:

**Animation/Interaction:** [Create 1 creative animation or interaction effect that matches this aesthetic and can be built with CSS/JS]

**Visual Effect:** [Create 1 visual effect or styling detail that enhances this aesthetic and is technically feasible]  

**Layout:** [Create 1 interesting layout approach that complements this aesthetic while being implementable]

Make each wildcard specific to this aesthetic and genuinely creative - avoid generic effects."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        
        # Parse for vibe titles
        import re
        prompts = []
        title_matches = re.findall(r'^\d+\.\s*(.+?)$', result, re.MULTILINE)
        if title_matches:
            prompts = [title.strip() for title in title_matches[:3]]
        else:
            # Fallback parsing
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            prompts = lines[:3] if len(lines) >= 3 else ['Modern Tech Aesthetic', 'Bold Minimalist Design', 'Innovative Functionality']
        
        # Create JSON output
        json_obj = {
            "landing_page_prompt": result,
            "vibe_titles": prompts,
            "style": "Custom design aesthetic generated from your images",
            "usage": "Use this design prompt to create your website"
        }
        
        return {"prompt_variations": prompts, "json_variation": json_obj}
        
    except Exception as e:
        return {"error": str(e), "type": str(type(e))}