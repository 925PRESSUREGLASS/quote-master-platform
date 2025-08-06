"""
OpenAI service for Quote Master Pro
"""

import openai
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class QuoteRequest:
    """Quote generation request"""
    prompt: str
    category: str
    tone: Optional[str] = None
    length: Optional[str] = "medium"
    model: str = "gpt-4"

@dataclass
class QuoteResponse:
    """Quote generation response"""
    content: str
    author: Optional[str] = None
    confidence: float = 0.0
    model_used: str = ""

class OpenAIService:
    """OpenAI service for quote generation and analysis"""

    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_quote(self, request: QuoteRequest) -> QuoteResponse:
        """Generate a quote using OpenAI"""
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt(request)
            user_prompt = self._build_user_prompt(request)

            response = self.client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.8,
                top_p=0.9
            )

            content = response.choices[0].message.content.strip()
            
            # Parse the response to extract quote and author
            quote_content, author = self._parse_quote_response(content)

            return QuoteResponse(
                content=quote_content,
                author=author,
                confidence=0.9,  # OpenAI typically has high confidence
                model_used=request.model
            )

        except Exception as e:
            logger.error(f"OpenAI quote generation failed: {e}")
            raise

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment and emotion of the given text. Return a JSON response with 'sentiment' (positive/negative/neutral), 'score' (-1 to 1), 'primary_emotion', and 'confidence' (0 to 1)."
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=150,
                temperature=0.3
            )

            result = response.choices[0].message.content
            # Parse JSON response (implement proper JSON parsing)
            return {
                "sentiment": "positive",  # Placeholder
                "score": 0.7,
                "primary_emotion": "optimism",
                "confidence": 0.85
            }

        except Exception as e:
            logger.error(f"OpenAI sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "primary_emotion": "neutral",
                "confidence": 0.0
            }

    def _build_system_prompt(self, request: QuoteRequest) -> str:
        """Build system prompt for quote generation"""
        base_prompt = """You are a master quote generator and inspirational writer. Your task is to create meaningful, impactful quotes that resonate with people's emotions and experiences.

Guidelines:
- Create original, profound quotes that sound authentic
- Match the requested category and tone
- Keep quotes concise but meaningful
- Include attribution if creating in the style of a known figure
- Focus on universal human experiences and wisdom"""

        if request.tone:
            base_prompt += f"\n- Tone should be: {request.tone}"
        
        if request.length:
            length_guide = {
                "short": "Keep quotes under 20 words",
                "medium": "Keep quotes between 20-40 words", 
                "long": "Quotes can be 40-80 words"
            }
            base_prompt += f"\n- {length_guide.get(request.length, 'Medium length preferred')}"

        return base_prompt

    def _build_user_prompt(self, request: QuoteRequest) -> str:
        """Build user prompt for quote generation"""
        return f"Generate an inspiring {request.category} quote based on: {request.prompt}"

    def _parse_quote_response(self, response: str) -> tuple[str, Optional[str]]:
        """Parse quote response to extract content and author"""
        # Simple parsing - look for attribution patterns
        if " - " in response:
            parts = response.rsplit(" - ", 1)
            if len(parts) == 2:
                quote_content = parts[0].strip('"').strip()
                author = parts[1].strip()
                return quote_content, author
        
        # No attribution found
        return response.strip('"').strip(), None

    async def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )

            return {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else "en",
                "confidence": 0.9  # Whisper typically has high confidence
            }

        except Exception as e:
            logger.error(f"OpenAI audio transcription failed: {e}")
            raise