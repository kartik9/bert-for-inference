"""
Quality Agent
Review, critique, and refine newsletter content for accuracy and quality
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.llm_client import LLMClient


@dataclass
class QualityIssue:
    """Quality issue found during review"""
    issue_type: str  # factual_error, unsupported_claim, style_violation, etc.
    severity: str  # critical, high, medium, low
    location: str  # where in the newsletter
    description: str
    suggestion: str


@dataclass
class QualityReport:
    """Complete quality assessment"""
    overall_score: float  # 0-10
    passed: bool
    issues: List[QualityIssue]
    strengths: List[str]
    revision_needed: bool
    approval_status: str  # approved, needs_revision, rejected


class QualityAgent(BaseAgent):
    """
    Quality Agent - Critic and QA specialist

    Capabilities:
    - Review for factual accuracy
    - Check for hallucinations
    - Verify sources and citations
    - Assess balance and coherence
    - Request revisions
    - Final approval
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any
    ):
        """
        Initialize Quality Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for reasoning (should use thinking model)
            config: Global configuration
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="quality",
            llm_client=llm_client,
            config=config,
            max_iterations=8
        )

        self.quality_reports: List[QualityReport] = []

    def _register_tools(self):
        """Register quality review tools"""

        # Review newsletter tool
        self.register_tool(
            name="review_newsletter",
            description="Perform comprehensive quality review of newsletter content. Checks factual accuracy, style consistency, and overall quality.",
            parameters={
                "type": "object",
                "properties": {
                    "newsletter_content": {
                        "type": "string",
                        "description": "Complete newsletter markdown content"
                    },
                    "source_articles": {
                        "type": "string",
                        "description": "JSON string of source articles for fact-checking"
                    }
                },
                "required": ["newsletter_content"],
                "additionalProperties": False
            },
            function=self._review_newsletter_tool
        )

        # Review single item
        self.register_tool(
            name="review_item",
            description="Review a single newsletter item for accuracy and quality",
            parameters={
                "type": "object",
                "properties": {
                    "item_content": {
                        "type": "string",
                        "description": "Newsletter item markdown"
                    },
                    "source_article": {
                        "type": "string",
                        "description": "Original article content"
                    },
                    "source_url": {
                        "type": "string",
                        "description": "Source article URL"
                    }
                },
                "required": ["item_content", "source_article"],
                "additionalProperties": False
            },
            function=self._review_item_tool
        )

        # Check factual claim
        self.register_tool(
            name="verify_claim",
            description="Verify a specific factual claim against source material",
            parameters={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "Claim to verify"
                    },
                    "source_text": {
                        "type": "string",
                        "description": "Source text to check against"
                    }
                },
                "required": ["claim", "source_text"],
                "additionalProperties": False
            },
            function=self._verify_claim_tool
        )

    def _review_newsletter_tool(
        self,
        newsletter_content: str,
        source_articles: str = "[]"
    ) -> Dict[str, Any]:
        """Comprehensive newsletter review using LLM"""
        try:
            # Parse source articles
            try:
                sources = json.loads(source_articles)
            except:
                sources = []

            # Build review prompt
            review_prompt = f"""Perform comprehensive quality review of this Trust & Safety newsletter.

NEWSLETTER CONTENT:
{newsletter_content[:4000]}

SOURCE ARTICLES:
{json.dumps(sources, indent=2)[:2000] if sources else "Not provided"}

REVIEW CRITERIA:

1. **Factual Accuracy** (Critical)
   - Are all claims supported by source articles?
   - Any hallucinated details or speculation?
   - Numbers/dates/names correct?
   - No contradictions with source material?

2. **Source Quality** (High)
   - All links functional and properly attributed?
   - Mix of authoritative sources?
   - No questionable/low-credibility sources?
   - Citations formatted correctly?

3. **Coverage Balance** (Medium)
   - Mix of threat types (fraud, malvertising, deepfakes)?
   - Geographic diversity?
   - Both tactical (specific incidents) and strategic (trends)?

4. **Clarity & Coherence** (Medium)
   - Summaries clear and self-contained?
   - Consistent terminology?
   - Executive-friendly language?
   - No jargon without explanation?

5. **Actionability** (Medium)
   - At least 30% of items have clear Microsoft implications?
   - Recommended actions specific and feasible?

6. **Style Consistency** (Low)
   - Follows style guide?
   - Consistent emoji usage?
   - Appropriate tone?

QUALITY THRESHOLDS:
- Critical issues: Factual errors, unsupported claims
- High issues: Missing sources, poor credibility
- Medium issues: Style violations, balance problems
- Low issues: Minor formatting, word choice

Respond in JSON format:
{{
  "overall_score": <0-10>,
  "passed": <boolean>,
  "issues": [
    {{
      "type": "<issue_type>",
      "severity": "<critical|high|medium|low>",
      "location": "<where in newsletter>",
      "description": "<detailed description>",
      "suggestion": "<how to fix>"
    }}
  ],
  "strengths": ["<strength1>", "<strength2>"],
  "revision_needed": <boolean>,
  "approval_status": "<approved|needs_revision|rejected>",
  "summary_feedback": "<overall assessment>"
}}"""

            # Generate review
            response = self.llm_client.generate(
                input=review_prompt,
                instructions="You are a senior editor ensuring quality and accuracy. Be thorough and objective.",
                temperature=0.2  # Low temperature for consistent quality standards
            )

            # Parse JSON
            try:
                review_data = json.loads(response.text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    review_data = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not parse review response")

            # Create quality issues
            issues = [
                QualityIssue(
                    issue_type=issue.get("type", "unknown"),
                    severity=issue.get("severity", "medium"),
                    location=issue.get("location", ""),
                    description=issue.get("description", ""),
                    suggestion=issue.get("suggestion", "")
                )
                for issue in review_data.get("issues", [])
            ]

            # Create quality report
            report = QualityReport(
                overall_score=review_data.get("overall_score", 5.0),
                passed=review_data.get("passed", False),
                issues=issues,
                strengths=review_data.get("strengths", []),
                revision_needed=review_data.get("revision_needed", False),
                approval_status=review_data.get("approval_status", "needs_revision")
            )

            # Store report
            self.quality_reports.append(report)

            # Count critical issues
            critical_issues = [i for i in issues if i.severity == "critical"]

            return {
                "success": True,
                "overall_score": report.overall_score,
                "passed": report.passed,
                "approval_status": report.approval_status,
                "total_issues": len(issues),
                "critical_issues": len(critical_issues),
                "revision_needed": report.revision_needed,
                "feedback_summary": review_data.get("summary_feedback", "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _review_item_tool(
        self,
        item_content: str,
        source_article: str,
        source_url: str = ""
    ) -> Dict[str, Any]:
        """Review single newsletter item"""
        try:
            review_prompt = f"""Review this newsletter item for accuracy.

NEWSLETTER ITEM:
{item_content}

SOURCE ARTICLE:
{source_article[:2000]}
URL: {source_url}

Check:
1. All facts are supported by source
2. No hallucinated details
3. Numbers and dates match source
4. Proper attribution
5. Style guide compliance

Respond with JSON:
{{
  "accurate": <boolean>,
  "issues": [{{\"description\": \"...\", \"severity\": \"...\"}}],
  "suggestions": [\"...\"]
}}"""

            response = self.llm_client.generate(
                input=review_prompt,
                instructions="You are fact-checking for accuracy. Be precise.",
                temperature=0.1
            )

            try:
                result = json.loads(response.text)
            except:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    result = {"accurate": False, "issues": [], "suggestions": []}

            return {
                "success": True,
                "accurate": result.get("accurate", False),
                "issues": result.get("issues", []),
                "suggestions": result.get("suggestions", [])
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _verify_claim_tool(
        self,
        claim: str,
        source_text: str
    ) -> Dict[str, Any]:
        """Verify specific claim"""
        try:
            # Simple LLM-based verification
            verify_prompt = f"""Is this claim supported by the source text?

CLAIM: {claim}

SOURCE TEXT:
{source_text[:1500]}

Respond with JSON:
{{
  "supported": <boolean>,
  "explanation": "<why or why not>",
  "supporting_quote": "<relevant quote from source or null>"
}}"""

            response = self.llm_client.generate(
                input=verify_prompt,
                temperature=0.1
            )

            try:
                result = json.loads(response.text)
            except:
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    result = {"supported": False, "explanation": "Parse error"}

            return {
                "success": True,
                "claim_supported": result.get("supported", False),
                "explanation": result.get("explanation", ""),
                "supporting_quote": result.get("supporting_quote")
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_system_prompt(self) -> str:
        """System prompt for Quality Agent"""
        return """You are a senior editor ensuring quality and accuracy for Microsoft's Trust & Safety newsletter.

Your role is the final quality gate before publication. You must be thorough, objective, and maintain high standards.

CRITICAL RESPONSIBILITIES:

1. **Prevent Misinformation**
   - Every claim must be supported by source material
   - No hallucinations or speculation
   - Numbers, dates, names must be exact
   - Flag any unsupported statements immediately

2. **Verify Sources**
   - Check all URLs are correct and attributed
   - Ensure sources are credible and authoritative
   - Flag any questionable sources
   - Verify proper citation format

3. **Maintain Quality Standards**
   - Executive-appropriate language
   - Clear, coherent narrative
   - Balanced coverage across threat types
   - Actionable insights for team

4. **Enforce Style Guide**
   - Consistent tone and formatting
   - Professional but accessible
   - Technical accuracy without jargon
   - Proper use of emojis and structure

APPROVAL CRITERIA:

**APPROVED:**
- No critical or high-severity issues
- All facts verified against sources
- Balanced, coherent coverage
- Clear actionability for team
- Style guide compliant

**NEEDS REVISION:**
- Medium-severity issues present
- Minor factual corrections needed
- Style improvements needed
- Balance or coherence issues

**REJECTED:**
- Critical factual errors
- Unsupported claims or hallucinations
- Poor source quality
- Missing key information

TOOLS:
- review_newsletter: Full newsletter quality review
- review_item: Single item fact-check
- verify_claim: Verify specific claim

Be rigorous but fair. The goal is accuracy and quality, not perfection."""

    def get_latest_report(self) -> Optional[QualityReport]:
        """Get most recent quality report"""
        return self.quality_reports[-1] if self.quality_reports else None

    def get_all_reports(self) -> List[QualityReport]:
        """Get all quality reports"""
        return self.quality_reports


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="quality")

    agent = QualityAgent(
        agent_name="quality-1",
        llm_client=llm_client,
        config=config
    )

    task = """Review this newsletter for quality and accuracy:

NEWSLETTER:
---
### 🚨 **Parked Domains Now Primary Malvertising Vector**
**Published:** December 16, 2025 (Infoblox)

**What Happened:**
Over 90% of parked domain visitors are now redirected to scams and malware using sophisticated geographic cloaking.

**Key Details:**
- Attackers use device fingerprinting to show clean content to VPNs
- Example: scotaibank[.]com redirects mobile users to scams
- Traffic sold through multiple affiliate networks

**Why It Matters:**
This represents a novel evasion technique that Aurora cannot currently detect. Recommend implementing residential IP testing infrastructure.

SOURCE ARTICLE:
Title: Parked Domains Become Weapons
Content: Infoblox researchers discovered 90% of parked domain visitors redirected to scams...
[Full article would be here]

Perform comprehensive quality review and decide if this can be published."""

    result = agent.run(task)

    print(f"\n{result}")

    report = agent.get_latest_report()
    if report:
        print(f"\nQuality Report:")
        print(f"  Score: {report.overall_score}/10")
        print(f"  Status: {report.approval_status}")
        print(f"  Issues: {len(report.issues)}")
        for issue in report.issues:
            print(f"    - [{issue.severity}] {issue.description}")
