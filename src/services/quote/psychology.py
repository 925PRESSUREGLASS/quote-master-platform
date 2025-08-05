"""Psychology analysis service for Quote Master Pro."""

import logging
from typing import Dict, Any, Optional, List, Tuple
import re
from enum import Enum

from src.services.ai.orchestrator import get_ai_orchestrator
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PsychologicalFramework(str, Enum):
    """Psychological frameworks for analysis."""
    COGNITIVE_BEHAVIORAL = "cognitive_behavioral"
    POSITIVE_PSYCHOLOGY = "positive_psychology"
    HUMANISTIC = "humanistic"
    MINDFULNESS_BASED = "mindfulness_based"
    PSYCHODYNAMIC = "psychodynamic"
    EXISTENTIAL = "existential"
    BEHAVIORAL = "behavioral"
    SOLUTION_FOCUSED = "solution_focused"


class PersonalityType(str, Enum):
    """Personality types for targeted quote generation."""
    INTROVERT = "introvert"
    EXTROVERT = "extrovert"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PRACTICAL = "practical"
    EMOTIONAL = "emotional"
    LOGICAL = "logical"
    INTUITIVE = "intuitive"


class PsychologyAnalyzer:
    """Analyze psychological aspects of quotes and user requests."""
    
    def __init__(self):
        self.ai_orchestrator = get_ai_orchestrator()
        self.psychological_indicators = self._load_psychological_indicators()
        self.cognitive_patterns = self._load_cognitive_patterns()
        self.emotional_triggers = self._load_emotional_triggers()
    
    def _load_psychological_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Load psychological indicators for different frameworks."""
        
        return {
            PsychologicalFramework.COGNITIVE_BEHAVIORAL: {
                "thought_patterns": ["think", "believe", "assume", "expect", "worry", "fear"],
                "behavioral_indicators": ["do", "act", "behave", "react", "respond", "choose"],
                "cognitive_distortions": ["always", "never", "must", "should", "catastrophe", "failure"],
                "positive_restructuring": ["can", "able", "possible", "learn", "grow", "change"]
            },
            
            PsychologicalFramework.POSITIVE_PSYCHOLOGY: {
                "strengths_focus": ["strength", "talent", "gift", "ability", "skill", "excellence"],
                "positive_emotions": ["joy", "gratitude", "love", "hope", "serenity", "pride"],
                "engagement_flow": ["focus", "immerse", "absorb", "engage", "flow", "passionate"],
                "meaning_purpose": ["purpose", "meaning", "values", "mission", "calling", "contribution"]
            },
            
            PsychologicalFramework.HUMANISTIC: {
                "self_actualization": ["potential", "authentic", "genuine", "true", "real", "self"],
                "personal_growth": ["grow", "develop", "evolve", "expand", "transform", "become"],
                "self_acceptance": ["accept", "embrace", "honor", "respect", "appreciate", "value"],
                "autonomy": ["choose", "decide", "control", "freedom", "independence", "self-directed"]
            },
            
            PsychologicalFramework.MINDFULNESS_BASED: {
                "present_moment": ["now", "present", "here", "moment", "awareness", "conscious"],
                "acceptance": ["accept", "allow", "let", "surrender", "release", "flow"],
                "non_judgment": ["observe", "notice", "witness", "aware", "mindful", "present"],
                "inner_peace": ["peace", "calm", "still", "quiet", "serene", "tranquil"]
            },
            
            PsychologicalFramework.EXISTENTIAL: {
                "meaning_making": ["meaning", "purpose", "existence", "being", "essence", "truth"],
                "freedom_responsibility": ["freedom", "choice", "responsibility", "create", "author", "decide"],
                "authenticity": ["authentic", "genuine", "true", "real", "honest", "sincere"],
                "mortality_awareness": ["life", "death", "time", "finite", "precious", "moment"]
            }
        }
    
    def _load_cognitive_patterns(self) -> Dict[str, List[str]]:
        """Load cognitive patterns and thinking styles."""
        
        return {
            "optimistic": ["hope", "possible", "opportunity", "bright", "positive", "achieve"],
            "pessimistic": ["worry", "fear", "doubt", "impossible", "problem", "failure"],
            "growth_mindset": ["learn", "grow", "develop", "improve", "challenge", "effort"],
            "fixed_mindset": ["talent", "natural", "born", "gifted", "stuck", "limited"],
            "solution_focused": ["solution", "answer", "way", "path", "resolve", "fix"],
            "problem_focused": ["problem", "issue", "difficulty", "challenge", "obstacle", "barrier"],
            "internal_locus": ["I", "me", "my", "control", "choose", "decide", "create"],
            "external_locus": ["they", "them", "luck", "fate", "circumstances", "others"]
        }
    
    def _load_emotional_triggers(self) -> Dict[str, Dict[str, List[str]]]:
        """Load emotional triggers for different personality types."""
        
        return {
            PersonalityType.INTROVERT: {
                "motivators": ["quiet", "solitude", "depth", "reflection", "inner", "personal"],
                "stressors": ["crowd", "noise", "pressure", "spotlight", "overwhelming", "chaotic"]
            },
            
            PersonalityType.EXTROVERT: {
                "motivators": ["people", "social", "energy", "interaction", "excitement", "dynamic"],
                "stressors": ["isolation", "quiet", "alone", "boring", "static", "withdrawn"]
            },
            
            PersonalityType.ANALYTICAL: {
                "motivators": ["logic", "reason", "data", "analysis", "facts", "evidence"],
                "stressors": ["emotion", "feelings", "intuition", "chaos", "unclear", "ambiguous"]
            },
            
            PersonalityType.CREATIVE: {
                "motivators": ["create", "imagine", "innovate", "artistic", "unique", "original"],
                "stressors": ["routine", "rigid", "conventional", "boring", "systematic", "predictable"]
            },
            
            PersonalityType.PRACTICAL: {
                "motivators": ["practical", "useful", "efficient", "results", "action", "concrete"],
                "stressors": ["theoretical", "abstract", "impractical", "idealistic", "vague", "conceptual"]
            }
        }
    
    async def analyze_request(
        self,
        prompt: str,
        context: Optional[str] = None,
        personalization: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a user's quote request for psychological insights."""
        
        try:
            logger.info("Analyzing user request for psychological insights")
            
            # Combine all text for analysis
            full_text = prompt
            if context:
                full_text += f" {context}"
            
            # Basic psychological pattern detection
            cognitive_patterns = self._detect_cognitive_patterns(full_text)
            emotional_state = self._analyze_emotional_state(full_text)
            personality_indicators = self._detect_personality_indicators(full_text)
            psychological_needs = self._identify_psychological_needs(full_text)
            
            # Advanced AI-powered analysis
            ai_analysis = await self._get_ai_psychological_analysis(full_text)
            
            # Incorporate personalization data
            personal_insights = self._analyze_personalization(personalization) if personalization else {}
            
            # Generate recommendations
            framework_recommendations = self._recommend_frameworks(
                cognitive_patterns, emotional_state, personality_indicators
            )
            
            return {
                "prompt": prompt,
                "cognitive_patterns": cognitive_patterns,
                "emotional_state": emotional_state,
                "personality_indicators": personality_indicators,
                "psychological_needs": psychological_needs,
                "ai_insights": ai_analysis,
                "personal_insights": personal_insights,
                "recommended_frameworks": framework_recommendations,
                "psychological_insights": self._synthesize_insights(
                    cognitive_patterns, emotional_state, psychological_needs, ai_analysis
                ),
                "emotional_context": self._build_emotional_context(emotional_state, personal_insights)
            }
            
        except Exception as e:
            logger.error(f"Request analysis failed: {str(e)}")
            return {
                "prompt": prompt,
                "error": str(e),
                "fallback_analysis": self._fallback_analysis(prompt)
            }
    
    async def analyze_quote(
        self,
        quote_text: str,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a quote for psychological impact and alignment."""
        
        try:
            logger.info("Analyzing quote for psychological impact")
            
            # Framework-specific analysis
            framework_analysis = {}
            if framework and framework in self.psychological_indicators:
                framework_analysis = self._analyze_framework_alignment(quote_text, framework)
            
            # Universal psychological factors
            wisdom_depth = self._assess_wisdom_depth(quote_text)
            emotional_resonance = self._assess_emotional_resonance(quote_text)
            cognitive_impact = self._assess_cognitive_impact(quote_text)
            behavioral_motivation = self._assess_behavioral_motivation(quote_text)
            
            # Therapeutic potential
            therapeutic_value = self._assess_therapeutic_value(quote_text)
            
            # AI-powered deep analysis
            ai_psychological_analysis = await self._get_ai_quote_analysis(quote_text, framework)
            
            # Target audience identification
            target_personality_types = self._identify_target_personalities(quote_text)
            
            return {
                "quote_text": quote_text,
                "framework_analysis": framework_analysis,
                "wisdom_depth": wisdom_depth,
                "emotional_resonance": emotional_resonance,
                "cognitive_impact": cognitive_impact,
                "behavioral_motivation": behavioral_motivation,
                "therapeutic_value": therapeutic_value,
                "ai_analysis": ai_psychological_analysis,
                "target_personalities": target_personality_types,
                "overall_psychological_score": self._calculate_overall_psychological_score(
                    wisdom_depth, emotional_resonance, cognitive_impact, behavioral_motivation
                ),
                "psychological_recommendations": self._generate_psychological_recommendations(
                    quote_text, framework_analysis, wisdom_depth, emotional_resonance
                )
            }
            
        except Exception as e:
            logger.error(f"Quote analysis failed: {str(e)}")
            return {
                "quote_text": quote_text,
                "error": str(e),
                "basic_analysis": self._basic_psychological_analysis(quote_text)
            }
    
    def _detect_cognitive_patterns(self, text: str) -> Dict[str, float]:
        """Detect cognitive thinking patterns in text."""
        
        text_lower = text.lower()
        pattern_scores = {}
        
        for pattern_name, keywords in self.cognitive_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            pattern_scores[pattern_name] = min(1.0, matches / max(len(keywords), 1))
        
        return pattern_scores
    
    def _analyze_emotional_state(self, text: str) -> Dict[str, Any]:
        """Analyze emotional state indicators in text."""
        
        # Emotional intensity markers
        intensity_markers = {
            "high": ["very", "extremely", "incredibly", "absolutely", "completely"],
            "medium": ["quite", "fairly", "somewhat", "rather", "pretty"],
            "low": ["slightly", "a bit", "maybe", "perhaps", "might"]
        }
        
        # Emotional valence
        positive_emotions = ["happy", "joy", "excited", "grateful", "peaceful", "confident"]
        negative_emotions = ["sad", "angry", "worried", "frustrated", "anxious", "depressed"]
        
        text_lower = text.lower()
        
        # Calculate intensity
        intensity_score = 0.0
        for level, markers in intensity_markers.items():
            count = sum(1 for marker in markers if marker in text_lower)
            if level == "high":
                intensity_score += count * 1.0
            elif level == "medium":
                intensity_score += count * 0.6
            else:
                intensity_score += count * 0.3
        
        # Calculate valence
        positive_count = sum(1 for emotion in positive_emotions if emotion in text_lower)
        negative_count = sum(1 for emotion in negative_emotions if emotion in text_lower)
        
        valence = "neutral"
        if positive_count > negative_count:
            valence = "positive"
        elif negative_count > positive_count:
            valence = "negative"
        
        return {
            "intensity": min(1.0, intensity_score / 10),
            "valence": valence,
            "positive_emotion_count": positive_count,
            "negative_emotion_count": negative_count,
            "emotional_complexity": min(1.0, (positive_count + negative_count) / 10)
        }
    
    def _detect_personality_indicators(self, text: str) -> Dict[str, float]:
        """Detect personality type indicators in text."""
        
        text_lower = text.lower()
        personality_scores = {}
        
        for personality_type in PersonalityType:
            if personality_type.value in self.emotional_triggers:
                motivators = self.emotional_triggers[personality_type.value]["motivators"]
                matches = sum(1 for keyword in motivators if keyword in text_lower)
                personality_scores[personality_type.value] = min(1.0, matches / max(len(motivators), 1))
        
        return personality_scores
    
    def _identify_psychological_needs(self, text: str) -> List[str]:
        """Identify psychological needs expressed in the text."""
        
        need_indicators = {
            "autonomy": ["control", "choice", "freedom", "independent", "decide"],
            "competence": ["succeed", "achieve", "master", "excel", "accomplish"],
            "relatedness": ["connect", "belong", "love", "friendship", "relationship"],
            "security": ["safe", "secure", "stable", "protected", "certain"],
            "meaning": ["purpose", "meaning", "significant", "important", "matter"],
            "growth": ["grow", "develop", "learn", "improve", "evolve"],
            "recognition": ["appreciate", "recognize", "acknowledge", "praise", "valued"]
        }
        
        text_lower = text.lower()
        identified_needs = []
        
        for need, indicators in need_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                identified_needs.append(need)
        
        return identified_needs
    
    async def _get_ai_psychological_analysis(self, text: str) -> Dict[str, Any]:
        """Get AI-powered psychological analysis."""
        
        try:
            analysis_prompt = f"""
            Analyze the following text from a psychological perspective:
            
            "{text}"
            
            Please provide insights on:
            1. Underlying emotional needs
            2. Cognitive patterns or thinking styles
            3. Potential psychological themes
            4. Personality indicators
            5. Motivational factors
            
            Format your response as a brief, insightful analysis.
            """
            
            response = await self.ai_orchestrator.analyze_text(
                text,
                analysis_type="psychology"
            )
            
            if response.success:
                return {
                    "analysis": response.content,
                    "confidence": response.confidence_score,
                    "model_used": response.model_used
                }
            else:
                return {"error": response.error_message}
                
        except Exception as e:
            logger.error(f"AI psychological analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_personalization(self, personalization: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze personalization data for psychological insights."""
        
        insights = {}
        
        # Age-related psychological considerations
        if "age_group" in personalization:
            age_group = personalization["age_group"]
            insights["age_considerations"] = self._get_age_psychological_factors(age_group)
        
        # Life stage considerations
        if "life_stage" in personalization:
            life_stage = personalization["life_stage"]
            insights["life_stage_needs"] = self._get_life_stage_needs(life_stage)
        
        # Interest-based personality inference
        if "interests" in personalization:
            interests = personalization["interests"]
            insights["personality_inference"] = self._infer_personality_from_interests(interests)
        
        # Challenge-based psychological state
        if "challenges" in personalization:
            challenges = personalization["challenges"]
            insights["psychological_state"] = self._assess_challenges_impact(challenges)
        
        return insights
    
    def _recommend_frameworks(
        self,
        cognitive_patterns: Dict[str, float],
        emotional_state: Dict[str, Any],
        personality_indicators: Dict[str, float]
    ) -> List[str]:
        """Recommend psychological frameworks based on analysis."""
        
        recommendations = []
        
        # Cognitive-behavioral for thinking pattern issues
        if cognitive_patterns.get("pessimistic", 0) > 0.5 or cognitive_patterns.get("problem_focused", 0) > 0.5:
            recommendations.append(PsychologicalFramework.COGNITIVE_BEHAVIORAL.value)
        
        # Positive psychology for growth-oriented individuals
        if cognitive_patterns.get("growth_mindset", 0) > 0.5 or cognitive_patterns.get("optimistic", 0) > 0.5:
            recommendations.append(PsychologicalFramework.POSITIVE_PSYCHOLOGY.value)
        
        # Mindfulness for high stress/anxiety
        if emotional_state.get("intensity", 0) > 0.7 and emotional_state.get("valence") == "negative":
            recommendations.append(PsychologicalFramework.MINDFULNESS_BASED.value)
        
        # Humanistic for self-actualization needs
        if personality_indicators.get("creative", 0) > 0.5 or personality_indicators.get("intuitive", 0) > 0.5:
            recommendations.append(PsychologicalFramework.HUMANISTIC.value)
        
        return recommendations[:3]  # Limit to top 3
    
    def _synthesize_insights(
        self,
        cognitive_patterns: Dict[str, float],
        emotional_state: Dict[str, Any],
        psychological_needs: List[str],
        ai_analysis: Dict[str, Any]
    ) -> str:
        """Synthesize all insights into a coherent summary."""
        
        insights = []
        
        # Cognitive insights
        dominant_pattern = max(cognitive_patterns.items(), key=lambda x: x[1]) if cognitive_patterns else None
        if dominant_pattern and dominant_pattern[1] > 0.3:
            insights.append(f"Shows {dominant_pattern[0].replace('_', ' ')} thinking patterns")
        
        # Emotional insights
        if emotional_state.get("intensity", 0) > 0.6:
            insights.append(f"High emotional intensity with {emotional_state.get('valence', 'neutral')} valence")
        
        # Needs insights
        if psychological_needs:
            primary_needs = psychological_needs[:2]
            insights.append(f"Primary psychological needs: {', '.join(primary_needs)}")
        
        # AI insights
        if ai_analysis.get("analysis"):
            insights.append("AI analysis suggests complex psychological themes")
        
        return "; ".join(insights) if insights else "Basic psychological patterns detected"
    
    def _build_emotional_context(
        self,
        emotional_state: Dict[str, Any],
        personal_insights: Dict[str, Any]
    ) -> str:
        """Build emotional context for quote generation."""
        
        context_parts = []
        
        # Emotional state
        valence = emotional_state.get("valence", "neutral")
        intensity = emotional_state.get("intensity", 0)
        
        if intensity > 0.6:
            context_parts.append(f"High {valence} emotional state")
        elif intensity > 0.3:
            context_parts.append(f"Moderate {valence} emotional tone")
        
        # Personal context
        if personal_insights.get("life_stage_needs"):
            context_parts.append(f"Life stage: {personal_insights['life_stage_needs']}")
        
        return "; ".join(context_parts) if context_parts else "Balanced emotional context"
    
    def _analyze_framework_alignment(self, quote_text: str, framework: str) -> Dict[str, Any]:
        """Analyze how well a quote aligns with a psychological framework."""
        
        if framework not in self.psychological_indicators:
            return {"error": f"Unknown framework: {framework}"}
        
        framework_data = self.psychological_indicators[framework]
        text_lower = quote_text.lower()
        
        alignment_scores = {}
        total_alignment = 0.0
        
        for category, keywords in framework_data.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            score = min(1.0, matches / max(len(keywords), 1))
            alignment_scores[category] = score
            total_alignment += score
        
        overall_alignment = total_alignment / len(framework_data) if framework_data else 0.0
        
        return {
            "framework": framework,
            "category_scores": alignment_scores,
            "overall_alignment": overall_alignment,
            "strength_areas": [cat for cat, score in alignment_scores.items() if score > 0.6],
            "alignment_level": "high" if overall_alignment > 0.7 else ("medium" if overall_alignment > 0.4 else "low")
        }
    
    def _assess_wisdom_depth(self, quote_text: str) -> float:
        """Assess the wisdom depth of a quote."""
        
        wisdom_indicators = [
            "truth", "wisdom", "understanding", "insight", "knowledge",
            "experience", "learn", "grow", "discover", "realize",
            "life", "time", "change", "journey", "path"
        ]
        
        text_lower = quote_text.lower()
        wisdom_count = sum(1 for indicator in wisdom_indicators if indicator in text_lower)
        
        # Additional depth factors
        abstract_concepts = ["essence", "nature", "reality", "existence", "being"]
        abstract_count = sum(1 for concept in abstract_concepts if concept in text_lower)
        
        # Philosophical structure indicators
        philosophical_structures = ["is not", "but rather", "true", "real", "meaning"]
        structure_count = sum(1 for structure in philosophical_structures if structure in text_lower)
        
        depth_score = (wisdom_count * 0.4 + abstract_count * 0.3 + structure_count * 0.3) / 10
        
        return min(1.0, depth_score)
    
    def _assess_emotional_resonance(self, quote_text: str) -> float:
        """Assess emotional resonance potential."""
        
        high_resonance_emotions = [
            "love", "hope", "courage", "strength", "peace", "joy",
            "freedom", "dreams", "passion", "heart", "soul", "spirit"
        ]
        
        universal_experiences = [
            "pain", "loss", "fear", "struggle", "challenge", "growth",
            "change", "journey", "life", "death", "time", "memory"
        ]
        
        text_lower = quote_text.lower()
        
        emotion_count = sum(1 for emotion in high_resonance_emotions if emotion in text_lower)
        experience_count = sum(1 for exp in universal_experiences if exp in text_lower)
        
        # Personal relevance indicators
        personal_pronouns = len(re.findall(r'\b(you|your|we|us|our)\b', text_lower))
        
        resonance_score = (emotion_count * 0.4 + experience_count * 0.4 + personal_pronouns * 0.2) / 10
        
        return min(1.0, resonance_score)
    
    def _assess_cognitive_impact(self, quote_text: str) -> float:
        """Assess cognitive impact and thought-provoking nature."""
        
        cognitive_triggers = [
            "think", "consider", "imagine", "believe", "understand",
            "realize", "discover", "question", "wonder", "reflect"
        ]
        
        perspective_shifters = [
            "not", "but", "however", "instead", "rather", "actually",
            "truly", "really", "perhaps", "maybe", "what if"
        ]
        
        text_lower = quote_text.lower()
        
        cognitive_count = sum(1 for trigger in cognitive_triggers if trigger in text_lower)
        perspective_count = sum(1 for shifter in perspective_shifters if shifter in text_lower)
        
        # Question marks increase cognitive engagement
        question_bonus = quote_text.count('?') * 0.2
        
        impact_score = (cognitive_count * 0.5 + perspective_count * 0.3 + question_bonus) / 10
        
        return min(1.0, impact_score)
    
    def _assess_behavioral_motivation(self, quote_text: str) -> float:
        """Assess potential to motivate behavioral change."""
        
        action_words = [
            "do", "act", "make", "create", "build", "start", "begin",
            "take", "move", "go", "try", "attempt", "pursue", "achieve"
        ]
        
        empowerment_words = [
            "can", "will", "able", "capable", "possible", "choose",
            "decide", "control", "power", "strength", "courage"
        ]
        
        text_lower = quote_text.lower()
        
        action_count = sum(1 for word in action_words if word in text_lower)
        empowerment_count = sum(1 for word in empowerment_words if word in text_lower)
        
        # Imperative mood increases motivation
        imperative_indicators = quote_text.count('!') + (1 if quote_text.strip().split()[0].lower() in action_words else 0)
        
        motivation_score = (action_count * 0.4 + empowerment_count * 0.4 + imperative_indicators * 0.2) / 10
        
        return min(1.0, motivation_score)
    
    def _assess_therapeutic_value(self, quote_text: str) -> Dict[str, float]:
        """Assess therapeutic value across different dimensions."""
        
        therapeutic_dimensions = {
            "healing": ["heal", "mend", "restore", "recover", "peace", "comfort"],
            "growth": ["grow", "develop", "evolve", "transform", "become", "change"],
            "resilience": ["strong", "resilient", "overcome", "endure", "survive", "persist"],
            "acceptance": ["accept", "embrace", "allow", "forgive", "let go", "release"],
            "hope": ["hope", "faith", "trust", "believe", "possible", "tomorrow"]
        }
        
        text_lower = quote_text.lower()
        therapeutic_scores = {}
        
        for dimension, keywords in therapeutic_dimensions.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            therapeutic_scores[dimension] = min(1.0, matches / max(len(keywords), 1))
        
        return therapeutic_scores
    
    async def _get_ai_quote_analysis(self, quote_text: str, framework: Optional[str]) -> Dict[str, Any]:
        """Get AI analysis of quote's psychological impact."""
        
        try:
            framework_context = f" using {framework} principles" if framework else ""
            
            analysis_prompt = f"""
            Analyze this quote for psychological impact{framework_context}:
            
            "{quote_text}"
            
            Assess:
            1. Psychological mechanisms at work
            2. Potential therapeutic value
            3. Target audience psychological profile
            4. Emotional and cognitive effects
            5. Behavioral influence potential
            """
            
            response = await self.ai_orchestrator.analyze_text(
                analysis_prompt,
                analysis_type="psychology"
            )
            
            if response.success:
                return {
                    "analysis": response.content,
                    "confidence": response.confidence_score,
                    "model_used": response.model_used
                }
            else:
                return {"error": response.error_message}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _identify_target_personalities(self, quote_text: str) -> List[str]:
        """Identify target personality types for the quote."""
        
        text_lower = quote_text.lower()
        target_types = []
        
        for personality_type in PersonalityType:
            if personality_type.value in self.emotional_triggers:
                motivators = self.emotional_triggers[personality_type.value]["motivators"]
                matches = sum(1 for keyword in motivators if keyword in text_lower)
                
                if matches >= 2:  # Threshold for targeting
                    target_types.append(personality_type.value)
        
        return target_types
    
    def _calculate_overall_psychological_score(
        self,
        wisdom_depth: float,
        emotional_resonance: float,
        cognitive_impact: float,
        behavioral_motivation: float
    ) -> float:
        """Calculate overall psychological effectiveness score."""
        
        # Weighted combination
        weights = [0.25, 0.3, 0.25, 0.2]  # Slightly favor emotional resonance
        scores = [wisdom_depth, emotional_resonance, cognitive_impact, behavioral_motivation]
        
        weighted_score = sum(score * weight for score, weight in zip(scores, weights))
        
        return min(1.0, max(0.0, weighted_score))
    
    def _generate_psychological_recommendations(
        self,
        quote_text: str,
        framework_analysis: Dict[str, Any],
        wisdom_depth: float,
        emotional_resonance: float
    ) -> List[str]:
        """Generate recommendations for psychological enhancement."""
        
        recommendations = []
        
        if wisdom_depth < 0.5:
            recommendations.append("Consider adding deeper philosophical or life wisdom elements")
        
        if emotional_resonance < 0.5:
            recommendations.append("Include more emotionally resonant language or universal experiences")
        
        if framework_analysis.get("overall_alignment", 0) < 0.5:
            recommendations.append("Better align with chosen psychological framework principles")
        
        if len(quote_text.split()) > 25:
            recommendations.append("Consider shortening for better psychological impact")
        
        if not any(word in quote_text.lower() for word in ["you", "your", "we", "us"]):
            recommendations.append("Add personal relevance with inclusive pronouns")
        
        return recommendations
    
    def _fallback_analysis(self, prompt: str) -> Dict[str, Any]:
        """Provide basic fallback analysis when main analysis fails."""
        
        return {
            "basic_emotional_tone": "neutral",
            "estimated_needs": ["general wisdom", "inspiration"],
            "suggested_approach": "universal inspirational quote",
            "confidence": 0.3
        }
    
    def _basic_psychological_analysis(self, quote_text: str) -> Dict[str, Any]:
        """Provide basic psychological analysis when full analysis fails."""
        
        word_count = len(quote_text.split())
        
        return {
            "readability": "high" if word_count < 15 else ("medium" if word_count < 25 else "low"),
            "emotional_appeal": "moderate",
            "complexity": "simple" if word_count < 10 else "moderate",
            "target_audience": "general",
            "confidence": 0.4
        }
    
    # Helper methods for personalization analysis
    def _get_age_psychological_factors(self, age_group: str) -> str:
        """Get psychological factors relevant to age group."""
        
        age_factors = {
            "teens": "Identity formation, peer acceptance, future anxiety",
            "twenties": "Career uncertainty, relationship building, independence",
            "thirties": "Achievement pressure, work-life balance, responsibility",
            "forties": "Mid-life reflection, purpose questioning, change adaptation",
            "fifties": "Legacy concerns, health awareness, wisdom sharing",
            "seniors": "Life reflection, meaning-making, acceptance"
        }
        
        return age_factors.get(age_group, "General life development")
    
    def _get_life_stage_needs(self, life_stage: str) -> str:
        """Get psychological needs for specific life stages."""
        
        stage_needs = {
            "student": "Achievement, competence, future planning",
            "career_starter": "Confidence, skill development, direction",
            "parent": "Balance, patience, nurturing wisdom",
            "professional": "Success, leadership, impact",
            "retiree": "Purpose, health, legacy",
            "transition": "Adaptation, courage, new beginnings"
        }
        
        return stage_needs.get(life_stage, "Growth and development")
    
    def _infer_personality_from_interests(self, interests: List[str]) -> Dict[str, float]:
        """Infer personality traits from interests."""
        
        interest_mappings = {
            "creative": ["art", "music", "writing", "design", "photography"],
            "analytical": ["science", "technology", "data", "research", "mathematics"],
            "social": ["volunteering", "community", "networking", "teaching", "counseling"],
            "adventurous": ["travel", "sports", "outdoor", "adventure", "exploration"],
            "intellectual": ["reading", "philosophy", "learning", "education", "history"]
        }
        
        personality_scores = {}
        
        for trait, trait_interests in interest_mappings.items():
            matches = sum(1 for interest in interests 
                         if any(trait_interest in interest.lower() for trait_interest in trait_interests))
            personality_scores[trait] = min(1.0, matches / 3)  # Normalize
        
        return personality_scores
    
    def _assess_challenges_impact(self, challenges: List[str]) -> str:
        """Assess psychological state based on current challenges."""
        
        stress_indicators = ["stress", "anxiety", "overwhelm", "pressure", "burnout"]
        change_indicators = ["transition", "change", "uncertainty", "decision", "choice"]
        relationship_indicators = ["relationship", "family", "friends", "conflict", "loneliness"]
        
        challenge_text = " ".join(challenges).lower()
        
        if any(indicator in challenge_text for indicator in stress_indicators):
            return "High stress, needs calming and coping strategies"
        elif any(indicator in challenge_text for indicator in change_indicators):
            return "In transition, needs guidance and courage"
        elif any(indicator in challenge_text for indicator in relationship_indicators):
            return "Relationship focus, needs connection and understanding"
        else:
            return "General life challenges, needs encouragement and perspective"