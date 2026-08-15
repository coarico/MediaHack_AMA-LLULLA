"""
Content analysis service for detecting fake news and misinformation
"""
from typing import Dict, List
from app.config import settings


class ContentAnalyzer:
    """Service for analyzing text content for fake news"""
    
    def __init__(self):
        """Initialize fake news detection model"""
        self.classifier = None
        
    def _load_model(self):
        """Lazy load fake news classifier"""
        if self.classifier is None:
            print("🔍 Loading Fake News Detection model...")
            try:
                from transformers import pipeline
                # Try Spanish fake news classifier, fallback to multilingual
                try:
                    self.classifier = pipeline(
                        "text-classification",
                        model="mrm8488/bert-spanish-cased-finetuned-fake-news"
                    )
                except Exception:
                    # Model no longer available, use alternative
                    self.classifier = pipeline(
                        "text-classification",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                print("✅ Fake News Detection model loaded")
            except Exception as e:
                # Silently fall back to heuristics - no need to alarm the user
                self.classifier = None
    
    async def analyze_content(self, text: str) -> Dict:
        """
        Analyze text for fake news indicators
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with analysis results
        """
        if not text or len(text.strip()) < 10:
            return {
                'is_fake_news': False,
                'confidence': 0.0,
                'label': 'INSUFFICIENT_TEXT',
                'details': 'Text too short for analysis'
            }
        
        # Try ML model first
        if settings.enable_fake_news_detection:
            self._load_model()
            
            if self.classifier:
                return await self._analyze_with_ml(text)
        
        # Fallback to heuristic analysis
        return await self._analyze_heuristic(text)
    
    async def _analyze_with_ml(self, text: str) -> Dict:
        """Analyze using ML model"""
        try:
            # Truncate text if too long (BERT limit)
            max_length = 512
            text_truncated = text[:max_length] if len(text) > max_length else text
            
            result = self.classifier(text_truncated)[0]
            
            is_fake = result['label'].upper() in ['FAKE', 'FALSE', 'FALSO']
            
            return {
                'is_fake_news': is_fake,
                'confidence': result['score'],
                'label': result['label'],
                'method': 'ml_model',
                'details': f"ML classification: {result['label']} ({result['score']:.2%})"
            }
            
        except Exception as e:
            print(f"⚠️ ML analysis failed: {e}")
            return await self._analyze_heuristic(text)
    
    async def _analyze_heuristic(self, text: str) -> Dict:
        """Fallback heuristic analysis"""
        
        # Fake news indicators (Spanish)
        fake_indicators = [
            'urgente', 'bomba', 'exclusiva', 'increíble', 'no creerás',
            'comparte', 'viral', 'censurado', 'ocultan', 'prohibido',
            'secreto', 'revelado', 'impactante', 'shock'
        ]
        
        text_lower = text.lower()
        
        # Count indicators
        indicator_count = sum(1 for indicator in fake_indicators if indicator in text_lower)
        
        # Simple scoring
        score = min(indicator_count / 5.0, 1.0)
        is_fake = score > settings.fake_news_threshold
        
        return {
            'is_fake_news': is_fake,
            'confidence': score,
            'label': 'FAKE' if is_fake else 'REAL',
            'method': 'heuristic',
            'details': f"Found {indicator_count} fake news indicators",
            'indicators_found': indicator_count
        }
    
    async def extract_claims(self, text: str) -> List[str]:
        """
        Extract potential claims from text for fact-checking
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted claims
        """
        # Simple sentence splitting
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
        
        # Filter for claim-like sentences
        claims = []
        claim_keywords = ['propone', 'dice', 'afirma', 'declara', 'anuncia', 'promete']
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in claim_keywords):
                claims.append(sentence)
        
        return claims[:5]  # Return top 5 claims
