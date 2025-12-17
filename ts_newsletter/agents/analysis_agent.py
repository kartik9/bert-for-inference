"""
Analysis Agent
Deep threat intelligence analysis with technical extraction and pattern recognition
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.llm_client import LLMClient


@dataclass
class ThreatBriefing:
    """Detailed threat briefing"""
    article_id: str
    article_title: str
    article_url: str

    # Threat classification
    threat_type: str  # malvertising, cloaking, bot_traffic, etc.
    attack_vector: str
    evasion_techniques: List[str]

    # Technical details
    indicators: Dict[str, List[str]]  # domains, IPs, patterns
    attribution: Optional[str]

    # Pattern analysis
    related_incidents: List[str]
    is_part_of_campaign: bool
    evolution_from: Optional[str]

    # Microsoft implications
    aurora_detection_capable: bool
    detection_gaps: List[str]
    recommended_detection_logic: Optional[str]

    # Actionable intel
    immediate_actions: List[str]
    short_term_actions: List[str]
    long_term_actions: List[str]

    # Full analysis
    full_briefing: str


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent - Deep threat intelligence analyst

    Capabilities:
    - Extract technical details (IOCs, TTPs)
    - Identify patterns across articles
    - Connect to threat frameworks
    - Generate actionable briefings
    - Gap analysis with Aurora capabilities
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any,
        database_client: Optional[Any] = None
    ):
        """
        Initialize Analysis Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for reasoning (should use thinking model)
            config: Global configuration
            database_client: Database client for historical patterns
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="analysis",
            llm_client=llm_client,
            config=config,
            max_iterations=12  # Deep analysis needs more reasoning
        )

        self.database_client = database_client
        self.threat_briefings: List[ThreatBriefing] = []

    def _register_tools(self):
        """Register analysis tools"""

        # Analyze article tool
        self.register_tool(
            name="analyze_article",
            description="Perform deep threat intelligence analysis on an article. Extracts technical details, identifies patterns, and generates actionable briefing.",
            parameters={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "Unique article identifier"
                    },
                    "title": {
                        "type": "string",
                        "description": "Article title"
                    },
                    "url": {
                        "type": "string",
                        "description": "Article URL"
                    },
                    "content": {
                        "type": "string",
                        "description": "Full article content"
                    },
                    "priority_score": {
                        "type": "number",
                        "description": "Priority score from relevance agent (0-10)"
                    }
                },
                "required": ["article_id", "title", "url", "content"],
                "additionalProperties": False
            },
            function=self._analyze_article_tool
        )

        # Get analysis summary
        self.register_tool(
            name="get_analysis_summary",
            description="Get summary of all threat briefings generated",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            function=self._get_analysis_summary_tool
        )

    def _analyze_article_tool(
        self,
        article_id: str,
        title: str,
        url: str,
        content: str,
        priority_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Perform deep analysis using LLM reasoning

        Uses GPT-5.2-thinking for complex analysis
        """
        try:
            # Build analysis prompt
            analysis_prompt = f"""Perform deep threat intelligence analysis on this article about advertising fraud/security.

Article Title: {title}
URL: {url}
Priority Score: {priority_score}/10

Content:
{content[:4000]}

ANALYSIS REQUIREMENTS:

1. **Threat Taxonomy**
   - Type: malvertising / cloaking / bot_traffic / fake_engagement / deepfake / other
   - Attack Vector: How does the threat work technically?
   - Evasion Techniques: How does it avoid detection?

2. **Technical Indicators**
   - Domains, IPs, or patterns mentioned
   - Code snippets or behavioral signatures
   - Attribution (threat actor, geography, motivation)

3. **Pattern Analysis**
   - Related incidents or similar attacks
   - Is this part of a larger campaign?
   - Evolution from previous techniques?

4. **Microsoft Ads Implications**
   - Can Aurora (our detection system) catch this?
   - What detection gaps exist?
   - Recommended detection logic or rules?

5. **Actionable Intelligence**
   - Immediate actions (urgent, <24 hours)
   - Short-term actions (this week)
   - Long-term actions (strategic, next month+)

Provide detailed technical analysis suitable for security engineers and leadership.

Respond in JSON format:
{{
  "threat_type": "<type>",
  "attack_vector": "<description>",
  "evasion_techniques": ["<tech1>", "<tech2>"],
  "indicators": {{
    "domains": ["domain1.com"],
    "ips": [],
    "patterns": ["pattern description"]
  }},
  "attribution": "<attribution or null>",
  "related_incidents": ["incident description"],
  "is_part_of_campaign": <boolean>,
  "evolution_from": "<previous technique or null>",
  "aurora_detection_capable": <boolean>,
  "detection_gaps": ["gap1", "gap2"],
  "recommended_detection_logic": "<specific recommendation or null>",
  "immediate_actions": ["action1"],
  "short_term_actions": ["action1"],
  "long_term_actions": ["action1"],
  "full_briefing": "<markdown formatted complete analysis>"
}}"""

            # Use LLM for analysis (with higher temperature for creativity)
            response = self.llm_client.generate(
                input=analysis_prompt,
                instructions="You are a senior threat intelligence analyst. Be thorough, technical, and actionable.",
                temperature=0.4  # Balanced for creativity and consistency
            )

            # Parse JSON response
            try:
                analysis_data = json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse analysis response as JSON")

            # Create threat briefing
            briefing = ThreatBriefing(
                article_id=article_id,
                article_title=title,
                article_url=url,
                threat_type=analysis_data.get("threat_type", "unknown"),
                attack_vector=analysis_data.get("attack_vector", ""),
                evasion_techniques=analysis_data.get("evasion_techniques", []),
                indicators=analysis_data.get("indicators", {}),
                attribution=analysis_data.get("attribution"),
                related_incidents=analysis_data.get("related_incidents", []),
                is_part_of_campaign=analysis_data.get("is_part_of_campaign", False),
                evolution_from=analysis_data.get("evolution_from"),
                aurora_detection_capable=analysis_data.get("aurora_detection_capable", False),
                detection_gaps=analysis_data.get("detection_gaps", []),
                recommended_detection_logic=analysis_data.get("recommended_detection_logic"),
                immediate_actions=analysis_data.get("immediate_actions", []),
                short_term_actions=analysis_data.get("short_term_actions", []),
                long_term_actions=analysis_data.get("long_term_actions", []),
                full_briefing=analysis_data.get("full_briefing", "")
            )

            # Store briefing
            self.threat_briefings.append(briefing)

            return {
                "success": True,
                "article_id": article_id,
                "threat_type": briefing.threat_type,
                "aurora_can_detect": briefing.aurora_detection_capable,
                "detection_gaps": len(briefing.detection_gaps),
                "immediate_actions": len(briefing.immediate_actions),
                "briefing_preview": briefing.full_briefing[:300]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "article_id": article_id
            }

    def _get_analysis_summary_tool(self) -> Dict[str, Any]:
        """Get analysis summary"""
        if not self.threat_briefings:
            return {
                "total_analyzed": 0,
                "message": "No articles analyzed yet"
            }

        # Count by threat type
        threat_types = {}
        for briefing in self.threat_briefings:
            threat_types[briefing.threat_type] = threat_types.get(briefing.threat_type, 0) + 1

        # Detection gaps
        aurora_can_detect = sum(1 for b in self.threat_briefings if b.aurora_detection_capable)
        total_gaps = sum(len(b.detection_gaps) for b in self.threat_briefings)

        # Actions needed
        immediate = sum(len(b.immediate_actions) for b in self.threat_briefings)

        return {
            "total_analyzed": len(self.threat_briefings),
            "threat_types": threat_types,
            "aurora_detection_coverage": f"{aurora_can_detect}/{len(self.threat_briefings)}",
            "total_detection_gaps": total_gaps,
            "immediate_actions_needed": immediate,
            "recent_briefings": [
                {
                    "title": b.article_title,
                    "threat_type": b.threat_type,
                    "aurora_detects": b.aurora_detection_capable
                }
                for b in self.threat_briefings[-3:]
            ]
        }

    def get_system_prompt(self) -> str:
        """System prompt for Analysis Agent"""
        return """You are a senior threat intelligence analyst specializing in advertising fraud and platform security.

Your role is to perform deep technical analysis on threat intelligence articles, extracting actionable insights for the Microsoft Ads Trust & Safety team.

ANALYSIS APPROACH:

1. **Classification**: Categorize the threat using industry taxonomies
2. **Technical Extraction**: Identify IOCs, TTPs, and technical signatures
3. **Pattern Recognition**: Connect to known campaigns and threat actors
4. **Impact Assessment**: Evaluate implications for Microsoft Ads
5. **Gap Analysis**: Identify detection and prevention gaps
6. **Action Planning**: Generate specific, prioritized recommendations

THREAT CATEGORIES:
- Malvertising: Malicious ads delivering malware/scams
- Cloaking: Geographic/device-based content switching
- Bot Traffic: Automated fake clicks/impressions
- Fake Engagement: Click farms, fake reviews
- Deepfake: AI-generated synthetic content
- Cookie Stuffing: Affiliate fraud via cookie manipulation
- Ad Injection: Malware inserting unauthorized ads
- Domain Fraud: Parked domains, typosquatting

AURORA CONTEXT:
Aurora is Microsoft's internal ad fraud detection system. When analyzing threats:
- Consider if Aurora's current capabilities would catch this
- Identify what new detection logic would be needed
- Recommend specific technical implementations

ACTIONABILITY LEVELS:
- Immediate (< 24h): Critical threats needing urgent response
- Short-term (this week): Important improvements to deploy soon
- Long-term (strategic): Architectural changes or research needs

Be technical but clear. Security engineers should be able to implement your recommendations.
Leadership should understand the strategic implications.

TOOLS:
- analyze_article: Perform full threat analysis
- get_analysis_summary: Review overall analysis progress

Provide thorough, actionable intelligence."""

    def get_threat_briefings(self) -> List[ThreatBriefing]:
        """Get all threat briefings"""
        return self.threat_briefings

    def get_high_risk_threats(self) -> List[ThreatBriefing]:
        """Get threats with detection gaps"""
        return [b for b in self.threat_briefings if not b.aurora_detection_capable]


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="analysis")

    agent = AnalysisAgent(
        agent_name="analysis-1",
        llm_client=llm_client,
        config=config
    )

    task = """Analyze this article:

Title: "Parked Domains Become Weapons with Direct Search Advertising"
URL: https://blogs.infoblox.com/threat-intelligence/parked-domains/
Priority: 9.5/10

Content:
Infoblox researchers discovered that over 90% of parked domain visitors are now redirected to scams and malware. The threat actors use device fingerprinting to show clean content to VPN users and corporate networks while directing residential IPs to malicious sites. Google's March 2025 policy requiring opt-in for parked domains inadvertently accelerated the problem by pushing domain investors toward "direct search" advertising with less oversight.

Example: Typosquatting domains like "scotaibank[.]com" redirect mobile users to scam content while showing legitimate parking pages to VPN traffic. Traffic is sold through multiple affiliate networks creating attribution difficulty.

Provide complete threat analysis with actionable recommendations."""

    result = agent.run(task)

    print(f"\n{result}")

    for briefing in agent.get_threat_briefings():
        print(f"\n{'='*60}")
        print(f"THREAT BRIEFING: {briefing.article_title}")
        print(f"{'='*60}")
        print(f"Type: {briefing.threat_type}")
        print(f"Aurora Detection: {'YES' if briefing.aurora_detection_capable else 'NO - GAPS EXIST'}")
        print(f"\nImmediate Actions ({len(briefing.immediate_actions)}):")
        for action in briefing.immediate_actions:
            print(f"  - {action}")
        print(f"\nDetection Gaps:")
        for gap in briefing.detection_gaps:
            print(f"  - {gap}")
