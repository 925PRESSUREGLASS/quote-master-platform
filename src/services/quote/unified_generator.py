"""
Enhanced Quote Generator Service
Combines AI services for both inspirational quotes and service quote generation
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from src.services.ai.openai_service import OpenAIService
from src.services.ai.claude import ClaudeService
from src.services.ai.orchestrator import AIOrchestrator
from src.services.quote.engine import QuoteEngine
from src.services.quote.service_quote import ServiceQuoteService
from src.core.config import get_settings
from src.core.exceptions import QuoteGenerationException

logger = logging.getLogger(__name__)
settings = get_settings()


class UnifiedQuoteGenerator:
    """
    Unified quote generator that handles both inspirational quotes 
    and service quotes with AI assistance
    """
    
    def __init__(self):
        self.openai = OpenAIService()
        self.claude = ClaudeService()
        self.orchestrator = AIOrchestrator()
        self.quote_engine = QuoteEngine()
        self.service_quote_service = ServiceQuoteService()
        
    async def generate_inspirational_quote(
        self,
        prompt: str,
        style: Optional[str] = None,
        category: Optional[str] = None,
        length: str = "medium",
        model_preference: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate an inspirational quote using AI services
        """
        try:
            # Determine the best AI service to use
            if model_preference == "auto":
                service = await self._select_best_service(prompt, "inspirational")
            elif model_preference == "openai":
                service = self.openai
            elif model_preference == "claude":
                service = self.claude
            else:
                service = self.orchestrator
                
            # Generate the quote
            result = await service.generate_quote({
                "prompt": prompt,
                "style": style,
                "category": category,
                "length": length,
                "type": "inspirational"
            })
            
            return {
                "content": result.get("content", ""),
                "author": result.get("author"),
                "category": category,
                "style": style,
                "confidence": result.get("confidence", 0.8),
                "model_used": result.get("model_used", "unknown"),
                "generation_time": result.get("generation_time", 0),
                "metadata": {
                    "prompt": prompt,
                    "length": length,
                    "generated_at": datetime.utcnow().isoformat(),
                    "service_used": service.__class__.__name__
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate inspirational quote: {str(e)}")
            raise QuoteGenerationException(f"Quote generation failed: {str(e)}")
    
    async def generate_service_quote_from_voice(
        self,
        transcription: str,
        audio_metadata: Dict[str, Any],
        fallback_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a service quote from voice transcription using AI
        """
        try:
            # Use AI to extract service quote parameters from transcription
            extraction_result = await self.orchestrator.extract_service_quote_data({
                "transcription": transcription,
                "audio_metadata": audio_metadata,
                "fallback_data": fallback_data
            })
            
            if not extraction_result.get("success"):
                raise QuoteGenerationException("Failed to extract quote data from voice")
            
            # Generate the service quote using extracted data
            quote_data = extraction_result.get("quote_data", {})
            service_quote = await self.service_quote_service.calculate_quote(quote_data)
            
            return {
                "service_quote": service_quote,
                "extraction_confidence": extraction_result.get("confidence", 0.0),
                "extracted_data": quote_data,
                "transcription": transcription,
                "ai_analysis": extraction_result.get("analysis", {}),
                "recommendations": extraction_result.get("recommendations", []),
                "metadata": {
                    "voice_processed": True,
                    "audio_duration": audio_metadata.get("duration", 0),
                    "audio_quality": audio_metadata.get("quality", "unknown"),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate service quote from voice: {str(e)}")
            raise QuoteGenerationException(f"Voice quote generation failed: {str(e)}")
    
    async def enhance_service_quote(
        self,
        quote_data: Dict[str, Any],
        enhancement_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Enhance an existing service quote with AI-generated insights
        """
        try:
            enhancement_prompt = self._build_enhancement_prompt(quote_data, enhancement_type)
            
            # Use Claude for detailed analysis and recommendations
            enhancement_result = await self.claude.analyze_and_enhance({
                "quote_data": quote_data,
                "prompt": enhancement_prompt,
                "enhancement_type": enhancement_type
            })
            
            return {
                "original_quote": quote_data,
                "enhanced_recommendations": enhancement_result.get("recommendations", []),
                "risk_analysis": enhancement_result.get("risk_analysis", {}),
                "pricing_insights": enhancement_result.get("pricing_insights", {}),
                "customer_communication": enhancement_result.get("customer_communication", {}),
                "competitive_analysis": enhancement_result.get("competitive_analysis", {}),
                "enhancement_confidence": enhancement_result.get("confidence", 0.8),
                "metadata": {
                    "enhancement_type": enhancement_type,
                    "enhanced_at": datetime.utcnow().isoformat(),
                    "ai_model": enhancement_result.get("model_used", "claude")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance service quote: {str(e)}")
            raise QuoteGenerationException(f"Quote enhancement failed: {str(e)}")
    
    async def generate_quote_follow_up(
        self,
        quote_data: Dict[str, Any],
        customer_response: Optional[str] = None,
        follow_up_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate personalized follow-up communication for service quotes
        """
        try:
            follow_up_prompt = self._build_follow_up_prompt(
                quote_data, customer_response, follow_up_type
            )
            
            # Use OpenAI for natural language generation
            follow_up_result = await self.openai.generate_communication({
                "prompt": follow_up_prompt,
                "tone": "professional",
                "format": "email",
                "personalization_data": quote_data
            })
            
            return {
                "email_subject": follow_up_result.get("subject", ""),
                "email_body": follow_up_result.get("body", ""),
                "sms_message": follow_up_result.get("sms", ""),
                "call_script": follow_up_result.get("call_script", ""),
                "follow_up_type": follow_up_type,
                "personalization_notes": follow_up_result.get("personalization", []),
                "metadata": {
                    "generated_for": quote_data.get("customer_name", "Unknown"),
                    "quote_id": quote_data.get("id"),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate quote follow-up: {str(e)}")
            raise QuoteGenerationException(f"Follow-up generation failed: {str(e)}")
    
    async def _select_best_service(self, prompt: str, quote_type: str) -> Any:
        """
        Intelligently select the best AI service based on prompt and type
        """
        # Simple logic - can be enhanced with ML model
        prompt_length = len(prompt)
        
        if quote_type == "inspirational":
            if prompt_length < 50:
                return self.openai  # Fast for short prompts
            else:
                return self.claude  # Better for complex prompts
        elif quote_type == "service":
            return self.orchestrator  # Best for structured data extraction
        
        return self.openai  # Default fallback
    
    def _build_enhancement_prompt(self, quote_data: Dict[str, Any], enhancement_type: str) -> str:
        """Build prompt for quote enhancement"""
        customer_name = quote_data.get('customer_name', 'N/A')
        service_type = quote_data.get('service_type', 'N/A')
        property_type = quote_data.get('property_type', 'N/A')
        square_meters = quote_data.get('square_meters', 'N/A')
        suburb = quote_data.get('suburb', 'N/A')
        total_price = quote_data.get('total_price', 0)
        
        base_prompt = f"""
        Analyze the following service quote and provide comprehensive insights:
        
        Quote Details:
        - Customer: {customer_name}
        - Service: {service_type}
        - Property: {property_type}
        - Area: {square_meters} sqm
        - Suburb: {suburb}
        - Total Price: ${total_price:.2f}
        
        Please provide:
        1. Risk analysis and mitigation strategies
        2. Pricing optimization recommendations
        3. Customer communication suggestions
        4. Competitive positioning insights
        5. Upselling opportunities
        """
        
        return base_prompt
    
    def _build_follow_up_prompt(
        self, 
        quote_data: Dict[str, Any], 
        customer_response: Optional[str],
        follow_up_type: str
    ) -> str:
        """Build prompt for follow-up communication"""
        service_type = quote_data.get('service_type', '')
        customer_name = quote_data.get('customer_name', '')
        total_price = quote_data.get('total_price', 0)
        suburb = quote_data.get('suburb', '')
        property_type = quote_data.get('property_type', '')
        
        base_prompt = f"""
        Generate a professional follow-up communication for this service quote:
        
        Quote: {service_type} for {customer_name}
        Price: ${total_price:.2f}
        Property: {suburb}, {property_type}
        
        Follow-up type: {follow_up_type}
        Customer previous response: {customer_response or 'No prior response'}
        
        Generate appropriate email, SMS, and call script content.
        """
        
        return base_prompt


# Create singleton instance
quote_generator = UnifiedQuoteGenerator()
