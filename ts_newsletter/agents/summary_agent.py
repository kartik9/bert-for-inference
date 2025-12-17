"""
Summary Agent
Newsletter content generation with consistent style and formatting
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.llm_client import LLMClient


@dataclass
class NewsletterItem:
    """Single newsletter item"""
    article_id: str
    article_url: str

    # Content
    headline: str
    emoji: str
    published_date: str
    source_name: str
    what_happened: str  # 2-3 sentence overview
    key_details: List[str]  # Bullet points
    why_it_matters: str  # 2-3 sentences on implications
    source_attribution: str  # Link with title

    # Metadata
    word_count: int
    priority_level: str


class SummaryAgent(BaseAgent):
    """
    Summary Agent - Newsletter content generator

    Capabilities:
    - Generate executive-friendly summaries
    - Maintain consistent tone and style
    - Create attention-grabbing headlines
    - Format for newsletter template
    - Add proper citations
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any
    ):
        """
        Initialize Summary Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for generation
            config: Global configuration
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="summary",
            llm_client=llm_client,
            config=config,
            max_iterations=10
        )

        self.newsletter_items: List[NewsletterItem] = []

    def _register_tools(self):
        """Register summary generation tools"""

        # Generate summary tool
        self.register_tool(
            name="generate_summary",
            description="Generate a newsletter-ready summary for an article. Creates headline, overview, key details, and implications following the style guide.",
            parameters={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "Unique article identifier"
                    },
                    "article_url": {
                        "type": "string",
                        "description": "Article URL"
                    },
                    "title": {
                        "type": "string",
                        "description": "Original article title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content or key excerpts"
                    },
                    "threat_briefing": {
                        "type": "string",
                        "description": "Threat analysis briefing from Analysis Agent"
                    },
                    "priority_level": {
                        "type": "string",
                        "description": "Priority level: HIGH, MEDIUM, or LOW"
                    },
                    "source_name": {
                        "type": "string",
                        "description": "Source publication name"
                    },
                    "published_date": {
                        "type": "string",
                        "description": "Publication date"
                    }
                },
                "required": ["article_id", "article_url", "title", "content"],
                "additionalProperties": False
            },
            function=self._generate_summary_tool
        )

        # Format newsletter section
        self.register_tool(
            name="format_newsletter",
            description="Format all summaries into complete newsletter markdown",
            parameters={
                "type": "object",
                "properties": {
                    "week_ending": {
                        "type": "string",
                        "description": "Week ending date (e.g., 'December 17, 2025')"
                    },
                    "include_patterns": {
                        "type": "boolean",
                        "description": "Include 'Emerging Patterns' section",
                        "default": True
                    }
                },
                "required": ["week_ending"],
                "additionalProperties": False
            },
            function=self._format_newsletter_tool
        )

        # Get summary count
        self.register_tool(
            name="get_summary_status",
            description="Get count of summaries generated",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            function=self._get_summary_status_tool
        )

    def _generate_summary_tool(
        self,
        article_id: str,
        article_url: str,
        title: str,
        content: str,
        threat_briefing: str = "",
        priority_level: str = "MEDIUM",
        source_name: str = "",
        published_date: str = ""
    ) -> Dict[str, Any]:
        """Generate newsletter summary using LLM"""
        try:
            # Determine emoji based on priority/content
            emoji_map = {
                "HIGH": "🚨",
                "MEDIUM": "📊",
                "LOW": "ℹ️"
            }
            base_emoji = emoji_map.get(priority_level, "📰")

            # Build generation prompt
            summary_prompt = f"""Generate a newsletter summary for this article.

Article Title: {title}
Source: {source_name}
Published: {published_date}
Priority: {priority_level}
URL: {article_url}

Content:
{content[:3000]}

Threat Briefing:
{threat_briefing[:2000] if threat_briefing else "N/A"}

STYLE REQUIREMENTS:

**Format:**
### [Emoji] **[Attention-grabbing headline]**
**Published:** [Date] ([Source])

**What Happened:**
[2-3 sentence overview - lead with impact, then mechanism]

**Key Details:**
- [Bullet: specific technical detail]
- [Bullet: scale/scope with numbers]
- [Bullet: novel element or evolution]
- [Bullet: attribution if known]

**Why It Matters:**
[2-3 sentences on implications for Microsoft Ads, connection to Aurora capabilities, or strategic importance. Executive-friendly language.]

**Source:** [Link with title]

GUIDELINES:
- Professional but accessible (executive-friendly)
- Lead with "what" and "why it matters"
- Include specific numbers/metrics when available
- Avoid jargon without context
- Active voice, present tense for ongoing threats
- Flag actionable items clearly
- Total word count: 150-250 words
- Make headline compelling but accurate

Respond in JSON format:
{{
  "headline": "<headline without emoji>",
  "emoji": "<emoji>",
  "what_happened": "<2-3 sentences>",
  "key_details": ["<detail1>", "<detail2>", "<detail3>"],
  "why_it_matters": "<2-3 sentences>",
  "recommended_emoji": "<better emoji if needed>"
}}"""

            # Generate summary
            response = self.llm_client.generate(
                input=summary_prompt,
                instructions="You are an expert technical writer for Microsoft's Trust & Safety team. Be concise, accurate, and compelling.",
                temperature=0.6  # Balanced for creativity and consistency
            )

            # Parse JSON
            try:
                summary_data = json.loads(response.text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    summary_data = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse summary response")

            # Use recommended emoji if provided
            final_emoji = summary_data.get("recommended_emoji", summary_data.get("emoji", base_emoji))

            # Calculate word count
            word_count = (
                len(summary_data["what_happened"].split()) +
                sum(len(detail.split()) for detail in summary_data["key_details"]) +
                len(summary_data["why_it_matters"].split())
            )

            # Create newsletter item
            item = NewsletterItem(
                article_id=article_id,
                article_url=article_url,
                headline=summary_data["headline"],
                emoji=final_emoji,
                published_date=published_date,
                source_name=source_name,
                what_happened=summary_data["what_happened"],
                key_details=summary_data["key_details"],
                why_it_matters=summary_data["why_it_matters"],
                source_attribution=f"[{source_name}]({article_url})" if source_name else f"[Source]({article_url})",
                word_count=word_count,
                priority_level=priority_level
            )

            # Store item
            self.newsletter_items.append(item)

            return {
                "success": True,
                "article_id": article_id,
                "headline": item.headline,
                "word_count": word_count,
                "emoji": final_emoji
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "article_id": article_id
            }

    def _format_newsletter_tool(
        self,
        week_ending: str,
        include_patterns: bool = True
    ) -> Dict[str, Any]:
        """Format complete newsletter"""
        try:
            # Sort items by priority
            priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            sorted_items = sorted(
                self.newsletter_items,
                key=lambda x: priority_order.get(x.priority_level, 3)
            )

            # Build newsletter markdown
            newsletter = f"""# What's Happening in Trust & Safety
### Week Ending {week_ending}

"""

            for item in sorted_items:
                newsletter += f"""---

### {item.emoji} **{item.headline}**
**Published:** {item.published_date} ({item.source_name})

**What Happened:**
{item.what_happened}

**Key Details:**
"""
                for detail in item.key_details:
                    newsletter += f"- {detail}\n"

                newsletter += f"""
**Why It Matters:**
{item.why_it_matters}

**Source:** {item.source_attribution}

"""

            if include_patterns:
                newsletter += """---

## Emerging Patterns to Watch

"""
                # This would ideally be generated by analyzing themes across articles
                # For now, placeholder
                newsletter += """*[Emerging patterns section would be generated based on cross-article analysis]*

"""

            newsletter += f"""---

*Generated by: Ads Trust & Safety Intelligence Team*
*Total articles: {len(sorted_items)}*
"""

            return {
                "success": True,
                "newsletter": newsletter,
                "item_count": len(sorted_items),
                "total_words": sum(item.word_count for item in sorted_items)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_summary_status_tool(self) -> Dict[str, Any]:
        """Get summary generation status"""
        return {
            "total_summaries": len(self.newsletter_items),
            "high_priority": len([i for i in self.newsletter_items if i.priority_level == "HIGH"]),
            "medium_priority": len([i for i in self.newsletter_items if i.priority_level == "MEDIUM"]),
            "low_priority": len([i for i in self.newsletter_items if i.priority_level == "LOW"]),
            "total_words": sum(i.word_count for i in self.newsletter_items),
            "recent_headlines": [i.headline for i in self.newsletter_items[-3:]]
        }

    def get_system_prompt(self) -> str:
        """System prompt for Summary Agent"""
        return """You are an expert technical writer for Microsoft's Trust & Safety team.

Your role is to transform threat intelligence into compelling, actionable newsletter content for both technical and executive audiences.

AUDIENCE:
- Security engineers who need technical details
- Product managers who need strategic implications
- Leadership who need high-level awareness
- Cross-org partners who need context

STYLE GUIDE:

**Tone:**
- Professional but accessible
- Authoritative without jargon
- Urgent when warranted, measured always
- Fact-focused, avoiding speculation

**Structure:**
- Lead with impact (what and why it matters)
- Support with specific details
- End with implications for Microsoft
- Always cite sources

**Language:**
- Active voice: "Attackers exploited" not "was exploited"
- Present tense for ongoing: "Campaign targets" not "targeted"
- Specific numbers: "$16B revenue" not "significant revenue"
- Clear terminology: Define specialized terms on first use

**Headlines:**
- Grab attention but don't sensationalize
- Specific over generic: "Parked Domains Become Primary Malvertising Vector" vs "New Threat Discovered"
- Include scale/impact when relevant
- Avoid clickbait

**Word Economy:**
- Target: 150-250 words per item
- Every word must earn its place
- Prefer concrete details over abstract concepts
- One idea per bullet point

QUALITY CHECKS:
- ✓ All claims backed by article content
- ✓ Numbers and dates accurate
- ✓ Technical details correct
- ✓ Sources properly attributed
- ✓ Implications clearly stated
- ✓ No speculation presented as fact

TOOLS:
- generate_summary: Create newsletter item for one article
- format_newsletter: Combine all items into full newsletter
- get_summary_status: Check progress

Generate content that is immediately useful and actionable."""

    def get_newsletter_items(self) -> List[NewsletterItem]:
        """Get all newsletter items"""
        return self.newsletter_items

    def get_formatted_newsletter(self, week_ending: str) -> str:
        """Get complete formatted newsletter"""
        result = self._format_newsletter_tool(week_ending=week_ending)
        return result.get("newsletter", "")


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="summary")

    agent = SummaryAgent(
        agent_name="summary-1",
        llm_client=llm_client,
        config=config
    )

    task = """Generate newsletter summaries for these analyzed articles:

Article 1:
Title: Parked Domains Now Primary Malvertising Vector
URL: https://blogs.infoblox.com/threat-intelligence/parked-domains/
Source: Infoblox Threat Intelligence
Published: December 16, 2025
Priority: HIGH
Content: Over 90% of parked domain visitors redirected to scams using geographic cloaking...
Threat Briefing: Novel evasion technique, Aurora cannot currently detect, recommend residential IP testing...

Article 2:
Title: Meta's China Ad Fraud: $16B Revenue
URL: https://fortune.com/meta-ad-fraud/
Source: Fortune
Published: December 16, 2025
Priority: HIGH
Content: Former integrity chief criticizes revenue-based enforcement caps...
Threat Briefing: Systemic issue with platform incentives, no immediate technical action needed...

Generate summaries for both articles, then format the complete newsletter for week ending December 17, 2025."""

    result = agent.run(task)

    print(f"\n{result}")

    # Get formatted newsletter
    newsletter = agent.get_formatted_newsletter("December 17, 2025")
    print(f"\n{'='*60}")
    print(newsletter)
