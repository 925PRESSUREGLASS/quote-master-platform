"""Quote generation engine for Quote Master Pro."""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import json

from .psychology import PsychologyAnalyzer
from .calculator import QuoteCalculator
from src.services.ai.orchestrator import get_ai_orchestrator
from src.core.config import get_settings
from src.core.exceptions import QuoteGenerationException

logger = logging.getLogger(__name__)
settings = get_settings()


class QuoteStyle(str, Enum):
    """Quote style enumeration."""
    INSPIRATIONAL = "inspirational"
    MOTIVATIONAL = "motivational"
    PHILOSOPHICAL = "philosophical"
    HUMOROUS = "humorous"
    POETIC = "poetic"
    SPIRITUAL = "spiritual"
    BUSINESS = "business"
    LIFE_WISDOM = "life_wisdom"
    RELATIONSHIP = "relationship"
    SUCCESS = "success"
    MINDFULNESS = "mindfulness"
    PERSONAL_GROWTH = "personal_growth"


class QuoteTone(str, Enum):
    """Quote tone enumeration."""
    POSITIVE = "positive"
    UPLIFTING = "uplifting"
    REFLECTIVE = "reflective"
    EMPOWERING = "empowering"
    CALMING = "calming"
    ENERGETIC = "energetic"
    THOUGHTFUL = "thoughtful"
    ENCOURAGING = "encouraging"
    WISE = "wise"
    PLAYFUL = "playful"


class QuoteLength(str, Enum):
    """Quote length enumeration."""
    SHORT = "short"        # 1-15 words
    MEDIUM = "medium"      # 16-35 words
    LONG = "long"          # 36+ words


class QuoteEngine:
    """Advanced quote generation engine with psychology integration."""
    
    def __init__(self):
        self.ai_orchestrator = get_ai_orchestrator()
        self.psychology_analyzer = PsychologyAnalyzer()
        self.quote_calculator = QuoteCalculator()
        self._style_templates = self._load_style_templates()
        self._psychological_frameworks = self._load_psychological_frameworks()
    
    def _load_style_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load quote style templates and guidelines."""
        
        return {
            QuoteStyle.INSPIRATIONAL: {
                "characteristics": [
                    "Uplifting and encouraging",
                    "Focuses on possibility and potential",
                    "Often uses metaphors from nature or journey",
                    "Emphasizes hope and positive outcomes"
                ],
                "keywords": ["inspire", "dream", "achieve", "believe", "possible", "journey", "light", "hope"],
                "sentence_starters": [
                    "Every step forward...",
                    "The greatest achievements...",
                    "Within you lies...",
                    "Your potential is..."
                ],
                "avoid": ["negativity", "limitations", "impossibility"]
            },
            
            QuoteStyle.MOTIVATIONAL: {
                "characteristics": [
                    "Action-oriented and direct",
                    "Creates urgency and momentum",
                    "Uses strong, decisive language",
                    "Focuses on taking action now"
                ],
                "keywords": ["action", "now", "move", "push", "drive", "achieve", "succeed", "go"],
                "sentence_starters": [
                    "The time is now to...",
                    "Success demands...",
                    "Take action and...",
                    "Push beyond..."
                ],
                "avoid": ["hesitation", "maybe", "someday", "if only"]
            },
            
            QuoteStyle.PHILOSOPHICAL: {
                "characteristics": [
                    "Deep and contemplative",
                    "Explores fundamental questions",
                    "Uses abstract concepts",
                    "Invites reflection and pondering"
                ],
                "keywords": ["truth", "existence", "meaning", "wisdom", "essence", "reality", "consciousness"],
                "sentence_starters": [
                    "The nature of...",
                    "In the realm of...",
                    "True wisdom lies in...",
                    "The paradox of..."
                ],
                "avoid": ["superficiality", "quick fixes", "simple answers"]
            },
            
            QuoteStyle.SPIRITUAL: {
                "characteristics": [
                    "Connects to higher purpose",
                    "Emphasizes inner peace and growth",
                    "Uses universal spiritual concepts",
                    "Focuses on transcendence and connection"
                ],
                "keywords": ["soul", "spirit", "divine", "peace", "harmony", "love", "unity", "transcend"],
                "sentence_starters": [
                    "The soul knows...",
                    "In stillness we find...",
                    "Divine love flows...",
                    "The spirit whispers..."
                ],
                "avoid": ["materialism", "ego", "separation"]
            },
            
            QuoteStyle.BUSINESS: {
                "characteristics": [
                    "Professional and results-focused",
                    "Emphasizes leadership and strategy",
                    "Uses business metaphors",
                    "Focuses on success and growth"
                ],
                "keywords": ["leadership", "vision", "strategy", "innovation", "excellence", "growth", "success"],
                "sentence_starters": [
                    "Great leaders understand...",
                    "Innovation requires...",
                    "Success in business...",
                    "The competitive advantage..."
                ],
                "avoid": ["personal emotions", "spiritual concepts", "non-business metaphors"]
            }
        }
    
    def _load_psychological_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Load psychological frameworks for quote generation."""
        
        return {
            "cognitive_behavioral": {
                "principles": [
                    "Thoughts influence emotions and behaviors",
                    "Focus on present moment awareness",
                    "Identify and challenge limiting beliefs",
                    "Emphasize personal agency and choice"
                ],
                "techniques": ["reframing", "mindfulness", "behavioral activation", "thought challenging"]
            },
            
            "positive_psychology": {
                "principles": [
                    "Focus on strengths and virtues",
                    "Cultivate positive emotions",
                    "Build resilience and optimism",
                    "Emphasize meaning and purpose"
                ],
                "techniques": ["gratitude", "strengths identification", "flow states", "meaning-making"]
            },
            
            "humanistic": {
                "principles": [
                    "Emphasize human potential and growth",
                    "Focus on self-actualization",
                    "Value authenticity and self-acceptance",
                    "Promote personal responsibility"
                ],
                "techniques": ["self-reflection", "values clarification", "authentic living", "personal growth"]
            },
            
            "mindfulness_based": {
                "principles": [
                    "Present moment awareness",
                    "Non-judgmental observation",
                    "Acceptance of what is",
                    "Cultivation of inner peace"
                ],
                "techniques": ["meditation", "breathing awareness", "body scanning", "mindful living"]
            }
        }
    
    async def generate_quote(
        self,
        prompt: str,
        style: Optional[QuoteStyle] = None,
        tone: Optional[QuoteTone] = None,
        length: Optional[QuoteLength] = None,
        psychology_framework: Optional[str] = None,
        target_audience: Optional[str] = None,
        context: Optional[str] = None,
        personalization: Optional[Dict[str, Any]] = None,
        advanced_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a sophisticated quote with psychology integration."""
        
        try:
            logger.info(f"Generating quote with prompt: '{prompt[:50]}...'")
            
            # Analyze the prompt for psychological insights
            prompt_analysis = await self.psychology_analyzer.analyze_request(
                prompt, context, personalization
            )
            
            # Build comprehensive generation context
            generation_context = self._build_generation_context(
                prompt=prompt,
                style=style,
                tone=tone,
                length=length,
                psychology_framework=psychology_framework,
                target_audience=target_audience,
                context=context,
                personalization=personalization,
                prompt_analysis=prompt_analysis,
                advanced_options=advanced_options or {}
            )
            
            # Generate the quote using AI orchestrator
            ai_response = await self.ai_orchestrator.generate_quote(
                prompt=generation_context["enhanced_prompt"],
                style=style.value if style else None,
                tone=tone.value if tone else None,
                length=length.value if length else None,
                context=generation_context["context_summary"],
                preferred_model=advanced_options.get("preferred_model") if advanced_options else None
            )
            
            if not ai_response.success:
                raise QuoteGenerationException(f"AI generation failed: {ai_response.error_message}")
            
            # Post-process and enhance the generated quote
            enhanced_quote = await self._enhance_generated_quote(
                ai_response.content,
                generation_context,
                ai_response
            )
            
            # Calculate quality and psychology scores
            quality_metrics = self.quote_calculator.calculate_quality_metrics(enhanced_quote["text"])
            psychology_scores = await self.psychology_analyzer.analyze_quote(
                enhanced_quote["text"],
                psychology_framework
            )
            
            # Build comprehensive result
            result = {
                "success": True,
                "quote": enhanced_quote,
                "quality_metrics": quality_metrics,
                "psychology_analysis": psychology_scores,
                "generation_metadata": {
                    "prompt": prompt,
                    "style": style.value if style else "adaptive",
                    "tone": tone.value if tone else "adaptive",
                    "length": length.value if length else "adaptive",
                    "psychology_framework": psychology_framework,
                    "ai_model": ai_response.model_used,
                    "processing_time": ai_response.processing_time,
                    "confidence": ai_response.confidence_score,
                    "generation_context": generation_context,
                    "prompt_analysis": prompt_analysis
                },
                "recommendations": self._generate_recommendations(
                    enhanced_quote, quality_metrics, psychology_scores
                )
            }
            
            logger.info("Quote generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Quote generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "quote": None,
                "generation_metadata": {
                    "prompt": prompt,
                    "error_occurred_at": datetime.utcnow().isoformat()
                }
            }
    
    def _build_generation_context(self, **kwargs) -> Dict[str, Any]:
        """Build comprehensive context for quote generation."""
        
        prompt = kwargs["prompt"]
        style = kwargs.get("style")
        tone = kwargs.get("tone")
        length = kwargs.get("length")
        psychology_framework = kwargs.get("psychology_framework")
        target_audience = kwargs.get("target_audience")
        context = kwargs.get("context")
        personalization = kwargs.get("personalization")
        prompt_analysis = kwargs.get("prompt_analysis", {})
        advanced_options = kwargs.get("advanced_options", {})
        
        # Build enhanced prompt with psychological insights
        enhanced_prompt_parts = [f"Create an inspiring quote based on: {prompt}"]
        
        # Add style guidance
        if style and style in self._style_templates:
            style_info = self._style_templates[style]
            enhanced_prompt_parts.append(
                f"Style: {style.value} - {', '.join(style_info['characteristics'])}"
            )
            
            # Add style-specific keywords
            if style_info.get("keywords"):
                enhanced_prompt_parts.append(
                    f"Consider incorporating concepts like: {', '.join(style_info['keywords'][:5])}"
                )
        
        # Add psychological framework guidance
        if psychology_framework and psychology_framework in self._psychological_frameworks:
            framework_info = self._psychological_frameworks[psychology_framework]
            enhanced_prompt_parts.append(
                f"Psychology framework: {psychology_framework} - "
                f"Apply principles: {', '.join(framework_info['principles'][:2])}"
            )
        
        # Add tone guidance
        if tone:
            tone_guidance = self._get_tone_guidance(tone)
            enhanced_prompt_parts.append(f"Tone: {tone_guidance}")
        
        # Add length guidance
        if length:
            length_guidance = self._get_length_guidance(length)
            enhanced_prompt_parts.append(f"Length: {length_guidance}")
        
        # Add target audience considerations
        if target_audience:
            enhanced_prompt_parts.append(f"Target audience: {target_audience}")
        
        # Add personalization elements
        if personalization:
            personal_elements = self._extract_personalization_elements(personalization)
            if personal_elements:
                enhanced_prompt_parts.append(f"Personal context: {personal_elements}")
        
        # Add prompt analysis insights
        if prompt_analysis.get("psychological_insights"):
            enhanced_prompt_parts.append(
                f"Psychological insight: {prompt_analysis['psychological_insights'][:200]}..."
            )
        
        # Add advanced creative constraints
        if advanced_options.get("creative_constraints"):
            enhanced_prompt_parts.append(
                f"Creative constraints: {advanced_options['creative_constraints']}"
            )
        
        # Build context summary
        context_parts = []
        if context:
            context_parts.append(f"Situation: {context}")
        
        if prompt_analysis.get("emotional_context"):
            context_parts.append(f"Emotional context: {prompt_analysis['emotional_context']}")
        
        if personalization:
            context_parts.append(f"Personal background: {json.dumps(personalization)[:100]}...")
        
        return {
            "enhanced_prompt": "\n\n".join(enhanced_prompt_parts),
            "context_summary": " | ".join(context_parts),
            "style_template": self._style_templates.get(style) if style else None,
            "psychology_framework_info": self._psychological_frameworks.get(psychology_framework) if psychology_framework else None,
            "personalization_elements": personalization,
            "advanced_options": advanced_options
        }
    
    def _get_tone_guidance(self, tone: QuoteTone) -> str:
        """Get tone-specific guidance for quote generation."""
        
        tone_guidance = {
            QuoteTone.POSITIVE: "Use uplifting, optimistic language that inspires hope",
            QuoteTone.UPLIFTING: "Create an encouraging, spirit-lifting message",
            QuoteTone.REFLECTIVE: "Invite contemplation and thoughtful consideration",
            QuoteTone.EMPOWERING: "Build confidence and sense of personal power",
            QuoteTone.CALMING: "Provide peace, serenity, and soothing comfort",
            QuoteTone.ENERGETIC: "Generate excitement, motivation, and dynamic energy",
            QuoteTone.THOUGHTFUL: "Encourage deep thinking and careful consideration",
            QuoteTone.ENCOURAGING: "Offer support, motivation, and positive reinforcement",
            QuoteTone.WISE: "Share profound wisdom and life experience",
            QuoteTone.PLAYFUL: "Include lightness, joy, and gentle humor"
        }
        
        return tone_guidance.get(tone, "Maintain an authentic and meaningful tone")
    
    def _get_length_guidance(self, length: QuoteLength) -> str:
        """Get length-specific guidance for quote generation."""
        
        length_guidance = {
            QuoteLength.SHORT: "Keep it concise and punchy (1-15 words). Every word should count.",
            QuoteLength.MEDIUM: "Create a balanced quote (16-35 words) with depth and clarity.",
            QuoteLength.LONG: "Develop a thoughtful, elaborate quote (36+ words) with rich detail."
        }
        
        return length_guidance.get(length, "Choose the natural length that best serves the message")
    
    def _extract_personalization_elements(self, personalization: Dict[str, Any]) -> str:
        """Extract and format personalization elements."""
        
        elements = []
        
        if personalization.get("age_group"):
            elements.append(f"age group: {personalization['age_group']}")
        
        if personalization.get("life_stage"):
            elements.append(f"life stage: {personalization['life_stage']}")
        
        if personalization.get("interests"):
            interests = personalization["interests"][:3]  # Limit to 3
            elements.append(f"interests: {', '.join(interests)}")
        
        if personalization.get("challenges"):
            challenges = personalization["challenges"][:2]  # Limit to 2
            elements.append(f"current challenges: {', '.join(challenges)}")
        
        if personalization.get("goals"):
            goals = personalization["goals"][:2]  # Limit to 2
            elements.append(f"goals: {', '.join(goals)}")
        
        return "; ".join(elements)
    
    async def _enhance_generated_quote(
        self,
        raw_quote: str,
        generation_context: Dict[str, Any],
        ai_response: Any
    ) -> Dict[str, Any]:
        """Enhance the generated quote with additional processing."""
        
        # Clean and format the quote
        cleaned_quote = self._clean_quote_text(raw_quote)
        
        # Extract author attribution if present
        quote_text, author = self._extract_author(cleaned_quote)
        
        # Calculate readability and impact scores
        readability_score = self.quote_calculator.calculate_readability(quote_text)
        impact_score = self.quote_calculator.calculate_impact_score(quote_text)
        
        # Identify key themes and concepts
        themes = await self._identify_themes(quote_text)
        
        # Generate alternative variations if requested
        variations = []
        if generation_context.get("advanced_options", {}).get("generate_variations"):
            variations = await self._generate_variations(quote_text, generation_context)
        
        return {
            "text": quote_text,
            "author": author,
            "word_count": len(quote_text.split()),
            "character_count": len(quote_text),
            "readability_score": readability_score,
            "impact_score": impact_score,
            "themes": themes,
            "variations": variations,
            "raw_generated_text": raw_quote,
            "processing_applied": [
                "text_cleaning",
                "author_extraction", 
                "readability_analysis",
                "impact_analysis",
                "theme_identification"
            ]
        }
    
    def _clean_quote_text(self, raw_text: str) -> str:
        """Clean and format the raw quote text."""
        
        # Remove leading/trailing whitespace
        cleaned = raw_text.strip()
        
        # Remove surrounding quotes if present
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()
        
        # Remove "Quote:" prefix if present
        if cleaned.lower().startswith("quote:"):
            cleaned = cleaned[6:].strip()
        
        # Ensure proper capitalization
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # Add period if missing and quote doesn't end with punctuation
        if cleaned and cleaned[-1] not in '.!?':
            cleaned += "."
        
        return cleaned
    
    def _extract_author(self, quote_text: str) -> Tuple[str, Optional[str]]:
        """Extract author attribution from quote text."""
        
        # Look for common attribution patterns
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+)$',  # "Quote - Author"
            r'^(.+?)\s*\(\s*(.+?)\s*\)$',  # "Quote (Author)"
            r'^(.+?)\s*by\s+(.+)$',  # "Quote by Author"
        ]
        
        import re
        
        for pattern in patterns:
            match = re.match(pattern, quote_text, re.IGNORECASE)
            if match:
                quote_part = match.group(1).strip()
                author_part = match.group(2).strip()
                
                # Validate that author part looks like a name (not part of quote)
                if len(author_part) < 50 and not author_part.lower().startswith(('the', 'a', 'an')):
                    return quote_part, author_part
        
        # No author found
        return quote_text, None
    
    async def _identify_themes(self, quote_text: str) -> List[str]:
        """Identify key themes in the quote."""
        
        try:
            # Use AI to identify themes
            theme_analysis = await self.ai_orchestrator.analyze_text(
                quote_text,
                analysis_type="themes"
            )
            
            if theme_analysis.success:
                # Extract themes from AI response
                themes = self._extract_themes_from_analysis(theme_analysis.content)
                return themes[:5]  # Limit to top 5 themes
            
        except Exception as e:
            logger.warning(f"Theme identification failed: {str(e)}")
        
        # Fallback to keyword-based theme identification
        return self._identify_themes_by_keywords(quote_text)
    
    def _extract_themes_from_analysis(self, analysis_text: str) -> List[str]:
        """Extract themes from AI analysis text."""
        
        # Simple extraction - in production, use more sophisticated NLP
        themes = []
        
        # Look for common theme indicators
        theme_keywords = [
            "love", "success", "happiness", "wisdom", "growth", "courage",
            "perseverance", "hope", "peace", "strength", "leadership",
            "creativity", "change", "opportunity", "resilience", "faith",
            "friendship", "family", "dreams", "goals", "motivation"
        ]
        
        analysis_lower = analysis_text.lower()
        
        for keyword in theme_keywords:
            if keyword in analysis_lower:
                themes.append(keyword.title())
        
        return list(set(themes))  # Remove duplicates
    
    def _identify_themes_by_keywords(self, quote_text: str) -> List[str]:
        """Identify themes using keyword matching."""
        
        quote_lower = quote_text.lower()
        themes = []
        
        theme_mappings = {
            "success": ["success", "achieve", "accomplish", "win", "triumph"],
            "love": ["love", "heart", "care", "affection", "romance"],
            "wisdom": ["wisdom", "knowledge", "learn", "understand", "insight"],
            "courage": ["courage", "brave", "bold", "fearless", "daring"],
            "hope": ["hope", "optimism", "faith", "believe", "trust"],
            "growth": ["grow", "develop", "progress", "evolve", "improve"],
            "happiness": ["happy", "joy", "delight", "pleasure", "cheerful"],
            "peace": ["peace", "calm", "serenity", "tranquil", "quiet"]
        }
        
        for theme, keywords in theme_mappings.items():
            if any(keyword in quote_lower for keyword in keywords):
                themes.append(theme.title())
        
        return themes
    
    async def _generate_variations(
        self,
        quote_text: str,
        generation_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate alternative variations of the quote."""
        
        variations = []
        
        try:
            # Generate variations with different approaches
            variation_prompts = [
                f"Rephrase this quote while keeping the same meaning: {quote_text}",
                f"Create a shorter version of this quote: {quote_text}",
                f"Create a more poetic version of this quote: {quote_text}"
            ]
            
            for i, prompt in enumerate(variation_prompts):
                variation_response = await self.ai_orchestrator.generate_text(
                    prompt=prompt,
                    max_tokens=100,
                    temperature=0.8
                )
                
                if variation_response.success:
                    variations.append({
                        "text": self._clean_quote_text(variation_response.content),
                        "type": ["rephrased", "shortened", "poetic"][i],
                        "confidence": variation_response.confidence_score
                    })
                    
        except Exception as e:
            logger.warning(f"Variation generation failed: {str(e)}")
        
        return variations
    
    def _generate_recommendations(
        self,
        enhanced_quote: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        psychology_scores: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for quote improvement or usage."""
        
        recommendations = []
        
        # Quality-based recommendations
        if quality_metrics.get("readability_score", 0) < 0.6:
            recommendations.append("Consider simplifying language for better readability")
        
        if quality_metrics.get("impact_score", 0) < 0.7:
            recommendations.append("Could benefit from stronger emotional language")
        
        # Length-based recommendations
        word_count = enhanced_quote.get("word_count", 0)
        if word_count > 50:
            recommendations.append("Consider creating a shorter version for social media")
        elif word_count < 5:
            recommendations.append("Quote might benefit from additional context or depth")
        
        # Psychology-based recommendations
        if psychology_scores.get("emotional_resonance", 0) < 0.6:
            recommendations.append("Could enhance emotional connection with audience")
        
        if psychology_scores.get("wisdom_depth", 0) > 0.8:
            recommendations.append("Excellent depth - suitable for philosophical audiences")
        
        # Usage recommendations
        themes = enhanced_quote.get("themes", [])
        if "success" in [t.lower() for t in themes]:
            recommendations.append("Perfect for business and professional contexts")
        
        if "love" in [t.lower() for t in themes]:
            recommendations.append("Great for personal relationships and emotional content")
        
        return recommendations
    
    def get_available_styles(self) -> List[Dict[str, Any]]:
        """Get available quote styles with descriptions."""
        
        return [
            {
                "value": style.value,
                "name": style.value.replace("_", " ").title(),
                "description": template["characteristics"][0] if template.get("characteristics") else "",
                "keywords": template.get("keywords", [])[:5]
            }
            for style, template in self._style_templates.items()
        ]
    
    def get_psychological_frameworks(self) -> List[Dict[str, Any]]:
        """Get available psychological frameworks."""
        
        return [
            {
                "name": name,
                "description": framework["principles"][0] if framework.get("principles") else "",
                "techniques": framework.get("techniques", [])
            }
            for name, framework in self._psychological_frameworks.items()
        ]


# Global engine instance
_engine = None


def get_quote_engine() -> QuoteEngine:
    """Get the global quote engine instance."""
    global _engine
    if _engine is None:
        _engine = QuoteEngine()
    return _engine