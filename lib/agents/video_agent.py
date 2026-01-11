"""
Video agent for generating storyboards from documentation
"""

import json
import os
from typing import Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

from lib.logger import create_logger

load_dotenv()

log = create_logger('VIDEO')

# Initialize client
api_key = os.getenv('GOOGLE_API_KEY')
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

VIDEO_SYSTEM_PROMPT = """You are an expert video content creator. Your job is to transform documentation into engaging 7-10 slide video storyboards for employee training.

## OUTPUT FORMAT
You MUST output valid JSON with this exact structure:
{
  "slides": [
    {
      "title": "Slide title (short, catchy)",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "imagePrompt": "Detailed description for AI image generation - describe a professional diagram or visualization",
      "voiceover": "30-60 second narration script. Conversational, clear, engaging."
    }
  ]
}

## SLIDE STRUCTURE (10 slides recommended)
1. **Opening** - Hook the viewer, introduce the topic, what they'll learn
2-3. **Context** - Set the scene, explain why this matters to users
4-7. **Main Content** - Core information, features, how things work
8-9. **Practical Tips** - How to help users, common scenarios
10. **Closing** - Summary, key takeaways, next steps

## RULES
- Create exactly 7-10 slides (prefer 10 for comprehensive topics)
- Each voiceover should be 30-60 seconds when read aloud (~75-150 words)
- Write voiceovers as if speaking to a colleague - conversational and clear
- Keep titles short (3-6 words maximum)
- Include 2-4 bullet points per slide
- Total video should be 5-8 minutes

## IMAGE PROMPT GUIDELINES
- Describe professional diagrams, charts, or illustrations
- Focus on clear, simple visuals that support the narration
- Avoid complex scenes - prefer abstract/conceptual representations
- Example: "A clean diagram showing data flowing from a database through an API to a mobile app"

## VOICEOVER GUIDELINES
- Write as if speaking directly to the viewer
- Use "you" and "we" naturally
- Keep sentences short and clear
- Include transitions between points
- Add emphasis where needed (the AI will handle tone)

Output ONLY valid JSON. No markdown, no explanations, just the JSON object."""

def generate_storyboard(document_title: str, document_content: str) -> Dict[str, Any]:
    """
    Generate a video storyboard from documentation
    
    Args:
        document_title: Title of the document
        document_content: Full content of the document
        
    Returns:
        Storyboard dict with slides array
    """
    log.info(f'Generating storyboard for: {document_title}')
    
    prompt = f"""Transform this documentation into an engaging video storyboard.

**Document Title:** {document_title}

**Content:**
{document_content[:8000]}  # Limit content to avoid token limits

Create a compelling 7-10 slide video that will help employees understand this topic. Focus on what's actionable and relevant to supporting users.

Output the storyboard as valid JSON following the format specified in your instructions."""

    try:
        if not client:
            raise ValueError('Gemini client not initialized - check GOOGLE_API_KEY')
        
        # Use Gemini 2.0 Flash for better storyboard generation
        config = types.GenerateContentConfig(
            system_instruction=VIDEO_SYSTEM_PROMPT,
            temperature=0.8,
            response_mime_type='application/json'
        )
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=config
        )
        
        # Parse JSON response
        storyboard_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if storyboard_text.startswith('```json'):
            storyboard_text = storyboard_text[7:]
        if storyboard_text.startswith('```'):
            storyboard_text = storyboard_text[3:]
        if storyboard_text.endswith('```'):
            storyboard_text = storyboard_text[:-3]
        
        storyboard = json.loads(storyboard_text.strip())
        
        log.info(f'Storyboard generated: {len(storyboard.get("slides", []))} slides')
        
        return storyboard
        
    except json.JSONDecodeError as e:
        log.error(f'Failed to parse storyboard JSON: {e}')
        log.error(f'Response text: {response.text[:500]}')
        raise ValueError(f'Invalid JSON response from AI: {e}')
    except Exception as e:
        log.error(f'Storyboard generation failed: {e}')
        raise
