"""
Relevance Agent
Intelligent filtering and prioritization of articles using multi-dimensional scoring
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.llm_client import LLMClient


@dataclass
class ArticleScore:
    """Multi-dimensional article score"""
    article_id: str
    url: str
    title: str

    # Score dimensions (0-10)
    relevance: float
    novelty: float
    impact: float
    actionability: float

    # Computed
    overall_score: float
    priority_level: str  # "HIGH", "MEDIUM", "LOW"

    # Reasoning
    reasoning: str
    flags: List[str]
    recommended_action: Optional[str] = None


class RelevanceAgent(BaseAgent):
    """
    Relevance Agent - Intelligent filter and prioritizer

    Capabilities:
    - Multi-dimensional scoring (relevance, novelty, impact, actionability)
    - LLM-powered evaluation (not rule-based)
    - Cluster related articles
    - Flag high-priority items
    - Historical context awareness
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any,
        database_client: Optional[Any] = None
    ):
        """
        Initialize Relevance Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for reasoning
            config: Global configuration
            database_client: Database client for historical context
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="relevance",
            llm_client=llm_client,
            config=config,
            max_iterations=8
        )

        self.database_client = database_client
        self.scored_articles: List[ArticleScore] = []

    def _register_tools(self):
        """Register relevance scoring tools"""

        # Score article tool
        self.register_tool(
            name="score_article",
            description="Score an article on multiple dimensions (relevance, novelty, impact, actionability). Returns detailed scores and reasoning.",
            parameters={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "Unique identifier for the article"
                    },
                    "url": {
                        "type": "string",
                        "description": "Article URL"
                    },
                    "title": {
                        "type": "string",
                        "description": "Article title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content or snippet"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source name"
                    }
                },
                "required": ["article_id", "url", "title", "content"],
                "additionalProperties": False
            },
            function=self._score_article_tool
        )

        # Get scoring summary
        self.register_tool(
            name="get_scoring_summary",
            description="Get summary of scored articles including distribution by priority level",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            function=self._get_scoring_summary_tool
        )

    def _score_article_tool(
        self,
        article_id: str,
        url: str,
        title: str,
        content: str,
        source: str = ""
    ) -> Dict[str, Any]:
        """
        Score an article using LLM evaluation

        This creates a nested LLM call where the agent uses the LLM
        to evaluate the article on multiple dimensions.
        """
        try:
            # Build evaluation prompt
            eval_prompt = f"""Evaluate this article for a Trust & Safety newsletter about advertising fraud and security.

Article Title: {title}
Source: {source}
URL: {url}

Content:
{content[:2000]}...

Evaluate on these dimensions (score 0-10):

1. **Relevance to Microsoft Ads Trust & Safety** (0-10)
   - Does it discuss threats affecting display/search/video ads?
   - Is it specific to ad fraud or generic cybersecurity?
   - Does it mention platforms like Google Ads, Meta, or programmatic ecosystem?

2. **Novelty** (0-10)
   - Is this a new technique/threat or rehash of known issues?
   - Are there fresh insights or just reporting on existing knowledge?

3. **Impact** (0-10)
   - Scale of threat (individual scams vs. systemic vulnerabilities)
   - Financial or user safety implications
   - Affects major platforms or niche cases?

4. **Actionability** (0-10)
   - Can Microsoft Ads team take concrete action?
   - Contains technical details for implementation?
   - Or just awareness/monitoring?

Provide scores and detailed reasoning. If overall score is 8+, flag as HIGH priority.

Respond in JSON format:
{{
  "relevance": <score>,
  "novelty": <score>,
  "impact": <score>,
  "actionability": <score>,
  "reasoning": "<detailed explanation>",
  "flags": ["<flag1>", "<flag2>"],
  "recommended_action": "<specific action or null>"
}}"""

            # Use LLM to evaluate (structured output)
            response = self.llm_client.generate(
                input=eval_prompt,
                instructions="You are an expert in advertising platform security. Provide objective, accurate scoring.",
                temperature=0.3  # Lower temperature for consistent scoring
            )

            # Parse JSON response
            try:
                scores_data = json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    scores_data = json.loads(json_match.group(1))
                else:
                    # Fallback: use default scores
                    scores_data = {
                        "relevance": 5.0,
                        "novelty": 5.0,
                        "impact": 5.0,
                        "actionability": 5.0,
                        "reasoning": "Error parsing LLM response",
                        "flags": [],
                        "recommended_action": None
                    }

            # Calculate overall score (weighted average)
            overall = (
                scores_data["relevance"] * 0.35 +
                scores_data["novelty"] * 0.25 +
                scores_data["impact"] * 0.30 +
                scores_data["actionability"] * 0.10
            )

            # Determine priority level
            if overall >= self.config.newsletter.high_priority_threshold:
                priority = "HIGH"
            elif overall >= 6.0:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            # Create score object
            article_score = ArticleScore(
                article_id=article_id,
                url=url,
                title=title,
                relevance=scores_data["relevance"],
                novelty=scores_data["novelty"],
                impact=scores_data["impact"],
                actionability=scores_data["actionability"],
                overall_score=overall,
                priority_level=priority,
                reasoning=scores_data["reasoning"],
                flags=scores_data.get("flags", []),
                recommended_action=scores_data.get("recommended_action")
            )

            # Store score
            self.scored_articles.append(article_score)

            return {
                "success": True,
                "article_id": article_id,
                "overall_score": overall,
                "priority": priority,
                "scores": {
                    "relevance": scores_data["relevance"],
                    "novelty": scores_data["novelty"],
                    "impact": scores_data["impact"],
                    "actionability": scores_data["actionability"]
                },
                "reasoning": scores_data["reasoning"][:200]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_scoring_summary_tool(self) -> Dict[str, Any]:
        """Get scoring summary"""
        if not self.scored_articles:
            return {
                "total_scored": 0,
                "message": "No articles scored yet"
            }

        high_priority = [a for a in self.scored_articles if a.priority_level == "HIGH"]
        medium_priority = [a for a in self.scored_articles if a.priority_level == "MEDIUM"]
        low_priority = [a for a in self.scored_articles if a.priority_level == "LOW"]

        return {
            "total_scored": len(self.scored_articles),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "average_score": sum(a.overall_score for a in self.scored_articles) / len(self.scored_articles),
            "top_articles": [
                {
                    "title": a.title,
                    "score": a.overall_score,
                    "priority": a.priority_level
                }
                for a in sorted(self.scored_articles, key=lambda x: x.overall_score, reverse=True)[:5]
            ]
        }

    def get_system_prompt(self) -> str:
        """System prompt for Relevance Agent"""
        return f"""You are an expert evaluator for Trust & Safety intelligence.

Your role is to score articles on multiple dimensions to determine their value for a newsletter about advertising fraud and security threats.

SCORING CRITERIA:

**Relevance (0-10):**
- 9-10: Directly about ad fraud/malvertising on major platforms
- 7-8: Related to ad tech security, applicable to Microsoft Ads
- 5-6: Tangentially related cybersecurity with ad context
- 3-4: Generic security news with minor ad mentions
- 0-2: Not relevant to advertising security

**Novelty (0-10):**
- 9-10: Completely new threat/technique, breakthrough research
- 7-8: Fresh insights on known threats, new data/analysis
- 5-6: Timely coverage of recent incident with details
- 3-4: Recap of known threats with minor updates
- 0-2: Old news or common knowledge

**Impact (0-10):**
- 9-10: Systemic threat, $10M+ impact, platform-wide vulnerability
- 7-8: Significant incident, $1M+ impact, affects major advertisers
- 5-6: Moderate threat, documented impact, industry-wide relevance
- 3-4: Minor incident, limited scope, niche impact
- 0-2: Theoretical or negligible impact

**Actionability (0-10):**
- 9-10: Clear technical details, specific detection/prevention methods
- 7-8: Enough detail to investigate, identify gaps in current defenses
- 5-6: Awareness-level intel, suggests areas for monitoring
- 3-4: General recommendations without specifics
- 0-2: No actionable information

THRESHOLDS:
- High Priority: Overall score ≥ {self.config.newsletter.high_priority_threshold}
- Medium Priority: Overall score ≥ 6.0
- Low Priority: Overall score < 6.0

TOOLS:
- score_article: Evaluate a single article
- get_scoring_summary: Check overall scoring progress

Be objective and consistent. Use the full 0-10 scale. Provide clear reasoning."""

    def get_scored_articles(self, min_score: Optional[float] = None) -> List[ArticleScore]:
        """Get scored articles, optionally filtered by minimum score"""
        if min_score is None:
            return sorted(self.scored_articles, key=lambda x: x.overall_score, reverse=True)

        filtered = [a for a in self.scored_articles if a.overall_score >= min_score]
        return sorted(filtered, key=lambda x: x.overall_score, reverse=True)

    def get_high_priority_articles(self) -> List[ArticleScore]:
        """Get only high-priority articles"""
        return [a for a in self.scored_articles if a.priority_level == "HIGH"]


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="relevance")

    agent = RelevanceAgent(
        agent_name="relevance-1",
        llm_client=llm_client,
        config=config
    )

    # Example task
    task = """Score these articles for the newsletter:

Article 1:
Title: "New Parked Domain Malvertising Campaign Affects 90% of Visitors"
Source: Infoblox
Content: Research reveals sophisticated geographic cloaking technique targeting residential IPs...

Article 2:
Title: "General Cybersecurity Tips for Small Businesses"
Source: Generic Blog
Content: Basic advice about passwords and antivirus software...

Evaluate each article and provide final recommendations on which to include."""

    result = agent.run(task)

    print(f"\n{result}")
    print(f"\nScored {len(agent.get_scored_articles())} articles")

    for article in agent.get_high_priority_articles():
        print(f"\nHIGH PRIORITY: {article.title}")
        print(f"  Score: {article.overall_score:.1f}")
        print(f"  Reasoning: {article.reasoning[:100]}...")
