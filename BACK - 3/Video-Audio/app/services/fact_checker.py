"""
Fact-checking service using Google Fact Check Tools API
"""
from googleapiclient.discovery import build
from google.oauth2 import service_account
from typing import Dict, List, Optional
import os
from app.config import settings


class FactChecker:
    """Service for fact-checking claims using Google Fact Check API"""
    
    def __init__(self):
        """Initialize Google Fact Check API client"""
        self.service = None
        
    def _init_service(self):
        """Initialize Google Fact Check API client"""
        if self.service is None and settings.enable_fact_checking:
            try:
                api_key = settings.google_fact_check_api_key
                if api_key:
                    print("🔍 Initializing Google Fact Check API with API key...")
                    self.service = build('factchecktools', 'v1alpha1', developerKey=api_key)
                    print("✅ Google Fact Check API initialized")
                else:
                    # No API key - use service account as fallback
                    creds_path = settings.google_application_credentials
                    if os.path.exists(creds_path):
                        credentials = service_account.Credentials.from_service_account_file(
                            creds_path,
                            scopes=['https://www.googleapis.com/auth/userinfo.email']
                        )
                        self.service = build('factchecktools', 'v1alpha1', credentials=credentials)
                        print("✅ Google Fact Check API initialized (service account)")
                    else:
                        print("⚠️ No Fact Check API key or credentials found, skipping fact-check")
                        self.service = None
            except Exception as e:
                print(f"⚠️ Could not initialize Google Fact Check API: {e}")
                self.service = None
    
    async def check_claim(self, claim: str, language: str = 'es') -> Dict:
        """
        Check a single claim against fact-check database
        
        Args:
            claim: Claim to fact-check
            language: Language code (default: es)
            
        Returns:
            Dict with fact-check results
        """
        self._init_service()
        
        if not self.service:
            return {
                'claim': claim,
                'fact_checks_found': 0,
                'fact_checks': [],
                'status': 'service_unavailable'
            }
        
        # Google Fact Check API needs meaningful claims, not short fragments
        query = claim.strip()[:80]
        # Skip queries that are too short or just filler words
        if len(query) < 20:
            return {
                'claim': claim,
                'fact_checks_found': 0,
                'fact_checks': [],
                'status': 'query_too_short'
            }
        # Skip common filler phrases that aren't claims
        filler_words = ['en todo caso', 'por lo tanto', 'es decir', 'o el cual', 'entre ustedes',
                        'no te acuerdo', 'para que', 'con el cual', 'de la misma']
        if any(query.lower().startswith(fw) for fw in filler_words):
            return {
                'claim': claim,
                'fact_checks_found': 0,
                'fact_checks': [],
                'status': 'not_a_claim'
            }
        
        try:
            # Search for fact-checks
            request = self.service.claims().search(
                query=query,
                languageCode=language,
                pageSize=5
            )
            
            response = request.execute()
            
            claims = response.get('claims', [])
            
            return {
                'claim': claim,
                'fact_checks_found': len(claims),
                'fact_checks': self._parse_fact_checks(claims),
                'status': 'success'
            }
            
        except Exception as e:
            print(f"⚠️ Fact-check API error: {e}")
            return {
                'claim': claim,
                'fact_checks_found': 0,
                'fact_checks': [],
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_fact_checks(self, claims: List) -> List[Dict]:
        """Parse fact-check results from API response"""
        parsed = []
        
        for claim_data in claims:
            claim_review = claim_data.get('claimReview', [])
            
            for review in claim_review:
                parsed.append({
                    'claim_text': claim_data.get('text', ''),
                    'claimant': claim_data.get('claimant', 'Unknown'),
                    'claim_date': claim_data.get('claimDate', ''),
                    'publisher': review.get('publisher', {}).get('name', 'Unknown'),
                    'url': review.get('url', ''),
                    'title': review.get('title', ''),
                    'rating': review.get('textualRating', 'Unknown'),
                    'language': review.get('languageCode', 'es')
                })
        
        return parsed
    
    async def check_multiple_claims(self, claims: List[str], language: str = 'es') -> Dict:
        """
        Check multiple claims
        
        Args:
            claims: List of claims to check
            language: Language code
            
        Returns:
            Dict with aggregated results
        """
        results = []
        total_fact_checks = 0
        
        for claim in claims:
            result = await self.check_claim(claim, language)
            results.append(result)
            total_fact_checks += result['fact_checks_found']
        
        return {
            'total_claims_checked': len(claims),
            'total_fact_checks_found': total_fact_checks,
            'results': results,
            'has_fact_checks': total_fact_checks > 0
        }
    
    async def analyze_text(self, text: str, language: str = 'es') -> Dict:
        """
        Analyze full text and extract/check claims
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            Dict with analysis results
        """
        # Extract meaningful claims - sentences between 20-80 chars, skip fillers
        filler_starts = {'en todo caso', 'por lo tanto', 'es decir', 'o el cual', 'entre ustedes',
                         'no te acuerdo', 'para que', 'con el cual', 'de la misma', 'pero bueno',
                         'y entonces', 'o sea', 'pues bien', 'así que'}
        sentences = []
        for s in text.split('.'):
            s = s.strip()
            if 20 < len(s) <= 80 and not any(s.lower().startswith(fw) for fw in filler_starts):
                sentences.append(s[:80])
        
        # Limit to first 3 sentences to avoid API quota
        claims_to_check = sentences[:3]
        
        if not claims_to_check:
            return {
                'status': 'no_claims_found',
                'total_fact_checks_found': 0,
                'results': []
            }
        
        # Check claims
        return await self.check_multiple_claims(claims_to_check, language)
