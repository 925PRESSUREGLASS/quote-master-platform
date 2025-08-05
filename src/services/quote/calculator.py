"""Quote quality calculation and metrics for Quote Master Pro."""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
import math

logger = logging.getLogger(__name__)


class QuoteCalculator:
    """Calculate various quality metrics and scores for quotes."""
    
    def __init__(self):
        self.common_words = self._load_common_words()
        self.power_words = self._load_power_words()
        self.emotional_words = self._load_emotional_words()
    
    def _load_common_words(self) -> set:
        """Load common English words for analysis."""
        return {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have',
            'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you',
            'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they',
            'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
            'one', 'all', 'would', 'there', 'their', 'what', 'so',
            'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
            'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than',
            'then', 'now', 'look', 'only', 'come', 'its', 'over',
            'think', 'also', 'back', 'after', 'use', 'two', 'how',
            'our', 'work', 'first', 'well', 'way', 'even', 'new',
            'want', 'because', 'any', 'these', 'give', 'day', 'most',
            'us'
        }
    
    def _load_power_words(self) -> set:
        """Load powerful, impactful words."""
        return {
            'achieve', 'amazing', 'awesome', 'breakthrough', 'brilliant',
            'champion', 'conquer', 'create', 'dedicate', 'deliver',
            'dominate', 'drive', 'empower', 'energy', 'excel',
            'exceptional', 'extraordinary', 'fearless', 'focus',
            'genius', 'grow', 'inspire', 'innovate', 'lead',
            'legendary', 'magnificent', 'master', 'overcome',
            'powerful', 'remarkable', 'revolutionary', 'succeed',
            'superb', 'thrive', 'transform', 'triumph', 'ultimate',
            'unstoppable', 'victory', 'win', 'wonder', 'excellence',
            'passion', 'purpose', 'vision', 'wisdom', 'courage',
            'strength', 'hope', 'faith', 'love', 'dream',
            'believe', 'imagine', 'discover', 'explore', 'journey',
            'adventure', 'freedom', 'peace', 'harmony', 'balance'
        }
    
    def _load_emotional_words(self) -> Dict[str, List[str]]:
        """Load emotional words categorized by emotion type."""
        return {
            'positive': [
                'joy', 'happiness', 'love', 'peace', 'hope', 'delight',
                'pleasure', 'bliss', 'contentment', 'satisfaction',
                'gratitude', 'appreciation', 'wonder', 'awe', 'excitement',
                'enthusiasm', 'passion', 'warmth', 'comfort', 'serenity'
            ],
            'negative': [
                'fear', 'anger', 'sadness', 'worry', 'anxiety', 'despair',
                'frustration', 'disappointment', 'regret', 'shame',
                'guilt', 'jealousy', 'hatred', 'resentment', 'bitterness',
                'loneliness', 'emptiness', 'pain', 'suffering', 'grief'
            ],
            'empowering': [
                'strength', 'power', 'courage', 'confidence', 'determination',
                'resilience', 'perseverance', 'grit', 'fortitude', 'valor',
                'bravery', 'boldness', 'assertiveness', 'independence',
                'self-reliance', 'empowerment', 'liberation', 'freedom'
            ],
            'calming': [
                'peace', 'tranquility', 'serenity', 'calm', 'stillness',
                'quiet', 'gentle', 'soothing', 'relaxing', 'restful',
                'harmonious', 'balanced', 'centered', 'grounded',
                'mindful', 'present', 'aware', 'conscious'
            ]
        }
    
    def calculate_quality_metrics(self, quote_text: str) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics for a quote."""
        
        if not quote_text or not quote_text.strip():
            return self._empty_metrics()
        
        try:
            # Basic text metrics
            word_count = len(quote_text.split())
            char_count = len(quote_text)
            sentence_count = len(re.findall(r'[.!?]+', quote_text))
            
            # Readability metrics
            readability_score = self.calculate_readability(quote_text)
            
            # Impact metrics
            impact_score = self.calculate_impact_score(quote_text)
            
            # Emotional resonance
            emotional_analysis = self.analyze_emotional_content(quote_text)
            
            # Uniqueness and originality
            uniqueness_score = self.calculate_uniqueness_score(quote_text)
            
            # Memorability factors
            memorability_score = self.calculate_memorability_score(quote_text)
            
            # Shareability metrics
            shareability_score = self.calculate_shareability_score(quote_text)
            
            # Overall quality score (weighted combination)
            overall_quality = self._calculate_overall_quality(
                readability_score,
                impact_score,
                emotional_analysis['total_score'],
                uniqueness_score,
                memorability_score,
                shareability_score
            )
            
            return {
                'word_count': word_count,
                'character_count': char_count,
                'sentence_count': sentence_count,
                'readability_score': readability_score,
                'impact_score': impact_score,
                'emotional_analysis': emotional_analysis,
                'uniqueness_score': uniqueness_score,
                'memorability_score': memorability_score,
                'shareability_score': shareability_score,
                'overall_quality': overall_quality,
                'length_category': self._categorize_length(word_count),
                'complexity_level': self._assess_complexity(quote_text),
                'recommendations': self._generate_quality_recommendations(
                    readability_score, impact_score, emotional_analysis,
                    uniqueness_score, memorability_score, word_count
                )
            }
            
        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {str(e)}")
            return self._empty_metrics()
    
    def calculate_readability(self, text: str) -> float:
        """Calculate readability score (0-1, higher is more readable)."""
        
        try:
            words = text.split()
            if not words:
                return 0.0
            
            # Word length analysis
            avg_word_length = sum(len(word.strip('.,!?;:"()')) for word in words) / len(words)
            
            # Sentence length analysis
            sentences = re.findall(r'[.!?]+', text)
            avg_sentence_length = len(words) / max(len(sentences), 1)
            
            # Common word usage
            common_word_ratio = sum(1 for word in words 
                                  if word.lower().strip('.,!?;:"()') in self.common_words) / len(words)
            
            # Complexity indicators
            complex_punctuation = len(re.findall(r'[;:()"\[\]]', text))
            complexity_penalty = min(0.3, complex_punctuation * 0.05)
            
            # Calculate readability (inverse of complexity)
            word_length_score = max(0, 1 - (avg_word_length - 4) * 0.1)  # Optimal around 4-5 chars
            sentence_length_score = max(0, 1 - (avg_sentence_length - 15) * 0.05)  # Optimal around 15 words
            common_words_score = min(1.0, common_word_ratio * 1.5)  # Boost for common words
            
            readability = (word_length_score * 0.3 + 
                          sentence_length_score * 0.3 + 
                          common_words_score * 0.4 - 
                          complexity_penalty)
            
            return max(0.0, min(1.0, readability))
            
        except Exception as e:
            logger.error(f"Readability calculation failed: {str(e)}")
            return 0.5
    
    def calculate_impact_score(self, text: str) -> float:
        """Calculate emotional and psychological impact score (0-1)."""
        
        try:
            words = text.lower().split()
            if not words:
                return 0.0
            
            # Power words analysis
            power_word_count = sum(1 for word in words 
                                 if word.strip('.,!?;:"()') in self.power_words)
            power_word_ratio = power_word_count / len(words)
            
            # Emotional word analysis
            emotional_word_count = 0
            for emotion_category in self.emotional_words.values():
                emotional_word_count += sum(1 for word in words 
                                          if word.strip('.,!?;:"()') in emotion_category)
            
            emotional_word_ratio = emotional_word_count / len(words)
            
            # Active voice indicators
            active_voice_indicators = ['achieve', 'create', 'build', 'make', 'do', 'take', 'give']
            active_voice_count = sum(1 for word in words 
                                   if word.strip('.,!?;:"()') in active_voice_indicators)
            active_voice_ratio = active_voice_count / len(words)
            
            # Imperative mood indicators
            imperative_words = ['be', 'do', 'take', 'make', 'choose', 'decide', 'act']
            imperative_count = sum(1 for word in words 
                                 if word.strip('.,!?;:"()') in imperative_words)
            imperative_ratio = imperative_count / len(words)
            
            # Concrete vs abstract balance
            concrete_words = ['hand', 'eye', 'road', 'mountain', 'river', 'sun', 'tree', 'door']
            concrete_count = sum(1 for word in words 
                                if word.strip('.,!?;:"()') in concrete_words)
            concrete_ratio = concrete_count / len(words)
            
            # Calculate impact score
            impact = (power_word_ratio * 0.3 + 
                     emotional_word_ratio * 0.25 + 
                     active_voice_ratio * 0.2 + 
                     imperative_ratio * 0.15 + 
                     concrete_ratio * 0.1)
            
            # Boost for exclamation marks and questions
            punctuation_boost = (text.count('!') * 0.05 + text.count('?') * 0.03)
            
            final_impact = min(1.0, impact + punctuation_boost)
            
            return max(0.0, final_impact)
            
        except Exception as e:
            logger.error(f"Impact score calculation failed: {str(e)}")
            return 0.5
    
    def analyze_emotional_content(self, text: str) -> Dict[str, Any]:
        """Analyze emotional content and categorization."""
        
        try:
            words = text.lower().split()
            if not words:
                return {'total_score': 0.0, 'primary_emotion': 'neutral', 'emotion_scores': {}}
            
            emotion_scores = {}
            total_emotional_words = 0
            
            # Analyze each emotion category
            for emotion_type, emotion_words in self.emotional_words.items():
                count = sum(1 for word in words 
                           if word.strip('.,!?;:"()') in emotion_words)
                emotion_scores[emotion_type] = count / len(words)
                total_emotional_words += count
            
            # Calculate total emotional intensity
            total_score = total_emotional_words / len(words)
            
            # Identify primary emotion
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else 'neutral'
            
            # Calculate emotional balance
            positive_score = emotion_scores.get('positive', 0) + emotion_scores.get('empowering', 0)
            negative_score = emotion_scores.get('negative', 0)
            emotional_balance = 'positive' if positive_score > negative_score else ('negative' if negative_score > positive_score else 'balanced')
            
            return {
                'total_score': min(1.0, total_score),
                'primary_emotion': primary_emotion,
                'emotion_scores': emotion_scores,
                'emotional_balance': emotional_balance,
                'emotional_intensity': self._calculate_emotional_intensity(emotion_scores)
            }
            
        except Exception as e:
            logger.error(f"Emotional analysis failed: {str(e)}")
            return {'total_score': 0.0, 'primary_emotion': 'neutral', 'emotion_scores': {}}
    
    def calculate_uniqueness_score(self, text: str) -> float:
        """Calculate how unique and original the quote appears (0-1)."""
        
        try:
            words = text.lower().split()
            if not words:
                return 0.0
            
            # Vocabulary diversity
            unique_words = len(set(words))
            diversity_ratio = unique_words / len(words)
            
            # Uncommon word usage
            uncommon_word_count = sum(1 for word in words 
                                    if word.strip('.,!?;:"()') not in self.common_words)
            uncommon_ratio = uncommon_word_count / len(words)
            
            # Metaphor and imagery indicators
            imagery_words = ['like', 'as', 'resembles', 'mirrors', 'reflects', 'echoes']
            metaphor_count = sum(1 for word in words 
                               if word.strip('.,!?;:"()') in imagery_words)
            metaphor_ratio = metaphor_count / len(words)
            
            # Creative word combinations (simplified heuristic)
            creative_combinations = 0
            for i in range(len(words) - 1):
                word1 = words[i].strip('.,!?;:"()')
                word2 = words[i + 1].strip('.,!?;:"()')
                
                # Check for interesting adjective-noun combinations
                if (word1 in self.power_words and word2 not in self.common_words) or \
                   (word1 not in self.common_words and word2 in self.power_words):
                    creative_combinations += 1
            
            creative_ratio = creative_combinations / max(len(words) - 1, 1)
            
            # Calculate uniqueness
            uniqueness = (diversity_ratio * 0.3 + 
                         uncommon_ratio * 0.4 + 
                         metaphor_ratio * 0.2 + 
                         creative_ratio * 0.1)
            
            return max(0.0, min(1.0, uniqueness))
            
        except Exception as e:
            logger.error(f"Uniqueness calculation failed: {str(e)}")
            return 0.5
    
    def calculate_memorability_score(self, text: str) -> float:
        """Calculate how memorable the quote is likely to be (0-1)."""
        
        try:
            words = text.split()
            if not words:
                return 0.0
            
            word_count = len(words)
            
            # Optimal length for memorability (research shows 7-15 words ideal)
            if 7 <= word_count <= 15:
                length_score = 1.0
            elif 5 <= word_count <= 20:
                length_score = 0.8
            elif word_count <= 25:
                length_score = 0.6
            else:
                length_score = max(0.2, 1.0 - (word_count - 25) * 0.02)
            
            # Rhyme and rhythm indicators
            rhyme_score = self._detect_rhyme_patterns(text)
            rhythm_score = self._analyze_rhythm(words)
            
            # Repetition and parallel structure
            repetition_score = self._analyze_repetition(words)
            
            # Alliteration
            alliteration_score = self._detect_alliteration(words)
            
            # Simple vs complex structure
            simplicity_score = 1.0 - min(0.5, len(re.findall(r'[,;:]', text)) * 0.1)
            
            # Strong opening/closing
            bookend_score = self._analyze_bookends(words)
            
            memorability = (length_score * 0.25 + 
                           rhyme_score * 0.15 + 
                           rhythm_score * 0.15 + 
                           repetition_score * 0.15 + 
                           alliteration_score * 0.1 + 
                           simplicity_score * 0.1 + 
                           bookend_score * 0.1)
            
            return max(0.0, min(1.0, memorability))
            
        except Exception as e:
            logger.error(f"Memorability calculation failed: {str(e)}")
            return 0.5
    
    def calculate_shareability_score(self, text: str) -> float:
        """Calculate how likely the quote is to be shared (0-1)."""
        
        try:
            word_count = len(text.split())
            char_count = len(text)
            
            # Optimal length for social media sharing
            if char_count <= 140:  # Twitter-friendly
                length_score = 1.0
            elif char_count <= 280:
                length_score = 0.9
            elif char_count <= 400:
                length_score = 0.7
            else:
                length_score = max(0.3, 1.0 - (char_count - 400) * 0.001)
            
            # Emotional appeal (people share emotional content)
            emotional_analysis = self.analyze_emotional_content(text)
            emotional_appeal = emotional_analysis['total_score']
            
            # Universal appeal (broad themes)
            universal_themes = ['love', 'success', 'happiness', 'life', 'hope', 'dreams', 'change']
            universal_appeal = sum(1 for theme in universal_themes 
                                 if theme in text.lower()) / len(universal_themes)
            
            # Quotability factors
            quotability = self._assess_quotability(text)
            
            # Personal relevance indicators
            personal_pronouns = len(re.findall(r'\b(you|your|we|us|our)\b', text.lower()))
            personal_relevance = min(1.0, personal_pronouns * 0.2)
            
            shareability = (length_score * 0.3 + 
                           emotional_appeal * 0.25 + 
                           universal_appeal * 0.2 + 
                           quotability * 0.15 + 
                           personal_relevance * 0.1)
            
            return max(0.0, min(1.0, shareability))
            
        except Exception as e:
            logger.error(f"Shareability calculation failed: {str(e)}")
            return 0.5
    
    def _calculate_overall_quality(self, *scores) -> float:
        """Calculate weighted overall quality score."""
        
        # Weights for different aspects
        weights = [0.2, 0.2, 0.15, 0.15, 0.15, 0.15]  # Must sum to 1.0
        
        if len(scores) != len(weights):
            return sum(scores) / len(scores)  # Simple average fallback
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        return max(0.0, min(1.0, weighted_sum))
    
    def _categorize_length(self, word_count: int) -> str:
        """Categorize quote length."""
        if word_count <= 10:
            return "very_short"
        elif word_count <= 20:
            return "short"
        elif word_count <= 35:
            return "medium"
        elif word_count <= 50:
            return "long"
        else:
            return "very_long"
    
    def _assess_complexity(self, text: str) -> str:
        """Assess text complexity level."""
        
        # Simple heuristics for complexity
        word_count = len(text.split())
        avg_word_length = sum(len(word) for word in text.split()) / word_count if word_count > 0 else 0
        punctuation_count = len(re.findall(r'[,;:()"\[\]]', text))
        
        complexity_score = (avg_word_length * 0.4 + 
                           punctuation_count * 0.3 + 
                           (word_count / 20) * 0.3)
        
        if complexity_score < 2:
            return "simple"
        elif complexity_score < 4:
            return "moderate"
        else:
            return "complex"
    
    def _calculate_emotional_intensity(self, emotion_scores: Dict[str, float]) -> str:
        """Calculate overall emotional intensity."""
        
        total_intensity = sum(emotion_scores.values())
        
        if total_intensity < 0.1:
            return "low"
        elif total_intensity < 0.3:
            return "moderate"
        else:
            return "high"
    
    def _detect_rhyme_patterns(self, text: str) -> float:
        """Detect rhyming patterns (simplified)."""
        
        # This is a very basic implementation
        # In production, you'd use a more sophisticated phonetic analysis
        
        words = [word.strip('.,!?;:"()').lower() for word in text.split()]
        rhyme_score = 0.0
        
        # Check for end rhymes (same ending sounds)
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                if len(words[i]) > 2 and len(words[j]) > 2:
                    if words[i][-2:] == words[j][-2:]:  # Simple ending match
                        rhyme_score += 0.2
        
        return min(1.0, rhyme_score)
    
    def _analyze_rhythm(self, words: List[str]) -> float:
        """Analyze rhythmic patterns in the text."""
        
        # Count syllables (simplified approximation)
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        if not words:
            return 0.0
        
        avg_syllables_per_word = total_syllables / len(words)
        
        # Good rhythm typically has 1.3-2.0 syllables per word
        if 1.3 <= avg_syllables_per_word <= 2.0:
            return 1.0
        else:
            return max(0.0, 1.0 - abs(avg_syllables_per_word - 1.65) * 0.5)
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified approximation)."""
        
        word = word.lower().strip('.,!?;:"()')
        if not word:
            return 0
        
        # Simple vowel counting method
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _analyze_repetition(self, words: List[str]) -> float:
        """Analyze repetition patterns for memorability."""
        
        if len(words) < 2:
            return 0.0
        
        # Check for repeated words
        word_counts = Counter(word.lower().strip('.,!?;:"()') for word in words)
        repeated_words = sum(1 for count in word_counts.values() if count > 1)
        
        # Check for parallel structure (repeated sentence beginnings)
        sentences = re.split(r'[.!?]+', ' '.join(words))
        sentence_starts = [sentence.strip().split()[:2] for sentence in sentences if sentence.strip()]
        
        parallel_structure = 0
        for i in range(len(sentence_starts)):
            for j in range(i + 1, len(sentence_starts)):
                if len(sentence_starts[i]) > 0 and len(sentence_starts[j]) > 0:
                    if sentence_starts[i][0].lower() == sentence_starts[j][0].lower():
                        parallel_structure += 1
        
        repetition_score = (repeated_words * 0.1 + parallel_structure * 0.2)
        return min(1.0, repetition_score)
    
    def _detect_alliteration(self, words: List[str]) -> float:
        """Detect alliteration patterns."""
        
        if len(words) < 2:
            return 0.0
        
        alliteration_count = 0
        
        for i in range(len(words) - 1):
            word1 = words[i].strip('.,!?;:"()').lower()
            word2 = words[i + 1].strip('.,!?;:"()').lower()
            
            if word1 and word2 and word1[0] == word2[0] and word1[0].isalpha():
                alliteration_count += 1
        
        return min(1.0, alliteration_count * 0.3)
    
    def _analyze_bookends(self, words: List[str]) -> float:
        """Analyze the strength of opening and closing words."""
        
        if not words:
            return 0.0
        
        first_word = words[0].strip('.,!?;:"()').lower()
        last_word = words[-1].strip('.,!?;:"()').lower()
        
        strong_openers = {'the', 'every', 'all', 'never', 'always', 'when', 'if', 'true', 'life'}
        strong_closers = {'everything', 'nothing', 'forever', 'always', 'never', 'truth', 'life', 'love'}
        
        opener_score = 1.0 if first_word in strong_openers or first_word in self.power_words else 0.5
        closer_score = 1.0 if last_word in strong_closers or last_word in self.power_words else 0.5
        
        return (opener_score + closer_score) / 2
    
    def _assess_quotability(self, text: str) -> float:
        """Assess how quotable the text is."""
        
        quotability_factors = 0.0
        
        # Complete thoughts
        if text.strip().endswith(('.', '!', '?')):
            quotability_factors += 0.3
        
        # Universal wisdom indicators
        wisdom_words = ['always', 'never', 'every', 'all', 'true', 'truth', 'life', 'love', 'time']
        wisdom_count = sum(1 for word in wisdom_words if word in text.lower())
        quotability_factors += min(0.3, wisdom_count * 0.1)
        
        # Memorable structure
        if any(pattern in text.lower() for pattern in ['not about', 'but about', 'is not', 'is that']):
            quotability_factors += 0.2
        
        # Inspirational tone
        if any(word in text.lower() for word in ['can', 'will', 'believe', 'achieve', 'become']):
            quotability_factors += 0.2
        
        return min(1.0, quotability_factors)
    
    def _generate_quality_recommendations(
        self,
        readability: float,
        impact: float,
        emotional_analysis: Dict[str, Any],
        uniqueness: float,
        memorability: float,
        word_count: int
    ) -> List[str]:
        """Generate recommendations for improving quote quality."""
        
        recommendations = []
        
        if readability < 0.6:
            recommendations.append("Consider using simpler words for better readability")
        
        if impact < 0.5:
            recommendations.append("Add more powerful, action-oriented words for greater impact")
        
        if emotional_analysis['total_score'] < 0.3:
            recommendations.append("Include more emotional language to increase resonance")
        
        if uniqueness < 0.4:
            recommendations.append("Try using more creative metaphors or unique word combinations")
        
        if memorability < 0.5:
            recommendations.append("Consider making the quote shorter or adding rhythmic elements")
        
        if word_count > 30:
            recommendations.append("Consider shortening for better shareability")
        
        if word_count < 5:
            recommendations.append("Consider adding more context or depth")
        
        return recommendations
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            'word_count': 0,
            'character_count': 0,
            'sentence_count': 0,
            'readability_score': 0.0,
            'impact_score': 0.0,
            'emotional_analysis': {'total_score': 0.0, 'primary_emotion': 'neutral', 'emotion_scores': {}},
            'uniqueness_score': 0.0,
            'memorability_score': 0.0,
            'shareability_score': 0.0,
            'overall_quality': 0.0,
            'length_category': 'empty',
            'complexity_level': 'unknown',
            'recommendations': ['Please provide text to analyze']
        }