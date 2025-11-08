"""
AI Safety Analysis Agent
Uses advanced AI (GPT-4/Claude) to perform deep trust and safety analysis of URLs
"""

import os
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class SafetyAnalysisAgent:
    """AI-powered URL safety analysis agent"""

    def __init__(self):
        """Initialize AI client based on available API keys"""
        self.openai_client = None
        self.anthropic_client = None
        self.model = None

        # Try OpenAI first
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o"  # Latest GPT-4o model (use gpt-5 when available)
            logger.info("Initialized with OpenAI GPT-4o")

        # Fall back to Anthropic
        elif os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-opus-20240229"  # or claude-3-sonnet
            logger.info("Initialized with Anthropic Claude")

        else:
            logger.warning("No AI API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

    def is_configured(self) -> bool:
        """Check if AI client is properly configured"""
        return self.openai_client is not None or self.anthropic_client is not None

    async def create_investigation_plan(
        self, url: str, technical_data: Dict[str, Any]
    ) -> List[str]:
        """
        Create a structured investigation plan based on technical analysis
        """
        if not self.is_configured():
            return [
                "Technical URL analysis",
                "Risk indicator assessment",
                "Content analysis",
                "Final verdict generation"
            ]

        prompt = f"""You are a trust and safety expert analyzing URLs for an ad platform.

URL to investigate: {url}

Technical analysis findings:
{json.dumps(technical_data, indent=2)}

Create a structured investigation plan with 5-8 specific steps to thoroughly analyze this URL for:
- Phishing attempts
- Malware distribution
- Scam operations
- Fraudulent advertising
- Brand impersonation
- Other trust & safety concerns

Return ONLY a JSON array of investigation steps as strings. Example:
["Step 1: Analyze domain registration patterns", "Step 2: Check content for social engineering", ...]
"""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a trust and safety expert. Respond only with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                plan_text = response.choices[0].message.content.strip()
                # Extract JSON from response
                if plan_text.startswith("```"):
                    plan_text = plan_text.split("```")[1].replace("json", "").strip()
                return json.loads(plan_text)

            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                plan_text = response.content[0].text.strip()
                if plan_text.startswith("```"):
                    plan_text = plan_text.split("```")[1].replace("json", "").strip()
                return json.loads(plan_text)

        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            # Return default plan
            return [
                "Analyze domain and hosting infrastructure",
                "Examine URL structure and patterns",
                "Investigate SSL/TLS certificate validity",
                "Review content for malicious elements",
                "Check for phishing indicators",
                "Assess overall risk level"
            ]

    async def investigate_url(
        self,
        url: str,
        technical_data: Dict[str, Any],
        investigation_plan: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform deep investigation with streaming updates
        Yields progress updates with AI reasoning
        """

        if not self.is_configured():
            yield {
                "type": "error",
                "message": "AI agent not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            }
            return

        # Build comprehensive analysis prompt
        prompt = self._build_investigation_prompt(url, technical_data, investigation_plan)

        try:
            progress = 50
            step_increment = 40 // len(investigation_plan)

            if self.openai_client:
                # Use streaming with OpenAI
                stream = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=3000,
                    stream=True
                )

                collected_text = ""
                current_section = "reasoning"

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        collected_text += content

                        # Detect section changes
                        if "INVESTIGATION STEP:" in collected_text:
                            progress = min(progress + step_increment, 85)
                            yield {
                                "type": "progress",
                                "message": "Analyzing next investigation step...",
                                "progress": progress
                            }

                        yield {
                            "type": "reasoning",
                            "content": content,
                            "section": current_section
                        }

            elif self.anthropic_client:
                # Use streaming with Anthropic
                async with self.anthropic_client.messages.stream(
                    model=self.model,
                    max_tokens=3000,
                    messages=[{"role": "user", "content": prompt}],
                    system=self._get_system_prompt()
                ) as stream:
                    collected_text = ""

                    async for text in stream.text_stream:
                        collected_text += text

                        if "INVESTIGATION STEP:" in collected_text:
                            progress = min(progress + step_increment, 85)
                            yield {
                                "type": "progress",
                                "message": "Analyzing next investigation step...",
                                "progress": progress
                            }

                        yield {
                            "type": "reasoning",
                            "content": text
                        }

        except Exception as e:
            logger.error(f"Investigation error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Investigation error: {str(e)}"
            }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """You are an expert Trust and Safety analyst working for a major advertising platform.

Your expertise includes:
- Identifying phishing attempts and brand impersonation
- Detecting malware distribution sites
- Recognizing scam operations and fraudulent schemes
- Understanding ad fraud techniques
- Analyzing suspicious domain patterns
- Evaluating SSL/TLS security issues
- Content analysis for malicious elements

When analyzing URLs:
1. Think critically and systematically through each investigation step
2. Consider multiple threat vectors
3. Cite specific evidence from the technical data
4. Explain your reasoning clearly
5. Be thorough but concise
6. Assign risk levels with clear justification

For each investigation step, structure your analysis as:

INVESTIGATION STEP: [Step name]
FINDINGS: [What you found]
EVIDENCE: [Specific data points]
RISK ASSESSMENT: [Risk level and reasoning]

After all steps, provide your thinking process in natural paragraphs showing how you arrived at your conclusions."""

    def _build_investigation_prompt(
        self,
        url: str,
        technical_data: Dict[str, Any],
        investigation_plan: List[str]
    ) -> str:
        """Build comprehensive investigation prompt"""

        # Summarize key technical findings
        risk_indicators = technical_data.get("risk_indicators", [])
        url_structure = technical_data.get("url_structure", {})
        ssl_info = technical_data.get("ssl_info", {})
        content_analysis = technical_data.get("content_analysis", {})
        web_reputation = technical_data.get("web_reputation", {})

        prompt = f"""Conduct a comprehensive trust and safety investigation of the following URL:

URL: {url}

=== TECHNICAL ANALYSIS DATA ===

URL STRUCTURE:
- Domain: {url_structure.get('fqdn', 'N/A')}
- Scheme: {url_structure.get('scheme', 'N/A')}
- Uses IP Address: {url_structure.get('has_ip', False)}
- URL Length: {url_structure.get('url_length', 0)} characters
- Suspicious Patterns: {', '.join(url_structure.get('suspicious_patterns', [])) or 'None detected'}

SSL/TLS INFORMATION:
- Has Valid SSL: {ssl_info.get('has_ssl', False)}
- Issuer: {ssl_info.get('issuer', {}).get('organizationName', 'N/A')}
- Valid Until: {ssl_info.get('valid_until', 'N/A')}

CONTENT ANALYSIS:
- Page Title: {content_analysis.get('title', 'N/A')}
- Forms Found: {content_analysis.get('forms_count', 0)}
- External Scripts: {content_analysis.get('external_scripts_count', 0)}
- iFrames: {content_analysis.get('iframes_count', 0)}
- Suspicious Content Patterns: {', '.join(content_analysis.get('suspicious_content', [])) or 'None'}

WEB REPUTATION ANALYSIS:
{self._format_web_reputation(web_reputation)}

AUTOMATED RISK INDICATORS:
{self._format_risk_indicators(risk_indicators)}

HTTP RESPONSE:
- Status Code: {technical_data.get('http_response', {}).get('status_code', 'N/A')}
- Redirects: {len(technical_data.get('http_response', {}).get('redirect_chain', []))}

=== INVESTIGATION PLAN ===

Follow these investigation steps systematically:

{self._format_investigation_plan(investigation_plan)}

=== INSTRUCTIONS ===

For EACH investigation step:
1. State what you're examining
2. Present your findings with specific evidence from the technical data
3. Explain the security implications
4. Assign a risk level for that aspect (LOW/MEDIUM/HIGH/CRITICAL)

Think out loud and show your reasoning process. Be thorough, cite specific evidence, and explain why certain indicators matter for trust and safety.

After completing all investigation steps, summarize your overall thinking process and how you arrived at your final assessment.

Begin your investigation now:"""

        return prompt

    def _format_risk_indicators(self, indicators: List[Dict[str, str]]) -> str:
        """Format risk indicators for prompt"""
        if not indicators:
            return "No automated risk indicators detected"

        formatted = []
        for idx, indicator in enumerate(indicators, 1):
            formatted.append(
                f"{idx}. [{indicator['type'].upper()}] {indicator['indicator']}\n"
                f"   Category: {indicator['category']}\n"
                f"   Risk: {indicator['risk']}"
            )
        return "\n".join(formatted)

    def _format_web_reputation(self, web_rep: Dict[str, Any]) -> str:
        """Format web reputation findings for prompt"""
        if not web_rep.get("search_performed"):
            return "Web reputation search not performed or not configured"

        scam_indicators = web_rep.get("scam_indicators", [])
        complaints = web_rep.get("user_complaints", [])
        reputation_score = web_rep.get("reputation_score", 70)
        risk_level = web_rep.get("risk_level", "UNKNOWN")
        total_results = web_rep.get("total_results_analyzed", 0)
        search_backend = web_rep.get("search_backend", "Unknown")

        lines = [
            f"- Search Backend: {search_backend}",
            f"- Total Search Results Analyzed: {total_results}",
            f"- Reputation Score: {reputation_score}/100",
            f"- Risk Level: {risk_level}",
            f"- Scam Reports Found: {len(scam_indicators)}",
            f"- User Complaints Found: {len(complaints)}",
        ]

        # Add details about high-severity scam reports
        if scam_indicators:
            high_severity = [s for s in scam_indicators if s.get('severity') == 'high']
            if high_severity:
                lines.append(f"\nHIGH-SEVERITY SCAM REPORTS ({len(high_severity)}):")
                for idx, scam in enumerate(high_severity[:3], 1):  # Show top 3
                    lines.append(f"  {idx}. {scam.get('title', 'No title')}")
                    lines.append(f"     Source: {scam.get('source', 'Unknown')}")
                    lines.append(f"     Keywords: {', '.join(scam.get('keywords', []))}")
                    snippet = scam.get('snippet', '')[:150]
                    if snippet:
                        lines.append(f"     Excerpt: {snippet}...")

        # Add user complaint samples
        if complaints:
            lines.append(f"\nUSER COMPLAINTS ({len(complaints)}):")
            for idx, complaint in enumerate(complaints[:3], 1):  # Show top 3
                lines.append(f"  {idx}. Type: {complaint.get('type', 'Unknown')}")
                lines.append(f"     Indicators: {', '.join(complaint.get('indicators', []))}")
                snippet = complaint.get('snippet', '')[:150]
                if snippet:
                    lines.append(f"     Excerpt: {snippet}...")

        return "\n".join(lines)

    def _format_investigation_plan(self, plan: List[str]) -> str:
        """Format investigation plan steps"""
        return "\n".join([f"{idx}. {step}" for idx, step in enumerate(plan, 1)])

    async def generate_report(
        self,
        url: str,
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate final comprehensive report with verdict
        """

        if not self.is_configured():
            return self._generate_fallback_report(url, technical_data)

        prompt = f"""Based on the complete investigation of URL: {url}

Technical Data Summary:
{json.dumps(technical_data, indent=2)}

Generate a comprehensive final report in JSON format with the following structure:

{{
  "verdict": "SAFE|SUSPICIOUS|MALICIOUS|BLOCKED",
  "confidence": 0-100,
  "primary_category": "phishing|malware|scam|fraud|legitimate|unknown",
  "secondary_categories": ["list", "of", "relevant", "categories"],
  "risk_score": 0-100,
  "summary": "2-3 sentence crisp summary of findings",
  "detailed_rationale": "Comprehensive explanation with specific evidence",
  "key_findings": [
    {{
      "finding": "Description of finding",
      "evidence": "Specific technical evidence",
      "severity": "low|medium|high|critical",
      "citation": "Reference to data source"
    }}
  ],
  "recommendations": [
    "Specific action item 1",
    "Specific action item 2"
  ],
  "threat_indicators": [
    "List of specific threat indicators found"
  ],
  "timestamp": "{datetime.utcnow().isoformat()}",
  "analyst_notes": "Additional context or observations"
}}

Ensure every finding has a clear citation to technical evidence. Be decisive in your verdict.
Return ONLY valid JSON, no markdown formatting."""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a trust and safety expert. Return only valid JSON."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    max_tokens=2000
                )
                report_text = response.choices[0].message.content.strip()

            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.5,
                    messages=[{"role": "user", "content": prompt}]
                )
                report_text = response.content[0].text.strip()

            # Clean and parse JSON
            if report_text.startswith("```"):
                report_text = report_text.split("```")[1].replace("json", "").strip()

            report = json.loads(report_text)
            return report

        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
            return self._generate_fallback_report(url, technical_data)

    def _generate_fallback_report(
        self, url: str, technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a basic report when AI is unavailable"""

        risk_indicators = technical_data.get("risk_indicators", [])
        high_risk = sum(1 for r in risk_indicators if r["type"] == "high")
        medium_risk = sum(1 for r in risk_indicators if r["type"] == "medium")

        # Simple scoring
        risk_score = (high_risk * 30) + (medium_risk * 15)
        risk_score = min(risk_score, 100)

        if risk_score >= 60:
            verdict = "MALICIOUS"
        elif risk_score >= 30:
            verdict = "SUSPICIOUS"
        else:
            verdict = "SAFE"

        return {
            "verdict": verdict,
            "confidence": 70,
            "primary_category": "unknown",
            "risk_score": risk_score,
            "summary": f"Automated analysis detected {high_risk} high-risk and {medium_risk} medium-risk indicators.",
            "detailed_rationale": "This is a basic automated analysis. For detailed AI-powered analysis, please configure an AI API key.",
            "key_findings": [
                {
                    "finding": r["indicator"],
                    "evidence": r["risk"],
                    "severity": r["type"],
                    "citation": r["category"]
                }
                for r in risk_indicators
            ],
            "recommendations": ["Manual review recommended", "Configure AI API for deep analysis"],
            "threat_indicators": [r["indicator"] for r in risk_indicators],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def answer_followup(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Answer follow-up questions about the URL analysis
        """

        if not self.is_configured():
            yield {
                "type": "response",
                "content": "AI agent not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
            }
            return

        # Build context-aware prompt
        context_summary = ""
        if previous_context:
            context_summary = f"""
Previous Analysis Context:
- URL: {url}
- Verdict: {previous_context.get('report', {}).get('verdict', 'N/A')}
- Risk Score: {previous_context.get('report', {}).get('risk_score', 'N/A')}
- Primary Category: {previous_context.get('report', {}).get('primary_category', 'N/A')}

Technical Data Available:
{json.dumps(previous_context.get('technical_data', {}), indent=2)[:1000]}...
"""

        prompt = f"""You are a trust and safety expert. A safety researcher is asking a follow-up question about a URL investigation.

{context_summary}

Researcher's Question: {question}

Provide a detailed, evidence-based answer. Reference specific technical findings when relevant. If you need additional information to answer comprehensively, indicate what would be helpful.

Answer:"""

        try:
            if self.openai_client:
                stream = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    stream=True
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield {
                            "type": "response",
                            "content": chunk.choices[0].delta.content
                        }

            elif self.anthropic_client:
                async with self.anthropic_client.messages.stream(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                    system=self._get_system_prompt()
                ) as stream:
                    async for text in stream.text_stream:
                        yield {
                            "type": "response",
                            "content": text
                        }

        except Exception as e:
            logger.error(f"Follow-up error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Error processing question: {str(e)}"
            }
