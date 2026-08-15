"""
Web search service for cross-referencing video content with real news sources.
Uses DuckDuckGo Search (no API key required) to find related articles.
"""
import asyncio
from typing import Dict, List, Optional
import re


class WebSearcher:
    """Search the web for news and articles related to video content"""

    def __init__(self):
        self._ddgs = None

    def _get_ddgs(self):
        if self._ddgs is None:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            self._ddgs = DDGS()
        return self._ddgs

    async def search_news(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search for news articles related to a query.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of news articles with title, url, snippet, source
        """
        results = []
        for attempt in range(3):
            try:
                ddgs = self._get_ddgs()
                raw = await asyncio.to_thread(
                    ddgs.news, query, region='wt-wt', max_results=max_results
                )
                for item in raw:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'snippet': item.get('body', item.get('excerpt', '')),
                        'source': item.get('source', item.get('publisher', '')),
                        'date': item.get('date', ''),
                        'image': item.get('image', '')
                    })
                if results:
                    break
                # No news results found, try again
                await asyncio.sleep(2)
            except Exception as e:
                print(f"ℹ️ News search retry {attempt+1}: {e}")
                await asyncio.sleep(3)
        
        # Fallback to text search if news returned nothing
        if not results:
            try:
                ddgs = self._get_ddgs()
                raw = await asyncio.to_thread(
                    ddgs.text, query, max_results=max_results
                )
                for item in raw:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('href', item.get('url', '')),
                        'snippet': item.get('body', item.get('snippet', '')),
                        'source': item.get('source', ''),
                        'date': '',
                        'image': ''
                    })
            except Exception as e2:
                print(f"⚠️ Fallback text search also failed: {e2}")

        return results

    async def search_general(self, query: str, max_results: int = 5) -> List[Dict]:
        """General web search (not restricted to news)"""
        results = []
        for attempt in range(3):
            try:
                ddgs = self._get_ddgs()
                raw = await asyncio.to_thread(
                    ddgs.text, query, max_results=max_results
                )
                for item in raw:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('href', item.get('url', '')),
                        'snippet': item.get('body', item.get('snippet', '')),
                        'source': item.get('source', ''),
                        'date': '',
                        'image': ''
                    })
                if results:
                    break
                await asyncio.sleep(2)
            except Exception as e:
                print(f"⚠️ Web search attempt {attempt+1} failed: {e}")
                await asyncio.sleep(3)

        return results

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract key search terms from transcription text"""
        # Remove common Spanish stopwords
        stopwords = {
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del',
            'al', 'a', 'que', 'en', 'y', 'o', 'se', 'es', 'son', 'por', 'para',
            'con', 'su', 'sus', 'lo', 'le', 'les', 'me', 'te', 'nos', 'les',
            'como', 'más', 'menos', 'muy', 'tan', 'tanto', 'todo', 'toda',
            'todos', 'todas', 'esto', 'eso', 'aquello', 'aquí', 'allí', 'ahí',
            'cuando', 'donde', 'quien', 'qué', 'cómo', 'cuál', 'por qué',
            'porque', 'pues', 'pero', 'aunque', 'sino', 'si', 'no', 'ya',
            'también', 'tampoco', 'entonces', 'así', 'ahora', 'después',
            'antes', 'durante', 'entre', 'sobre', 'tras', 'hacia', 'hasta',
            'desde', 'sin', 'sobre', 'tras', 'él', 'ella', 'ellos', 'ellas',
            'nosotros', 'vosotros', 'ustedes', 'usted', 'ha', 'han', 'fue',
            'ser', 'estar', 'tener', 'hacer', 'decir', 'ir', 'ver', 'dar',
            'saber', 'querer', 'poder', 'decir', 'este', 'esta', 'estos',
            'estas', 'ese', 'esa', 'esos', 'esas', 'mi', 'tu', 'nuestra',
            'nuestro', 'vuestra', 'vuestro', 'mí', 'ti', 'sí', 'mismo',
            'misma', 'ellos', 'ellas', 'hay', 'había', 'habrá', 'puede',
            'pueden', 'debe', 'deben', 'cada', 'otro', 'otra', 'otros', 'otras'
        }

        # Clean and tokenize
        words = re.findall(r'\b[a-záéíóúñ]{3,}\b', text.lower())
        word_freq = {}
        for w in words:
            if w not in stopwords:
                word_freq[w] = word_freq.get(w, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]

    def _cross_reference(self, transcription: str, articles: List[Dict]) -> Dict:
        """
        Cross-reference transcription with found articles to assess credibility.

        Args:
            transcription: Full transcription text
            articles: List of found news articles

        Returns:
            Dict with cross-reference analysis
        """
        if not articles:
            return {
                'has_context': False,
                'sources_found': 0,
                'reliable_sources': 0,
                'matched_sources': [],
                'all_reliable_sources': [
                    'Primicias', 'El Universo', 'El Comercio', 'Ecuavisa',
                    'Teleamazonas', 'Expreso', 'Metro Ecuador', 'Extra',
                    'La Hora', 'Vistazo', 'Wambra', 'GkillCity', '4Pelagatos',
                    'BBC', 'Reuters', 'AP News', 'AFP', 'CNN Español',
                    'El País', 'El Mundo', 'EFE', 'The New York Times',
                    'The Washington Post', 'The Guardian', 'Al Jazeera',
                    'France 24', 'Deutsche Welle', 'Infobae', 'La Nación',
                    'Clarín', 'El Tiempo', 'Semana'
                ],
                'assessment': 'No se encontraron fuentes relacionadas para verificar el contenido.',
                'confidence': 0.0
            }

        trans_lower = transcription.lower()
        trans_keywords = set(self._extract_keywords(transcription, 10))

        # Known reliable news sources (Ecuador + internacional)
        reliable_sources = [
            {'domain': 'primicias.ec', 'name': 'Primicias'},
            {'domain': 'eluniverso.com', 'name': 'El Universo'},
            {'domain': 'elcomercio.com', 'name': 'El Comercio'},
            {'domain': 'ecuavisa.com', 'name': 'Ecuavisa'},
            {'domain': 'teleamazonas.com', 'name': 'Teleamazonas'},
            {'domain': 'expreso.ec', 'name': 'Expreso'},
            {'domain': 'metro.ec', 'name': 'Metro Ecuador'},
            {'domain': 'extra.ec', 'name': 'Extra'},
            {'domain': 'lahora.com', 'name': 'La Hora'},
            {'domain': 'vistazo.com', 'name': 'Vistazo'},
            {'domain': 'wambra.com', 'name': 'Wambra'},
            {'domain': 'gkillcity.com', 'name': 'GkillCity'},
            {'domain': '4pelagatos.com', 'name': '4Pelagatos'},
            {'domain': 'bbc.com', 'name': 'BBC'},
            {'domain': 'bbc.co.uk', 'name': 'BBC'},
            {'domain': 'reuters.com', 'name': 'Reuters'},
            {'domain': 'apnews.com', 'name': 'AP News'},
            {'domain': 'afp.com', 'name': 'AFP'},
            {'domain': 'cnnespanol.cnn.com', 'name': 'CNN Español'},
            {'domain': 'elpais.com', 'name': 'El País'},
            {'domain': 'elmundo.es', 'name': 'El Mundo'},
            {'domain': 'efe.com', 'name': 'EFE'},
            {'domain': 'nytimes.com', 'name': 'The New York Times'},
            {'domain': 'washingtonpost.com', 'name': 'The Washington Post'},
            {'domain': 'theguardian.com', 'name': 'The Guardian'},
            {'domain': 'aljazeera.com', 'name': 'Al Jazeera'},
            {'domain': 'france24.com', 'name': 'France 24'},
            {'domain': 'dw.com', 'name': 'Deutsche Welle'},
            {'domain': 'infobae.com', 'name': 'Infobae'},
            {'domain': 'lanacion.com.ar', 'name': 'La Nación'},
            {'domain': 'clarin.com', 'name': 'Clarín'},
            {'domain': 'eltiempo.com', 'name': 'El Tiempo'},
            {'domain': 'semana.com', 'name': 'Semana'},
        ]
        reliable_domains = [r['domain'] for r in reliable_sources]

        matching_articles = []
        reliable_count = 0
        matched_sources = []

        for article in articles:
            title = article.get('title', '').lower()
            snippet = article.get('snippet', '').lower()
            source = article.get('source', '').lower()
            url = article.get('url', '').lower()

            # Check if article content overlaps with transcription keywords
            article_text = f"{title} {snippet}"
            article_words = set(re.findall(r'\b[a-záéíóúñ]{3,}\b', article_text))
            overlap = trans_keywords & article_words

            # Find which reliable source matched
            matched_source_name = None
            for rs in reliable_sources:
                if rs['domain'] in url or rs['domain'] in source:
                    matched_source_name = rs['name']
                    break

            is_reliable = matched_source_name is not None

            if is_reliable:
                reliable_count += 1
                if matched_source_name not in matched_sources:
                    matched_sources.append(matched_source_name)

            if overlap or is_reliable:
                matching_articles.append({
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', ''),
                    'snippet': article.get('snippet', '')[:200],
                    'is_reliable': is_reliable,
                    'reliable_name': matched_source_name,
                    'keyword_overlap': len(overlap),
                    'date': article.get('date', '')
                })

        # Sort by reliability and overlap
        matching_articles.sort(key=lambda x: (x['is_reliable'], x['keyword_overlap']), reverse=True)

        # Assessment
        if reliable_count >= 2:
            assessment = f'Contenido respaldado por {reliable_count} fuentes confiables. La información coincide con reportajes de medios reconocidos.'
            confidence = 0.85
        elif reliable_count == 1:
            assessment = 'Contenido parcialmente respaldado por al menos una fuente confiable. Se recomienda corroborar con fuentes adicionales.'
            confidence = 0.65
        elif len(matching_articles) > 0:
            assessment = f'Se encontraron {len(matching_articles)} resultados relacionados, pero ninguno de medios ampliamente reconocidos. La información puede ser verídica pero requiere corroboración manual.'
            confidence = 0.45
        else:
            assessment = 'No se encontraron fuentes que respalden directamente el contenido. Esto no significa que sea falso, pero no hay corroboración externa disponible.'
            confidence = 0.2

        return {
            'has_context': True,
            'sources_found': len(articles),
            'reliable_sources': reliable_count,
            'matched_sources': matched_sources,
            'all_reliable_sources': [rs['name'] for rs in reliable_sources],
            'matching_articles': matching_articles[:5],
            'assessment': assessment,
            'confidence': confidence
        }

    async def analyze_context(self, transcription: str, title: str = '', channel: str = '') -> Dict:
        """
        Full context analysis: search web for related news and cross-reference.

        Args:
            transcription: Full transcription text
            title: Video title (if available)
            channel: Channel name (if available)

        Returns:
            Dict with web context analysis
        """
        # Build search query - combine cleaned title + keywords for better results
        keywords = self._extract_keywords(transcription, 8)
        
        # Clean title: remove parentheses, extra chars
        clean_title = re.sub(r'[\(\)\[\]\{\}]', '', title).strip() if title else ''
        
        # Build query with context terms
        if clean_title and keywords:
            # Use title + top 3 keywords for specificity
            query = f"{clean_title} {' '.join(keywords[:3])}"
        elif clean_title:
            query = clean_title
        elif keywords:
            query = ' '.join(keywords[:5])
        elif channel:
            query = f"{channel} noticias Ecuador"
        else:
            query = transcription[:150]

        # Add Ecuador context if not present
        if 'ecuador' not in query.lower() and 'correa' not in query.lower():
            query = f"{query} Ecuador"

        # Try news search first, fallback to general search
        all_articles = await self.search_news(query, max_results=8)
        if not all_articles:
            print(f"📰 News search empty, trying general search...")
            all_articles = await self.search_general(query, max_results=8)

        # If results are poor, try with keywords only from transcription
        if len(all_articles) < 3 and keywords:
            kw_query = f"{' '.join(keywords[:5])} Ecuador noticias"
            print(f"📰 Trying keyword search: {kw_query}")
            kw_articles = await self.search_general(kw_query, max_results=8)
            # Merge unique
            seen = {a.get('url') for a in all_articles}
            for a in kw_articles:
                if a.get('url') not in seen:
                    all_articles.append(a)
                    seen.add(a.get('url'))

        # Filter out obviously irrelevant results (music, sports, etc)
        irrelevant_sources = ['wikipedia.org', 'youtube.com/music', 'spotify', 'instagram', 'facebook.com/profiles']
        all_articles = [a for a in all_articles if not any(s in (a.get('url', '') + a.get('source', '')).lower() for s in irrelevant_sources)]

        print(f"📰 Total articles found: {len(all_articles)}")

        # Cross-reference
        cross_ref = self._cross_reference(transcription, all_articles)

        return {
            'search_queries': [query],
            'total_articles_found': len(all_articles),
            'articles': all_articles[:8],
            'cross_reference': cross_ref
        }
