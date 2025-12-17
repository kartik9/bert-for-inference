"""
Research Agent
Autonomously searches for and collects threat intelligence articles
"""

import json
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.llm_client import LLMClient
from ts_newsletter.tools import RSSReader, SearchAPI, WebScraper


class ResearchAgent(BaseAgent):
    """
    Research Agent - Autonomous information gatherer

    Capabilities:
    - Execute targeted search queries
    - Monitor RSS feeds
    - Fetch full article content
    - Follow citation chains
    - Deduplicate findings
    - Store articles in database
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any,
        search_api: SearchAPI,
        rss_reader: RSSReader,
        web_scraper: WebScraper,
        database_client: Optional[Any] = None
    ):
        """
        Initialize Research Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for reasoning
            config: Global configuration
            search_api: Search API instance (DuckDuckGo or Bing)
            rss_reader: RSS reader instance
            web_scraper: Web scraper instance
            database_client: Database client for storing articles
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="research",
            llm_client=llm_client,
            config=config,
            max_iterations=15  # Research might need more iterations
        )

        self.search_api = search_api
        self.rss_reader = rss_reader
        self.web_scraper = web_scraper
        self.database_client = database_client

        # Storage for found articles
        self.collected_articles: List[Dict[str, Any]] = []
        self.seen_urls = set()

    def _register_tools(self):
        """Register research tools"""

        # Web search tool
        self.register_tool(
            name="web_search",
            description="Search the web for articles about advertising fraud and security threats. Returns list of search results with titles, URLs, and snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'malvertising 2025', 'deepfake advertising fraud')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 20
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            function=self._web_search_tool
        )

        # Fetch RSS feeds tool
        self.register_tool(
            name="fetch_rss_feeds",
            description="Fetch recent articles from configured RSS feeds (security blogs, ad tech industry sources). Returns list of articles from feeds.",
            parameters={
                "type": "object",
                "properties": {
                    "feed_category": {
                        "type": "string",
                        "description": "Category of feeds to fetch: 'security_blogs', 'ad_tech_industry', or 'all'",
                        "default": "all"
                    },
                    "max_age_days": {
                        "type": "integer",
                        "description": "Only return articles newer than this many days",
                        "default": 7
                    }
                },
                "required": [],
                "additionalProperties": False
            },
            function=self._fetch_rss_feeds_tool
        )

        # Fetch full article content
        self.register_tool(
            name="fetch_article",
            description="Fetch the full content of an article from a URL. Use this to get detailed content for promising articles found via search or RSS.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the article to fetch"
                    }
                },
                "required": ["url"],
                "additionalProperties": False
            },
            function=self._fetch_article_tool
        )

        # Store article
        self.register_tool(
            name="store_article",
            description="Store an article for later processing. Use this after determining an article is relevant.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Article URL"
                    },
                    "title": {
                        "type": "string",
                        "description": "Article title"
                    },
                    "snippet": {
                        "type": "string",
                        "description": "Brief snippet or summary"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source name (e.g., 'Krebs on Security', 'web_search')"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason why this article is relevant"
                    }
                },
                "required": ["url", "title", "snippet", "source"],
                "additionalProperties": False
            },
            function=self._store_article_tool
        )

        # Get collected count
        self.register_tool(
            name="get_collection_status",
            description="Get status of article collection (how many articles collected, what topics covered)",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            function=self._get_collection_status_tool
        )

    def _web_search_tool(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Execute web search"""
        try:
            results = self.search_api.search(query, max_results=max_results)

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "snippet": r.snippet,
                        "source": r.source
                    }
                    for r in results
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _fetch_rss_feeds_tool(
        self,
        feed_category: str = "all",
        max_age_days: int = 7
    ) -> Dict[str, Any]:
        """Fetch RSS feeds"""
        try:
            feeds_config = self.config.get_rss_feeds()
            feeds_to_fetch = []

            if feed_category == "all":
                for category_feeds in feeds_config.values():
                    feeds_to_fetch.extend(category_feeds)
            elif feed_category in feeds_config:
                feeds_to_fetch = feeds_config[feed_category]
            else:
                return {
                    "success": False,
                    "error": f"Unknown feed category: {feed_category}"
                }

            articles = self.rss_reader.fetch_multiple_feeds(
                feeds_to_fetch,
                max_age_days=max_age_days
            )

            return {
                "success": True,
                "feed_category": feed_category,
                "feeds_checked": len(feeds_to_fetch),
                "articles_found": len(articles),
                "articles": [
                    {
                        "title": a.title,
                        "url": a.url,
                        "summary": a.summary,
                        "source": a.source_feed,
                        "published": str(a.published_date) if a.published_date else None
                    }
                    for a in articles
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _fetch_article_tool(self, url: str) -> Dict[str, Any]:
        """Fetch full article content"""
        try:
            article = self.web_scraper.fetch_url(url)

            if article:
                return {
                    "success": True,
                    "url": article.url,
                    "title": article.title,
                    "content": article.content[:5000],  # Truncate for LLM context
                    "author": article.author,
                    "published_date": str(article.published_date) if article.published_date else None,
                    "content_length": len(article.content)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to fetch article"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _store_article_tool(
        self,
        url: str,
        title: str,
        snippet: str,
        source: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Store article for later processing"""
        # Check for duplicates
        if url in self.seen_urls:
            return {
                "success": False,
                "message": "Article already collected"
            }

        # Store in memory
        article_data = {
            "url": url,
            "title": title,
            "snippet": snippet,
            "source": source,
            "reason": reason,
            "collected_at": str(self.trace.start_time)
        }

        self.collected_articles.append(article_data)
        self.seen_urls.add(url)

        # TODO: Store in database if client provided
        # if self.database_client:
        #     self.database_client.store_article(article_data)

        return {
            "success": True,
            "message": f"Article stored (total: {len(self.collected_articles)})",
            "article_id": len(self.collected_articles) - 1
        }

    def _get_collection_status_tool(self) -> Dict[str, Any]:
        """Get collection status"""
        return {
            "total_collected": len(self.collected_articles),
            "unique_sources": len(set(a["source"] for a in self.collected_articles)),
            "articles": [
                {
                    "title": a["title"],
                    "source": a["source"],
                    "reason": a.get("reason", "")
                }
                for a in self.collected_articles[-5:]  # Last 5
            ]
        }

    def get_system_prompt(self) -> str:
        """System prompt for Research Agent"""
        search_queries = self.config.get_search_queries()

        return f"""You are an expert threat intelligence researcher specializing in advertising fraud and security.

Your role is to autonomously gather articles about Trust & Safety threats affecting advertising platforms.

RESEARCH STRATEGY:
1. Start with RSS feeds to get curated sources
2. Execute targeted web searches for specific topics
3. Evaluate each result for relevance before storing
4. Be thorough but efficient - aim for quality over quantity
5. Follow citation chains for high-value sources
6. Track your progress and avoid duplicates

FOCUS AREAS:
{json.dumps(search_queries, indent=2)}

RELEVANCE CRITERIA:
- Novel fraud techniques or evasion methods
- Large-scale incidents ($1M+ impact or major platform)
- New regulatory enforcement actions
- Critical security vulnerabilities in ad tech
- Major platform policy changes affecting fraud detection
- Industry trend reports with quantitative data
- Research papers on ad fraud taxonomy

IGNORE:
- Generic cybersecurity news without ad-specific context
- Product marketing without technical substance
- Duplicate coverage of same incident
- Articles older than 7 days (unless exceptional)

TOOLS AVAILABLE:
- web_search: Search for specific topics
- fetch_rss_feeds: Get articles from security blogs
- fetch_article: Get full content of promising articles
- store_article: Save relevant articles
- get_collection_status: Check your progress

WORKFLOW:
1. Check RSS feeds for recent security blog posts
2. Execute targeted searches for key topics
3. Evaluate results and fetch full content for promising articles
4. Store relevant articles with clear reasoning
5. Continue until you've collected 15-25 high-quality articles

Be systematic and explain your search strategy before executing."""

    def get_collected_articles(self) -> List[Dict[str, Any]]:
        """Get all collected articles"""
        return self.collected_articles


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory
    from ts_newsletter.tools import SearchAPIFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="research")
    search_api = SearchAPIFactory.create(config)
    rss_reader = RSSReader()
    web_scraper = WebScraper()

    # Create research agent
    agent = ResearchAgent(
        agent_name="research-1",
        llm_client=llm_client,
        config=config,
        search_api=search_api,
        rss_reader=rss_reader,
        web_scraper=web_scraper
    )

    # Run research task
    result = agent.run(
        task="Find recent articles about advertising fraud and malvertising published in the last 7 days. Focus on novel techniques and high-impact incidents."
    )

    print(f"\n{result}")
    print(f"\nCollected {len(agent.get_collected_articles())} articles:")
    for i, article in enumerate(agent.get_collected_articles(), 1):
        print(f"{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Reason: {article.get('reason', 'N/A')}")
        print()
