"""External search client for finding relevant code patterns and features."""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote
import aiohttp
from bs4 import BeautifulSoup

from core.config import Config
from utils.logger import get_logger


@dataclass
class SearchResult:
    """Represents a search result."""
    title: str
    url: str
    snippet: str
    source: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExternalSearchClient:
    """Client for searching external sources for code patterns and features."""
    
    def __init__(self, config: Config):
        """Initialize the search client."""
        self.config = config
        self.logger = get_logger(__name__)
        self.session = None
        
        # API keys from config
        self.serp_api_key = config.get('serp_api_key')
        
        self.logger.info("External search client initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_github_repositories(self, query: str, language: str = None, limit: int = 10) -> List[SearchResult]:
        """Search GitHub repositories for relevant projects."""
        self.logger.info(f"Searching GitHub repositories for: {query}")
        
        try:
            # Build GitHub search query
            search_query = f"{query} in:name,description,readme"
            if language:
                search_query += f" language:{language}"
            
            # Use GitHub API search
            url = "https://api.github.com/search/repositories"
            params = {
                "q": search_query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            headers = {}
            if self.config.github_token:
                headers["Authorization"] = f"token {self.config.github_token}"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        result = SearchResult(
                            title=item['full_name'],
                            url=item['html_url'],
                            snippet=item.get('description', ''),
                            source='github',
                            relevance_score=self._calculate_github_relevance(item, query),
                            metadata={
                                'stars': item['stargazers_count'],
                                'language': item.get('language'),
                                'updated_at': item['updated_at'],
                                'forks': item['forks_count']
                            }
                        )
                        results.append(result)
                    
                    return sorted(results, key=lambda x: x.relevance_score, reverse=True)
                else:
                    self.logger.error(f"GitHub API error: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error searching GitHub: {e}")
            return []
    
    async def search_code_patterns(self, query: str, language: str = None, limit: int = 20) -> List[SearchResult]:
        """Search for specific code patterns and implementations."""
        self.logger.info(f"Searching code patterns for: {query}")
        
        try:
            # Build GitHub code search query
            search_query = query
            if language:
                search_query += f" language:{language}"
            
            url = "https://api.github.com/search/code"
            params = {
                "q": search_query,
                "sort": "indexed",
                "order": "desc",
                "per_page": limit
            }
            
            headers = {}
            if self.config.github_token:
                headers["Authorization"] = f"token {self.config.github_token}"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        result = SearchResult(
                            title=f"{item['repository']['full_name']}/{item['name']}",
                            url=item['html_url'],
                            snippet=self._extract_code_snippet(item.get('text_matches', [])),
                            source='github_code',
                            relevance_score=self._calculate_code_relevance(item, query),
                            metadata={
                                'repository': item['repository']['full_name'],
                                'path': item['path'],
                                'size': item['size']
                            }
                        )
                        results.append(result)
                    
                    return sorted(results, key=lambda x: x.relevance_score, reverse=True)
                else:
                    self.logger.error(f"GitHub Code API error: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error searching code patterns: {e}")
            return []
    
    async def search_web_for_tutorials(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search the web for tutorials and documentation."""
        self.logger.info(f"Searching web for tutorials: {query}")
        
        if not self.serp_api_key:
            self.logger.warning("No SerpAPI key configured, skipping web search")
            return []
        
        try:
            from serpapi import Search
            
            search = Search({
                "q": f"{query} tutorial implementation example",
                "engine": "google",
                "api_key": self.serp_api_key,
                "num": limit
            })
            
            results = search.get_dict()
            search_results = []
            
            for item in results.get('organic_results', []):
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    snippet=item.get('snippet', ''),
                    source='web',
                    relevance_score=self._calculate_web_relevance(item, query),
                    metadata={
                        'position': item.get('position', 0)
                    }
                )
                search_results.append(result)
            
            return sorted(search_results, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error searching web: {e}")
            return []
    
    async def search_stack_overflow(self, query: str, limit: int = 15) -> List[SearchResult]:
        """Search Stack Overflow for solutions and patterns."""
        self.logger.info(f"Searching Stack Overflow for: {query}")
        
        try:
            # Use Stack Overflow API
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": limit,
                "filter": "withbody"
            }
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        result = SearchResult(
                            title=item.get('title', ''),
                            url=item.get('link', ''),
                            snippet=self._clean_html(item.get('body', '')[:300]),
                            source='stackoverflow',
                            relevance_score=self._calculate_so_relevance(item, query),
                            metadata={
                                'score': item.get('score', 0),
                                'answer_count': item.get('answer_count', 0),
                                'is_answered': item.get('is_answered', False),
                                'tags': item.get('tags', [])
                            }
                        )
                        results.append(result)
                    
                    return sorted(results, key=lambda x: x.relevance_score, reverse=True)
                else:
                    self.logger.error(f"Stack Overflow API error: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error searching Stack Overflow: {e}")
            return []
    
    async def comprehensive_search(self, query: str, language: str = None, limit_per_source: int = 5) -> Dict[str, List[SearchResult]]:
        """Perform comprehensive search across all sources."""
        self.logger.info(f"Performing comprehensive search for: {query}")
        
        results = {}
        
        # Search all sources concurrently
        tasks = [
            self.search_github_repositories(query, language, limit_per_source),
            self.search_code_patterns(query, language, limit_per_source),
            self.search_web_for_tutorials(query, limit_per_source),
            self.search_stack_overflow(query, limit_per_source)
        ]
        
        try:
            github_repos, code_patterns, web_tutorials, stackoverflow = await asyncio.gather(*tasks, return_exceptions=True)
            
            results['github_repositories'] = github_repos if not isinstance(github_repos, Exception) else []
            results['code_patterns'] = code_patterns if not isinstance(code_patterns, Exception) else []
            results['web_tutorials'] = web_tutorials if not isinstance(web_tutorials, Exception) else []
            results['stackoverflow'] = stackoverflow if not isinstance(stackoverflow, Exception) else []
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive search: {e}")
            results = {source: [] for source in ['github_repositories', 'code_patterns', 'web_tutorials', 'stackoverflow']}
        
        return results
    
    def _calculate_github_relevance(self, repo: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for GitHub repository."""
        score = 0.0
        query_lower = query.lower()
        
        # Name match
        if query_lower in repo['name'].lower():
            score += 0.4
        
        # Description match
        description = repo.get('description', '').lower()
        if query_lower in description:
            score += 0.3
        
        # Stars boost (normalized)
        stars = repo['stargazers_count']
        score += min(stars / 1000, 0.2)  # Max 0.2 boost from stars
        
        # Recent activity boost
        import datetime
        updated = datetime.datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00'))
        days_since_update = (datetime.datetime.now(datetime.timezone.utc) - updated).days
        if days_since_update < 30:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_code_relevance(self, code_item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for code search result."""
        score = 0.0
        query_lower = query.lower()
        
        # File name match
        if query_lower in code_item['name'].lower():
            score += 0.3
        
        # Path relevance
        if any(term in code_item['path'].lower() for term in query_lower.split()):
            score += 0.2
        
        # Repository stars (if available)
        if 'repository' in code_item and 'stargazers_count' in code_item['repository']:
            stars = code_item['repository']['stargazers_count']
            score += min(stars / 2000, 0.2)
        
        # Text matches boost
        text_matches = code_item.get('text_matches', [])
        if text_matches:
            score += min(len(text_matches) * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _calculate_web_relevance(self, web_item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for web search result."""
        score = 0.0
        query_lower = query.lower()
        
        # Title match
        title = web_item.get('title', '').lower()
        if query_lower in title:
            score += 0.4
        
        # Snippet match
        snippet = web_item.get('snippet', '').lower()
        query_words = query_lower.split()
        matching_words = sum(1 for word in query_words if word in snippet)
        score += (matching_words / len(query_words)) * 0.3
        
        # Position boost (higher positions get higher scores)
        position = web_item.get('position', 10)
        score += max(0, (10 - position) / 10) * 0.3
        
        return min(score, 1.0)
    
    def _calculate_so_relevance(self, so_item: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for Stack Overflow result."""
        score = 0.0
        query_lower = query.lower()
        
        # Title match
        title = so_item.get('title', '').lower()
        if query_lower in title:
            score += 0.4
        
        # Score boost (normalized)
        item_score = so_item.get('score', 0)
        score += min(item_score / 50, 0.2)
        
        # Answer availability
        if so_item.get('is_answered', False):
            score += 0.2
        
        # Answer count boost
        answer_count = so_item.get('answer_count', 0)
        score += min(answer_count / 10, 0.2)
        
        return min(score, 1.0)
    
    def _extract_code_snippet(self, text_matches: List[Dict[str, Any]]) -> str:
        """Extract relevant code snippet from text matches."""
        if not text_matches:
            return ""
        
        # Get the first meaningful match
        for match in text_matches:
            fragment = match.get('fragment', '')
            if len(fragment) > 20:  # Meaningful snippet
                return fragment[:200] + "..."
        
        return ""
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract text."""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text().strip()
        except:
            return html_content