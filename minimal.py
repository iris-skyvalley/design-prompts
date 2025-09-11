import os
import openai
import base64
import logging
import time
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Design Prompt Generator", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Environment variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,https://design-prompts.vercel.app").split(",")
logger.info(f"Allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

SUPPORTED_FORMATS = {"image/png", "image/jpeg", "image/jpg", "image/svg+xml"}
MAX_IMAGES = 5
MAX_SIZE_MB = 10

# Initialize OpenAI client (will be initialized on first use if API key is available)
client = None

def get_openai_client():
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        client = openai.OpenAI(api_key=api_key)
    return client

async def validate_image_content(file_data: bytes, filename: str) -> bool:
    """Validate that uploaded file is actually an image by checking magic bytes"""
    try:
        from PIL import Image
        import io
        
        # Check if PIL can open and verify the image
        img = Image.open(io.BytesIO(file_data))
        img.verify()  # Verify it's a valid image
        
        # Additional checks
        if img.size[0] < 10 or img.size[1] < 10:  # Too small
            return False
        if img.size[0] > 4096 or img.size[1] > 4096:  # Too large
            return False
            
        return True
    except Exception as e:
        logger.warning(f"Invalid image file {filename}: {str(e)}")
        return False

async def analyze_design_images(image_data_list: List[bytes]) -> dict:
    """Analyze design images using OpenAI Vision API to extract design features"""
    
    # Resize images for faster processing
    from PIL import Image
    import io
    
    base64_images = []
    for img_data in image_data_list:
        try:
            # Resize image to max 512px on longest side for faster processing
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            resized_data = output.getvalue()
            
            base64_img = base64.b64encode(resized_data).decode('utf-8')
            base64_images.append(base64_img)
        except Exception as e:
            print(f"Error resizing image: {e}")
            # Fallback to original if resize fails
            base64_img = base64.b64encode(img_data).decode('utf-8')
            base64_images.append(base64_img)
    
    # Create messages with images
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
    
    try:
        response = get_openai_client().chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        print("Vision API call successful")
    except Exception as e:
        print(f"Vision API call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze images: {str(e)}")
    
    analysis = response.choices[0].message.content
    
    # Parse the analysis into structured features
    # This is a simple parser - could be made more sophisticated
    features = {
        "analysis": analysis,
        "color_palette": [],
        "typography": "",
        "layout": "",
        "components": [],
        "mood": ""
    }
    
    return features

async def generate_design_prompts(features: dict) -> dict:
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

{features.get('analysis', features)}

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

    response = get_openai_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=1000
    )
    text = response.choices[0].message.content
    print(f"Full OpenAI response: {text}")
    
    # Parse the response for vibe titles and landing page prompt
    prompts = []
    landing_page_prompt = ""
    import re
    
    # Try to extract vibe titles (first part)
    title_matches = re.findall(r'^\d+\.\s*(.+?)$', text, re.MULTILINE)
    if title_matches:
        prompts = [title.strip() for title in title_matches[:3]]
    else:
        # Fallback: look for quoted titles or distinctive patterns
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted_matches:
            prompts = quoted_matches[:3]
        else:
            # Last fallback: split and take first few lines
            lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('Create') and not line.startswith('Design')]
            prompts = lines[:3] if len(lines) >= 3 else ['Modern Tech Aesthetic', 'Bold Minimalist Design', 'Innovative Functionality']
    
    # Extract the design prompt - look for any substantial content after the titles
    lines = text.split('\n')
    
    # Find where the main content starts (after the numbered titles)
    content_start = 0
    for i, line in enumerate(lines):
        if i >= 3:  # After first 3 titles
            if line.strip() and not line.strip().startswith(('1.', '2.', '3.')):
                content_start = i
                break
    
    if content_start > 0:
        # Take everything from content_start onward as the design prompt
        remaining_lines = lines[content_start:]
        landing_page_prompt = '\n'.join(remaining_lines).strip()
    
    # If no substantial content found, look for any large paragraph
    if not landing_page_prompt or len(landing_page_prompt) < 100:
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if len(para.strip()) > 150:  # Substantial content
                landing_page_prompt = para.strip()
                break
    
    # If no design prompt found, use the raw OpenAI response
    if not landing_page_prompt:
        landing_page_prompt = text  # Use the full OpenAI response
    
    # Create JSON output with the landing page prompt (hide internal processing)
    json_obj = {
        "landing_page_prompt": landing_page_prompt,
        "vibe_titles": prompts,
        "style": "Custom design aesthetic generated from your images",
        "usage": "Use this design prompt to create your website"
    }
    
    return {"prompt_variations": prompts, "json_variation": json_obj}

async def generate_surprise_prompts() -> dict:
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
- Mysterious depths where light becomes liquid
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
    
    response = get_openai_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt}\n\nGenerate something completely unique for request #{random_seed} at {timestamp}"},
        ],
        temperature=0.9,  # High creativity
        max_tokens=800
    )
    text = response.choices[0].message.content
    print(f"Surprise prompt response for {random_seed}: {text[:200]}...")
    
    # Parse similar to the regular prompts
    prompts = []
    landing_page_prompt = ""
    import re
    
    # Try to extract vibe titles
    title_matches = re.findall(r'^\d+\.\s*(.+?)$', text, re.MULTILINE)
    if title_matches:
        prompts = [title.strip() for title in title_matches[:3]]
    else:
        # Fallback parsing
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
        if quoted_matches:
            prompts = quoted_matches[:3]
        else:
            prompts = ['Experimental Wildcard Design', 'Creative Surprise Aesthetic', 'Bold Unconventional Concept']
    
    # Use the full response as the landing page prompt
    landing_page_prompt = text
    
    # Create JSON output
    json_obj = {
        "landing_page_prompt": landing_page_prompt,
        "vibe_titles": prompts,
        "style": "Surprise me - creative experimental design",
        "usage": "Use this creative prompt to build something completely unexpected and unique"
    }
    
    return {"prompt_variations": prompts, "json_variation": json_obj}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@limiter.limit("10/minute")
@app.post("/generate-prompt/")
async def generate_prompt(request: Request, files: List[UploadFile] = File(...)):
    client_ip = request.client.host
    logger.info(f"Generate prompt request from {client_ip} with {len(files)} files")
    
    if not (1 <= len(files) <= MAX_IMAGES):
        logger.warning(f"Invalid file count from {client_ip}: {len(files)} files")
        raise HTTPException(status_code=400, detail="Upload 1-5 images.")
    
    image_data_list = []
    for file in files:
        if file.content_type not in SUPPORTED_FORMATS:
            logger.warning(f"Unsupported file type from {client_ip}: {file.content_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        contents = await file.read()
        if len(contents) > MAX_SIZE_MB * 1024 * 1024:
            logger.warning(f"File too large from {client_ip}: {len(contents)} bytes")
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 10MB size limit.")
        
        # Validate actual image content
        if not await validate_image_content(contents, file.filename):
            logger.warning(f"Invalid image content from {client_ip}: {file.filename}")
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a valid image.")
            
        image_data_list.append(contents)
    
    try:
        # Analyze images using Vision API
        print(f"Analyzing {len(image_data_list)} images...")
        features = await analyze_design_images(image_data_list)
        print(f"Analysis result: {features.get('analysis', 'No analysis found')[:200]}...")
        
        # Generate design prompts based on analysis
        result = await generate_design_prompts(features)
        return JSONResponse(result)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error processing images: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@limiter.limit("10/minute")
@app.post("/surprise-me/")
async def surprise_me(request: Request):
    client_ip = request.client.host
    logger.info(f"Surprise me request from {client_ip}")
    
    try:
        # Generate random creative design prompts without image analysis
        result = await generate_surprise_prompts()
        logger.info(f"Surprise prompt generated successfully for {client_ip}")
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error generating surprise prompts for {client_ip}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
