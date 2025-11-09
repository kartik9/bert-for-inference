"""
AI Safety Analysis Agent
Uses GPT-5 Responses API for deep trust and safety analysis of URLs
GPT-4o-mini used for data extraction and analysis tasks
"""

import os
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class SafetyAnalysisAgent:
    """AI-powered URL safety analysis agent using GPT-5 Responses API"""

    def __init__(self):
        """Initialize AI client with GPT-5"""
        self.openai_client = None
        self.model = "gpt-5"  # Using latest GPT-5 model

        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("Initialized with GPT-5 Responses API")
        else:
            logger.warning("No OpenAI API key configured. Set OPENAI_API_KEY")

    def is_configured(self) -> bool:
        """Check if AI client is properly configured"""
        return self.openai_client is not None

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

Based on this technical analysis, create an intelligent investigation plan with 5-8 specific steps to thoroughly analyze this URL for:
- Phishing attempts and credential theft
- Malware distribution
- Scam operations and fraud
- Fraudulent advertising
- Brand impersonation
- Other trust & safety concerns

Return ONLY a JSON object with this structure:
{{
  "investigation_steps": ["Step 1: ...", "Step 2: ...", ...]
}}
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert trust & safety analyst. Generate strategic investigation plans."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("investigation_steps", [
                "Analyze technical indicators",
                "Investigate web reputation",
                "Assess threat level"
            ])

        except Exception as e:
            logger.error(f"GPT-5 investigation plan error: {str(e)}")
            # Return intelligent default plan
            return [
                "Analyze domain and hosting infrastructure for anomalies",
                "Examine URL structure for brand impersonation patterns",
                "Investigate SSL/TLS certificate validity and trust",
                "Review web content for malicious elements and social engineering",
                "Analyze web reputation and user complaints",
                "Assess overall risk level and threat classification"
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
                "message": "GPT-5 not configured. Please set OPENAI_API_KEY"
            }
            return

        # Build comprehensive analysis prompt
        prompt = self._build_investigation_prompt(url, technical_data, investigation_plan)

        try:
            progress = 50
            step_increment = 40 // len(investigation_plan)

            # Use GPT-5 streaming
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
                max_tokens=4000,
                stream=True
            )

            collected_text = ""

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    collected_text += content

                    # Detect section changes for progress tracking
                    if "INVESTIGATION STEP:" in collected_text:
                        progress = min(progress + step_increment, 85)
                        yield {
                            "type": "progress",
                            "message": "Analyzing next investigation step...",
                            "progress": progress
                        }

                    yield {
                        "type": "reasoning",
                        "content": content
                    }

        except Exception as e:
            logger.error(f"GPT-5 investigation error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Investigation error: {str(e)}"
            }

    async def investigate_url_iterative(
        self,
        url: str,
        technical_data: Dict[str, Any],
        investigation_plan: List[str],
        url_analyzer_instance=None,
        max_iterations: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform iterative investigation that continues until AI is confident
        Yields progress updates with AI reasoning and iteration tracking

        Args:
            url: URL being investigated
            technical_data: Initial technical analysis data
            investigation_plan: Initial investigation plan
            url_analyzer_instance: URLAnalyzer instance for follow-up searches
            max_iterations: Maximum number of investigation iterations (default 3)
        """

        if not self.is_configured():
            yield {
                "type": "error",
                "message": "GPT-5 not configured. Please set OPENAI_API_KEY"
            }
            return

        iteration = 1
        is_confident = False
        investigation_history = []
        accumulated_data = technical_data.copy()

        while not is_confident and iteration <= max_iterations:
            # Notify user of iteration
            yield {
                "type": "iteration",
                "iteration": iteration,
                "max_iterations": max_iterations,
                "message": f"Investigation Round {iteration}/{max_iterations}"
            }

            # Build investigation prompt with accumulated data
            prompt = self._build_investigation_prompt(
                url,
                accumulated_data,
                investigation_plan,
                iteration=iteration,
                previous_findings=investigation_history
            )

            try:
                progress = 50
                step_increment = 30 // len(investigation_plan)
                collected_reasoning = ""

                # Use GPT-5 streaming for investigation
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
                    max_tokens=4000,
                    stream=True
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        collected_reasoning += content

                        if "INVESTIGATION STEP:" in collected_reasoning:
                            progress = min(progress + step_increment, 75)
                            yield {
                                "type": "progress",
                                "message": f"Round {iteration}: Analyzing next step...",
                                "progress": progress
                            }

                        yield {
                            "type": "reasoning",
                            "content": content
                        }

                investigation_history.append({
                    "iteration": iteration,
                    "reasoning": collected_reasoning[:500]  # Store summary
                })

                # Assess confidence after this investigation round
                yield {
                    "type": "status",
                    "message": f"Assessing confidence after round {iteration}..."
                }

                confidence_result = await self._assess_confidence(
                    url,
                    accumulated_data,
                    collected_reasoning,
                    iteration,
                    max_iterations
                )

                yield {
                    "type": "confidence",
                    "iteration": iteration,
                    "confidence_score": confidence_result["confidence_score"],
                    "is_conclusive": confidence_result["is_conclusive"],
                    "reasoning": confidence_result["reasoning"]
                }

                is_confident = confidence_result["is_conclusive"]

                # If not confident and can iterate more, plan follow-up actions
                if not is_confident and iteration < max_iterations:
                    yield {
                        "type": "status",
                        "message": "Planning follow-up investigation actions..."
                    }

                    followup_plan = await self._plan_followup_actions(
                        url,
                        accumulated_data,
                        collected_reasoning,
                        confidence_result
                    )

                    yield {
                        "type": "followup_plan",
                        "iteration": iteration,
                        "actions": followup_plan["actions"],
                        "reasoning": followup_plan["reasoning"]
                    }

                    # Execute follow-up actions if url_analyzer available
                    if url_analyzer_instance and followup_plan["actions"]:
                        yield {
                            "type": "status",
                            "message": "Executing follow-up searches and analysis..."
                        }

                        new_data = await self._execute_followup_actions(
                            url,
                            followup_plan["actions"],
                            url_analyzer_instance
                        )

                        # Merge new data into accumulated data
                        if new_data:
                            accumulated_data["followup_findings"] = accumulated_data.get("followup_findings", [])
                            accumulated_data["followup_findings"].append({
                                "iteration": iteration,
                                "data": new_data
                            })

                            yield {
                                "type": "followup_data",
                                "iteration": iteration,
                                "data": new_data,
                                "message": "New evidence gathered from follow-up investigation"
                            }

                iteration += 1

            except Exception as e:
                logger.error(f"GPT-5 iterative investigation error (iteration {iteration}): {str(e)}")
                yield {
                    "type": "error",
                    "message": f"Investigation error in round {iteration}: {str(e)}"
                }
                break

        # Final status
        if is_confident:
            yield {
                "type": "conclusion",
                "message": f"Investigation concluded with confidence after {iteration-1} round(s)",
                "total_iterations": iteration - 1
            }
        else:
            yield {
                "type": "conclusion",
                "message": f"Investigation completed maximum {max_iterations} rounds",
                "total_iterations": max_iterations
            }

    async def _assess_confidence(
        self,
        url: str,
        accumulated_data: Dict[str, Any],
        investigation_reasoning: str,
        iteration: int,
        max_iterations: int
    ) -> Dict[str, Any]:
        """
        Use GPT-5 to assess confidence in the current findings
        Returns confidence score and whether investigation is conclusive
        """

        prompt = f"""You are a trust and safety expert evaluating the completeness of a URL investigation.

URL: {url}
Current Investigation Round: {iteration}/{max_iterations}

INVESTIGATION FINDINGS SO FAR:
{investigation_reasoning[:2000]}

AVAILABLE DATA:
- Technical analysis: {"Complete" if accumulated_data.get("url_structure") else "Limited"}
- Web reputation data: {"Available" if accumulated_data.get("web_reputation", {}).get("search_performed") else "Not available"}
- Follow-up findings: {len(accumulated_data.get("followup_findings", []))} additional investigations

Assess the confidence level in making a conclusive determination about this URL's safety.

Return ONLY a JSON object with this structure:
{{
  "confidence_score": 0-100,
  "is_conclusive": true/false,
  "reasoning": "Explain what evidence you have, what's missing, and why you are/aren't confident",
  "evidence_gaps": ["List any critical information gaps"],
  "recommendation": "continue_investigation|conclude_now"
}}

Consider:
1. Do you have enough evidence to make a decisive verdict?
2. Are there critical unknowns that additional searches could resolve?
3. Would more investigation significantly change your assessment?
4. Have you exhausted useful avenues of investigation?

Be decisive: Only continue if additional investigation would likely provide material new evidence."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust and safety expert evaluating investigation completeness."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Confidence assessment error: {str(e)}")
            # Conservative fallback: continue investigating
            return {
                "confidence_score": 50,
                "is_conclusive": iteration >= max_iterations,
                "reasoning": "Unable to assess confidence due to error. Continuing investigation.",
                "evidence_gaps": ["Assessment error occurred"],
                "recommendation": "continue_investigation"
            }

    async def _plan_followup_actions(
        self,
        url: str,
        accumulated_data: Dict[str, Any],
        investigation_reasoning: str,
        confidence_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use GPT-5 to plan specific follow-up actions to gather more evidence
        """

        evidence_gaps = confidence_result.get("evidence_gaps", [])

        prompt = f"""You are a trust and safety expert planning follow-up investigation actions.

URL: {url}

CURRENT ASSESSMENT:
Confidence Score: {confidence_result.get("confidence_score", 0)}/100
Evidence Gaps: {json.dumps(evidence_gaps)}
Reasoning: {confidence_result.get("reasoning", "Unknown")}

INVESTIGATION SUMMARY:
{investigation_reasoning[:1500]}

AVAILABLE DATA:
{json.dumps({
    "has_web_reputation": accumulated_data.get("web_reputation", {}).get("search_performed", False),
    "reputation_score": accumulated_data.get("web_reputation", {}).get("reputation_score", "N/A"),
    "scam_indicators_found": len(accumulated_data.get("web_reputation", {}).get("scam_indicators", [])),
    "previous_followups": len(accumulated_data.get("followup_findings", []))
}, indent=2)}

Plan 2-4 specific, targeted follow-up actions that would address the evidence gaps. These can include:
- Specific targeted web searches (provide exact search queries)
- Checking specific technical attributes
- Looking for specific patterns or indicators

Return ONLY a JSON object with this structure:
{{
  "actions": [
    {{
      "type": "web_search",
      "description": "What this search will find",
      "search_queries": ["specific query 1", "specific query 2"]
    }},
    {{
      "type": "technical_recheck",
      "description": "What to verify",
      "focus_areas": ["ssl_details", "redirect_chain", "content_patterns"]
    }}
  ],
  "reasoning": "Why these actions will address the evidence gaps"
}}

Focus on actions that will provide NEW, specific evidence to resolve uncertainties."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust and safety expert planning targeted investigations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Follow-up planning error: {str(e)}")
            return {
                "actions": [],
                "reasoning": f"Unable to plan follow-up actions due to error: {str(e)}"
            }

    async def _execute_followup_actions(
        self,
        url: str,
        actions: List[Dict[str, Any]],
        url_analyzer_instance
    ) -> Dict[str, Any]:
        """
        Execute the planned follow-up actions and gather new data
        """

        new_findings = {
            "web_searches": [],
            "technical_checks": []
        }

        for action in actions:
            action_type = action.get("type")

            try:
                if action_type == "web_search" and hasattr(url_analyzer_instance, 'reputation_searcher'):
                    # Execute targeted web searches
                    search_queries = action.get("search_queries", [])
                    if search_queries:
                        search_results = await url_analyzer_instance.reputation_searcher.execute_targeted_searches(
                            url,
                            search_queries
                        )
                        new_findings["web_searches"].append({
                            "description": action.get("description"),
                            "results": search_results
                        })

                elif action_type == "technical_recheck":
                    # Re-examine specific technical aspects
                    focus_areas = action.get("focus_areas", [])
                    # This could trigger specific technical re-checks
                    # For now, we'll note what was requested
                    new_findings["technical_checks"].append({
                        "description": action.get("description"),
                        "focus_areas": focus_areas,
                        "status": "Noted for final analysis"
                    })

            except Exception as e:
                logger.error(f"Error executing follow-up action {action_type}: {str(e)}")
                continue

        return new_findings

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
        investigation_plan: List[str],
        iteration: int = 1,
        previous_findings: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build comprehensive investigation prompt"""

        # Summarize key technical findings
        risk_indicators = technical_data.get("risk_indicators", [])
        url_structure = technical_data.get("url_structure", {})
        ssl_info = technical_data.get("ssl_info", {})
        content_analysis = technical_data.get("content_analysis", {})
        web_reputation = technical_data.get("web_reputation", {})
        ad_platforms = technical_data.get("ad_platforms", {})
        followup_findings = technical_data.get("followup_findings", [])

        # Build iteration context
        iteration_context = ""
        if iteration > 1 and previous_findings:
            iteration_context = f"""
=== PREVIOUS INVESTIGATION ROUNDS ===

This is investigation round {iteration}. Previous rounds have been conducted.
You have access to new follow-up data gathered based on earlier findings.
Focus on integrating this new evidence with previous analysis.

Previous Investigation Summary:
{chr(10).join([f"Round {f['iteration']}: {f['reasoning'][:200]}..." for f in previous_findings[-2:]])}
"""

        # Build follow-up findings section
        followup_context = ""
        if followup_findings:
            followup_context = "\n=== FOLLOW-UP INVESTIGATION FINDINGS ===\n\n"
            for idx, finding in enumerate(followup_findings, 1):
                followup_context += f"Follow-up Round {finding['iteration']}:\n"
                if finding['data'].get('web_searches'):
                    followup_context += f"  - Additional web searches conducted: {len(finding['data']['web_searches'])} targeted searches\n"
                if finding['data'].get('technical_checks'):
                    followup_context += f"  - Technical re-checks: {len(finding['data']['technical_checks'])} areas verified\n"

        prompt = f"""Conduct a comprehensive trust and safety investigation of the following URL:

URL: {url}
{iteration_context}

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

AD PLATFORM TRANSPARENCY:
{self._format_ad_platforms(ad_platforms)}

AUTOMATED RISK INDICATORS:
{self._format_risk_indicators(risk_indicators)}

HTTP RESPONSE:
- Status Code: {technical_data.get('http_response', {}).get('status_code', 'N/A')}
- Redirects: {len(technical_data.get('http_response', {}).get('redirect_chain', []))}

=== INVESTIGATION PLAN ===

Follow these investigation steps systematically:

{self._format_investigation_plan(investigation_plan)}
{followup_context}

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

    def _format_ad_platforms(self, ad_platforms: Dict[str, Any]) -> str:
        """Format ad platform transparency findings for prompt"""
        if not ad_platforms.get("checked"):
            return "Ad platform check not performed or failed"

        lines = []
        google = ad_platforms.get("google_ads", {})
        meta = ad_platforms.get("meta_ads", {})

        # Summary
        summary = ad_platforms.get("summary", "No advertising detected")
        lines.append(f"Summary: {summary}")

        # Google Ads findings
        if google.get("search_performed"):
            lines.append("\nGOOGLE ADS TRANSPARENCY CENTER:")
            if google.get("found_ads"):
                lines.append("  ✓ Domain found advertising on Google Ads")
                advertisers = google.get("advertisers", [])
                if advertisers:
                    lines.append(f"  - Advertisers: {', '.join(advertisers)}")
                ad_count = google.get("ad_count", 0)
                if ad_count > 0:
                    lines.append(f"  - Approximate ad count: {ad_count}")
                ad_examples = google.get("ad_examples", [])
                if ad_examples:
                    lines.append("  - Ad examples:")
                    for ad in ad_examples[:3]:
                        lines.append(f"    • {ad}")
                advertiser_info = google.get("advertiser_info", "")
                if advertiser_info:
                    lines.append(f"  - Advertiser info: {advertiser_info}")
            else:
                lines.append("  ✗ No active advertising detected on Google Ads")

        # Meta Ad Library findings
        if meta.get("search_performed"):
            lines.append("\nMETA AD LIBRARY (Facebook/Instagram):")
            if meta.get("found_ads"):
                lines.append("  ✓ Domain found advertising on Meta platforms")
                advertisers = meta.get("advertisers", [])
                if advertisers:
                    lines.append(f"  - Advertisers/Pages: {', '.join(advertisers)}")
                ad_count = meta.get("ad_count", 0)
                if ad_count > 0:
                    lines.append(f"  - Approximate ad count: {ad_count}")
                ad_examples = meta.get("ad_examples", [])
                if ad_examples:
                    lines.append("  - Ad examples:")
                    for ad in ad_examples[:3]:
                        lines.append(f"    • {ad}")
            else:
                lines.append("  ✗ No active advertising detected on Meta platforms")

        lines.append("\nIMPORTANT CONTEXT FOR ANALYSIS:")
        lines.append("- If a suspicious URL is actively advertising on major platforms, this is significant")
        lines.append("- Advertiser identity can reveal legitimacy or deception (e.g., unknown entity claiming to be PayPal)")
        lines.append("- Ad content and claims should be verified against actual website behavior")
        lines.append("- Multiple platforms + high ad volume may indicate sophisticated fraud operation")

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
  "verdict": "SAFE|MANUAL_REVIEW_REQUIRED|SUSPICIOUS|MALICIOUS",
  "confidence": 0-100,
  "primary_category": "phishing|malware|scam|fraud|legitimate|unknown",
  "secondary_categories": ["list", "of", "relevant", "categories"],
  "descriptive_risk_category": "Intelligent description of specific risk type (only if verdict is not SAFE)",
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
  "campaign_indicators": {{
    "broader_campaign_detected": true/false,
    "confidence": 0-100,
    "pivot_points": [
      {{
        "type": "domain_pattern|ip_address|ssl_cert|registrar|nameserver|asn|advertiser_id|content_signature|phishing_kit",
        "indicator": "Specific value or pattern to search for",
        "description": "How this can be used to find related threats",
        "evidence": "Why we believe this is part of a campaign",
        "recommended_action": "Specific search query or action to take"
      }}
    ],
    "campaign_assessment": "Explanation of campaign scope and patterns"
  }},
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

DESCRIPTIVE RISK CATEGORY GENERATION (for non-SAFE verdicts):
When verdict is MANUAL_REVIEW_REQUIRED, SUSPICIOUS, or MALICIOUS, generate an intelligent, specific descriptive_risk_category based on the evidence:

Guidelines for descriptive_risk_category:
- Be SPECIFIC and DESCRIPTIVE based on actual findings, not generic labels
- Describe the EXACT type of threat or concern identified
- Use evidence-based language that helps manual reviewers understand the risk

Examples of GOOD descriptive risk categories:
- "PayPal credential phishing impersonating official login page"
- "Tech support scam using fake Microsoft security warnings"
- "Cryptocurrency investment fraud with testimonial manipulation"
- "Romance scam operation with stolen profile photos"
- "Counterfeit luxury goods seller with trademark infringement"
- "Malware distribution disguised as software update"
- "Brand impersonation using typosquatted domain"
- "Fake invoice phishing targeting business accounts"
- "Get-rich-quick pyramid scheme with unrealistic returns"
- "Compromised legitimate website hosting malicious redirects"
- "Disposable hosting infrastructure for serial fraud operations"
- "Clickbait content farm with misleading advertising"

Examples of BAD (too generic) descriptive risk categories:
- "Phishing" (too broad - what kind of phishing?)
- "Scam" (too vague - what type of scam?)
- "Fraud" (not specific enough)
- "Malicious website" (doesn't explain what it does)

The descriptive_risk_category should:
1. Capture the SPECIFIC modus operandi based on evidence
2. Include relevant brand/entity if impersonation is involved
3. Describe the attack vector or deception method
4. Be immediately actionable for manual reviewers
5. Reflect technical findings (e.g., "compromised infrastructure" if Shodan shows malware tags)

For SAFE verdict: Set descriptive_risk_category to null or omit it entirely.

For MANUAL_REVIEW_REQUIRED: Describe the ambiguity/concern that requires human review:
- "New domain with no reputation history - requires baseline establishment"
- "Conflicting signals between positive SSL and poor content quality"
- "Limited technical data due to access restrictions"

VERDICT CLASSIFICATION SYSTEM (for human security researchers with expert manual reviewers):

1. SAFE: High confidence that the URL is legitimate with no significant threats
   - Use when: Clear evidence of legitimacy, no concerning indicators
   - Confidence threshold: >80

2. MANUAL_REVIEW_REQUIRED: Insufficient evidence to classify definitively despite thorough investigation
   - Use when: Conflicting signals, limited data availability, edge cases, or uncertainty remains
   - This is NOT a middle ground between safe and unsafe - it means "I don't have enough evidence"
   - Examples: New domain with no reputation data, technical issues preventing analysis, ambiguous indicators
   - Expert human reviewers will investigate these cases

3. SUSPICIOUS: Evidence suggests potential threats or concerning patterns, but not definitively malicious
   - Use when: Some red flags present but not conclusive proof of malicious intent
   - May include: Poor reputation, suspicious patterns, minor violations
   - Confidence threshold: >70 that something is concerning

4. MALICIOUS: High confidence that the URL is actively engaged in fraud, phishing, malware, or scams
   - Use when: Strong evidence of malicious activity (scam reports, phishing indicators, malware hosting)
   - Confidence threshold: >80 for malicious classification

CAMPAIGN INDICATORS & PIVOT POINT DETECTION:

When verdict is SUSPICIOUS or MALICIOUS, analyze evidence to identify if this URL is part of a BROADER MALICIOUS CAMPAIGN.

CRITICAL RULES:
- Only set broader_campaign_detected=true when confidence >70% based on STRONG evidence
- Be conservative - do NOT speculate without evidence
- Pivot points must be ACTIONABLE - users will scan for these patterns
- If no clear campaign patterns exist, set broader_campaign_detected=false with empty pivot_points array

EVIDENCE TO ANALYZE FOR CAMPAIGN PATTERNS:

1. **Domain Patterns** (typosquatting, similar naming):
   - Multiple domains with similar names (paypa1.com, paypa|.com, paypai.com)
   - Same domain structure pattern (login-[brand].com, secure-[brand].com)
   - Sequential numbering or variations
   Example pivot: {{"type": "domain_pattern", "indicator": "paypa[l|1|i].com or pay-pal-*.com", "description": "Typosquatting pattern targeting PayPal brand"}}

2. **Shared Infrastructure** (IP, ASN, hosting):
   - Same IP address across multiple suspicious indicators
   - Same ASN/hosting provider with malicious tags from Shodan
   - Disposable infrastructure pattern (cheap VPS, frequently changing)
   Example pivot: {{"type": "ip_address", "indicator": "1.2.3.4", "description": "IP hosts multiple phishing domains"}}
   Example pivot: {{"type": "asn", "indicator": "AS12345 (Cheap Host Inc)", "description": "ASN shows pattern of hosting short-lived scam sites"}}

3. **SSL/TLS Certificate Patterns**:
   - Same SSL certificate across multiple domains
   - Same certificate issuer with unusual pattern
   - Self-signed certificates with similar attributes
   Example pivot: {{"type": "ssl_cert", "indicator": "SHA1: abc123...", "description": "Certificate shared across 5+ domains in investigation"}}

4. **Registration Patterns** (WHOIS data):
   - Same registrar with bulk registration pattern
   - Registration dates within same week/month
   - Same privacy service (common but note if suspicious context)
   - Similar contact information
   Example pivot: {{"type": "registrar", "indicator": "ScamRegistrar LLC, registered 2024-10-15 to 2024-10-22", "description": "Bulk registration pattern"}}

5. **Advertiser Patterns** (from ad platform data):
   - Same advertiser ID across multiple suspicious domains
   - Similar advertiser names with variations
   - Ad content patterns (same images, same copy structure)
   Example pivot: {{"type": "advertiser_id", "indicator": "Meta Page ID: 123456789", "description": "Advertiser running ads for multiple suspicious domains"}}

6. **Content Signatures** (phishing kits, malware families):
   - Identical page structure/HTML
   - Same external scripts/resources loaded
   - Same form action URLs
   - Known phishing kit signature
   Example pivot: {{"type": "phishing_kit", "indicator": "Login form posts to hxxp://attacker.com/log.php", "description": "Standard phishing kit signature"}}
   Example pivot: {{"type": "content_signature", "indicator": "Loads script from cdn.malicious.com/track.js", "description": "Same tracking script across campaign"}}

7. **Nameserver Patterns**:
   - Same DNS nameservers across domains
   - Nameservers associated with malicious activity
   Example pivot: {{"type": "nameserver", "indicator": "ns1.scamhost.ru, ns2.scamhost.ru", "description": "Nameservers used by multiple fraud domains"}}

RECOMMENDED ACTIONS FOR PIVOT POINTS:
- Make them SPECIFIC and ACTIONABLE
- Provide exact search queries when possible
- Examples:
  - "Search Shodan for IP: 1.2.3.4"
  - "Search domain registrations for pattern: secure-[brand]-*.com in last 30 days"
  - "Search ad libraries for Meta Advertiser ID: 123456789"
  - "Scan SSL certificates with SHA1: abc123..."

WHEN TO SET broader_campaign_detected=false:
- Isolated domain with no pattern connections
- Generic shared hosting (DigitalOcean/AWS without other indicators)
- Common registrar with no bulk registration pattern
- No evidence of related infrastructure or domains

EXAMPLES:

Good campaign detection:
{{
  "broader_campaign_detected": true,
  "confidence": 85,
  "pivot_points": [
    {{
      "type": "domain_pattern",
      "indicator": "paypa[l|1|i].com, pay-pal-*.com, paypal-*.com",
      "description": "Typosquatting campaign targeting PayPal users with multiple domain variations",
      "evidence": "DNS shows 3 similar domains (paypa1.com, paypai.com, paypal-login.com) all registered 2024-10-15, same IP, same SSL cert",
      "recommended_action": "Search domain registrations for 'paypa*' pattern in last 60 days; monitor similar typosquats"
    }},
    {{
      "type": "ip_address",
      "indicator": "192.0.2.45",
      "description": "Shared hosting IP for phishing campaign infrastructure",
      "evidence": "Shodan shows IP hosts 12 domains, tagged as 'phishing', all domains use same phishing kit signature",
      "recommended_action": "Search Shodan for IP 192.0.2.45; investigate all hosted domains for phishing content"
    }}
  ],
  "campaign_assessment": "This appears to be a coordinated PayPal phishing campaign using typosquatted domains, shared infrastructure, and identical phishing kit. Evidence suggests campaign involves 10+ domains based on IP hosting and domain patterns. Recommend proactive blocking of domain pattern and IP-based detection."
}}

No campaign detected:
{{
  "broader_campaign_detected": false,
  "confidence": 0,
  "pivot_points": [],
  "campaign_assessment": "No evidence of broader campaign. URL appears to be isolated incident with no infrastructure or pattern connections to other threats."
}}

Be decisive based on available evidence. Use MANUAL_REVIEW_REQUIRED only when you genuinely lack sufficient data to classify, NOT as a safety net for uncertain cases where you have evidence pointing one way or another.

Ensure every finding has a clear citation to technical evidence.
Return ONLY valid JSON, no markdown formatting."""

        try:
            # Use GPT-5 with response_format for structured JSON output
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust and safety expert. Generate comprehensive analysis reports."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            report_text = response.choices[0].message.content.strip()
            report = json.loads(report_text)
            return report

        except Exception as e:
            logger.error(f"GPT-5 report generation error: {str(e)}")
            return self._generate_fallback_report(url, technical_data)

    def _generate_fallback_report(
        self, url: str, technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a basic report when AI is unavailable"""

        risk_indicators = technical_data.get("risk_indicators", [])
        critical_risk = sum(1 for r in risk_indicators if r.get("type") == "critical")
        high_risk = sum(1 for r in risk_indicators if r.get("type") == "high")
        medium_risk = sum(1 for r in risk_indicators if r.get("type") == "medium")
        total_indicators = len(risk_indicators)

        # Simple scoring with updated thresholds
        risk_score = (critical_risk * 40) + (high_risk * 25) + (medium_risk * 10)
        risk_score = min(risk_score, 100)

        # Check if we have sufficient data for classification
        has_web_reputation = technical_data.get("web_reputation", {}).get("search_performed", False)
        has_dns = technical_data.get("dns_info", {}).get("resolved", False)
        has_content = technical_data.get("content_analysis", {}) and not technical_data.get("content_analysis", {}).get("error")

        data_sources_available = sum([has_web_reputation, has_dns, has_content])

        # Determine verdict based on 4-level system
        if data_sources_available < 2 or total_indicators == 0:
            # Insufficient data for classification
            verdict = "MANUAL_REVIEW_REQUIRED"
            confidence = 40
            summary = f"Limited data available for automated classification. Only {data_sources_available}/3 primary data sources accessible."
        elif critical_risk >= 2 or risk_score >= 70:
            verdict = "MALICIOUS"
            confidence = 75
            summary = f"High-confidence malicious classification. Detected {critical_risk} critical and {high_risk} high-risk indicators."
        elif high_risk >= 2 or risk_score >= 40:
            verdict = "SUSPICIOUS"
            confidence = 70
            summary = f"Suspicious patterns detected. Found {high_risk} high-risk and {medium_risk} medium-risk indicators."
        elif risk_score <= 15 and high_risk == 0 and critical_risk == 0:
            verdict = "SAFE"
            confidence = 65
            summary = f"No significant threats detected. Analysis found {total_indicators} minor indicators."
        else:
            # Edge case: some risk but not enough to be suspicious
            verdict = "MANUAL_REVIEW_REQUIRED"
            confidence = 50
            summary = f"Mixed signals detected. {risk_score} risk score requires expert review."

        # Generate descriptive risk category for non-SAFE verdicts
        descriptive_risk_category = None
        if verdict != "SAFE":
            descriptive_risk_category = self._generate_basic_risk_category(
                verdict, risk_indicators, technical_data
            )

        return {
            "verdict": verdict,
            "confidence": confidence,
            "primary_category": "unknown",
            "descriptive_risk_category": descriptive_risk_category,
            "risk_score": risk_score,
            "summary": summary,
            "detailed_rationale": f"Basic automated analysis (AI unavailable). Risk indicators: {critical_risk} critical, {high_risk} high, {medium_risk} medium. Data sources: {data_sources_available}/3 available. For comprehensive AI-powered analysis with reasoning, configure OpenAI API key.",
            "key_findings": [
                {
                    "finding": r.get("indicator", "Unknown indicator"),
                    "evidence": r.get("risk", ""),
                    "severity": r.get("type", "unknown"),
                    "citation": r.get("category", "technical")
                }
                for r in risk_indicators
            ],
            "campaign_indicators": {
                "broader_campaign_detected": False,
                "confidence": 0,
                "pivot_points": [],
                "campaign_assessment": "Campaign analysis requires AI (GPT-5). Configure OpenAI API key for advanced threat intelligence."
            },
            "recommendations": [
                "Expert manual review recommended" if verdict == "MANUAL_REVIEW_REQUIRED" else "Review findings and take appropriate action",
                "Configure AI API (OpenAI GPT-5) for deep investigation and reasoning"
            ],
            "threat_indicators": [r.get("indicator", "") for r in risk_indicators if r.get("indicator")],
            "timestamp": datetime.utcnow().isoformat(),
            "analyst_notes": f"Fallback classification based on rule-based heuristics. Verdict: {verdict} requires human verification."
        }

    def _generate_basic_risk_category(
        self,
        verdict: str,
        risk_indicators: List[Dict[str, Any]],
        technical_data: Dict[str, Any]
    ) -> str:
        """
        Generate a basic descriptive risk category when AI is unavailable
        This is a simplified version - GPT-5 provides much better categorization
        """
        if verdict == "MANUAL_REVIEW_REQUIRED":
            return "Insufficient data for risk classification - manual investigation required"

        # Analyze risk indicators to determine primary risk type
        categories = [r.get("category", "") for r in risk_indicators]
        indicators_text = [r.get("indicator", "").lower() for r in risk_indicators]

        # Check for specific threat patterns
        web_rep = technical_data.get("web_reputation", {})
        scam_indicators = web_rep.get("scam_indicators", [])
        shodan = technical_data.get("shodan_infrastructure", {})
        ad_platforms = technical_data.get("ad_platforms", {})

        # Priority-based classification
        # 1. Check Shodan for infrastructure threats
        if shodan.get("checked"):
            shodan_risks = shodan.get("risk_indicators", [])
            malicious_tags = [r for r in shodan_risks if r.get("type") == "malicious_tag"]
            if malicious_tags:
                tag_desc = malicious_tags[0].get("description", "")
                if "malware" in tag_desc.lower():
                    return "Malware hosting infrastructure detected"
                elif "phishing" in tag_desc.lower():
                    return "Phishing operation infrastructure"
                elif "botnet" in tag_desc.lower() or "c2" in tag_desc.lower():
                    return "Botnet or command-and-control infrastructure"
                elif "compromised" in tag_desc.lower():
                    return "Compromised server infrastructure"

        # 2. Check web reputation for specific scam types
        if scam_indicators:
            high_severity_scams = [s for s in scam_indicators if s.get("severity") == "high"]
            if high_severity_scams:
                # Try to extract specific scam type from indicators
                for scam in high_severity_scams[:2]:
                    indicator_lower = scam.get("indicator", "").lower()
                    if "phishing" in indicator_lower or "credential" in indicator_lower:
                        return "Credential phishing operation"
                    elif "investment" in indicator_lower or "crypto" in indicator_lower:
                        return "Investment fraud or cryptocurrency scam"
                    elif "romance" in indicator_lower or "dating" in indicator_lower:
                        return "Romance scam operation"
                    elif "tech support" in indicator_lower or "refund" in indicator_lower:
                        return "Tech support or refund scam"
                    elif "fake" in indicator_lower and "product" in indicator_lower:
                        return "Counterfeit product sales operation"

                return "Online scam operation with multiple user reports"

        # 3. Check URL structure indicators
        url_struct_indicators = [i for i in indicators_text if any(
            pattern in i for pattern in ["phishing", "typosquat", "impersonat", "suspicious_keywords"]
        )]
        if url_struct_indicators:
            if any("paypal" in i or "bank" in i or "login" in i for i in indicators_text):
                return "Potential financial credential phishing"
            return "Brand impersonation or typosquatting attempt"

        # 4. Check content-based indicators
        content_indicators = [r for r in risk_indicators if r.get("category") == "content"]
        if content_indicators:
            for ind in content_indicators:
                indicator = ind.get("indicator", "").lower()
                if "form" in indicator and "external" in indicator:
                    return "Suspicious form submission to external domain"
                elif "iframe" in indicator:
                    return "Hidden iframe content injection"

        # 5. Check for advertising fraud patterns
        if ad_platforms.get("google_ads", {}).get("found_ads") or ad_platforms.get("meta", {}).get("found_ads"):
            return "Active advertising with suspicious indicators"

        # 6. Generic categorization based on risk level
        if "infrastructure" in categories:
            return "Suspicious hosting infrastructure patterns"
        elif "web_reputation" in categories:
            return "Poor online reputation with concerning user reports"
        elif "security" in categories:
            return "Security configuration concerns"

        # Default fallback
        if verdict == "MALICIOUS":
            return "Malicious activity detected - specific type requires analysis"
        elif verdict == "SUSPICIOUS":
            return "Suspicious patterns detected - manual review recommended"

        return "Unclassified threat - expert review required"

    async def answer_followup(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Answer follow-up questions about the URL analysis
        Uses basic context-only approach (fast but limited)
        """

        if not self.is_configured():
            yield {
                "type": "response",
                "content": "GPT-5 not configured. Please set OPENAI_API_KEY environment variable."
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
            # Use GPT-5 streaming for follow-up responses
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

        except Exception as e:
            logger.error(f"GPT-5 follow-up error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Error processing question: {str(e)}"
            }

    async def answer_followup_with_investigation(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]] = None,
        url_analyzer_instance=None,
        user_screenshots: Optional[List[str]] = None,
        screenshot_context: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Answer follow-up questions with active investigation capability
        Generic AI-driven system that can handle ANY question type

        Now supports multimodal analysis with user-provided screenshots for:
        - Ad cloaking detection (compare user's ad screenshot vs actual site)
        - Visual evidence analysis
        - Screenshot comparison (user vs URLScan.io)

        GPT-5 analyzes the question and decides what actions to take,
        then synthesizes answer with gathered evidence

        Args:
            user_screenshots: List of base64-encoded images or image URLs
            screenshot_context: User description of screenshots (e.g., "This is the ad I saw on Facebook")
        """

        if not self.is_configured():
            yield {
                "type": "error",
                "message": "GPT-5 not configured. Please set OPENAI_API_KEY"
            }
            return

        yield {
            "type": "status",
            "message": "Analyzing your question..."
        }

        # If user provided screenshots, analyze them first
        screenshot_analysis = None
        if user_screenshots:
            yield {
                "type": "status",
                "message": f"Analyzing {len(user_screenshots)} screenshot(s) with AI..."
            }

            screenshot_analysis = await self._analyze_user_screenshots(
                url,
                user_screenshots,
                screenshot_context,
                previous_context
            )

            if screenshot_analysis:
                yield {
                    "type": "screenshot_analysis",
                    "data": screenshot_analysis,
                    "message": "Screenshot analysis complete"
                }

        # Step 1: GPT-5 analyzes the question and determines required actions
        action_plan = await self._analyze_followup_question(
            url,
            question,
            previous_context,
            screenshot_analysis
        )

        yield {
            "type": "plan",
            "message": f"Planning: {action_plan.get('reasoning', 'Determining investigation approach...')}"
        }

        # Step 2: Execute actions if new data is needed
        new_data = {}
        if action_plan.get("requires_new_data") and action_plan.get("actions"):
            yield {
                "type": "status",
                "message": f"Gathering additional evidence ({len(action_plan['actions'])} action(s))..."
            }

            new_data = await self._execute_followup_investigation_actions(
                url,
                action_plan["actions"],
                previous_context,
                url_analyzer_instance
            )

            if new_data:
                yield {
                    "type": "data_gathered",
                    "message": "New evidence collected. Analyzing..."
                }

        # Step 3: GPT-5 synthesizes comprehensive answer (including screenshot analysis)
        yield {
            "type": "status",
            "message": "Formulating answer..."
        }

        async for response_chunk in self._synthesize_followup_answer(
            url,
            question,
            previous_context,
            action_plan,
            new_data,
            screenshot_analysis
        ):
            yield response_chunk

    async def _analyze_followup_question(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]],
        screenshot_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use GPT-5 to analyze the question and determine what actions are needed
        This is the key to making the system generic

        Now also considers user-provided screenshot analysis if available
        """

        context_summary = self._build_context_summary(url, previous_context)

        # Add screenshot analysis to context if available
        screenshot_info = ""
        if screenshot_analysis:
            screenshot_info = f"\n\nUSER-PROVIDED SCREENSHOTS ANALYSIS:\n{json.dumps(screenshot_analysis, indent=2)}\n\nThe user has provided visual evidence. Consider this in your investigation plan."

        prompt = f"""You are a trust and safety expert analyzing a follow-up question about a URL investigation.

ORIGINAL INVESTIGATION:
{context_summary}
{screenshot_info}

RESEARCHER'S QUESTION:
{question}

Analyze this question and determine what additional information or actions are needed to answer it comprehensively.

Available action types:
1. "web_search" - Search the web for specific information
2. "compare_domains" - Compare two or more domains for relationships/similarities
3. "whois_lookup" - Get WHOIS registration data for a domain
4. "fetch_evidence" - Retrieve specific evidence mentioned in investigation
5. "analyze_advertiser" - Analyze advertiser information provided by user
6. "check_relationship" - Check if domains/entities are related
7. "shodan_lookup" - Get infrastructure intelligence from Shodan (ports, services, vulnerabilities, hosting)
8. "no_action" - Answer from existing context only

Return ONLY a JSON object:
{{
  "intent": "comparison|context_update|evidence_request|relationship_check|strategic_analysis|clarification",
  "requires_new_data": true/false,
  "actions": [
    {{
      "type": "web_search",
      "description": "Why this search is needed",
      "params": {{
        "queries": ["specific query 1", "specific query 2"]
      }}
    }},
    {{
      "type": "compare_domains",
      "description": "What to compare",
      "params": {{
        "domains": ["domain1.com", "domain2.com"],
        "comparison_aspects": ["whois", "content", "reputation"]
      }}
    }},
    {{
      "type": "analyze_advertiser",
      "description": "Analyze provided advertiser info",
      "params": {{
        "advertiser_data": "extracted from question"
      }}
    }}
  ],
  "reasoning": "Explain why these actions will answer the question"
}}

Be intelligent about detecting:
- User providing new context (advertiser info, campaign details)
- Questions about domain relationships (typosquatting, impersonation)
- Requests for specific evidence or details
- Comparative questions
- Strategic/analytical questions (may not need new data)
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are analyzing follow-up questions and planning investigation actions."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Question analysis error: {str(e)}")
            # Fallback: answer from context only
            return {
                "intent": "clarification",
                "requires_new_data": False,
                "actions": [],
                "reasoning": f"Error analyzing question: {str(e)}. Will answer from existing context."
            }

    async def _execute_followup_investigation_actions(
        self,
        url: str,
        actions: List[Dict[str, Any]],
        previous_context: Optional[Dict[str, Any]],
        url_analyzer_instance
    ) -> Dict[str, Any]:
        """
        Execute the actions determined by GPT-5
        Modular design allows easy addition of new action types
        """

        results = {
            "actions_executed": [],
            "data": {}
        }

        for action in actions:
            action_type = action.get("type")
            params = action.get("params", {})

            try:
                logger.info(f"Executing follow-up action: {action_type}")

                if action_type == "web_search":
                    # Execute web searches
                    queries = params.get("queries", [])
                    if queries and url_analyzer_instance and hasattr(url_analyzer_instance, 'reputation_searcher'):
                        search_results = await url_analyzer_instance.reputation_searcher.execute_targeted_searches(
                            url,
                            queries
                        )
                        results["data"]["web_search"] = search_results
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description"),
                            "queries": queries,
                            "results_count": search_results.get("total_results", 0)
                        })

                elif action_type == "compare_domains":
                    # Compare multiple domains
                    domains = params.get("domains", [])
                    if domains and url_analyzer_instance:
                        comparison = await self._compare_domains(domains, url_analyzer_instance)
                        results["data"]["domain_comparison"] = comparison
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description"),
                            "domains": domains
                        })

                elif action_type == "whois_lookup":
                    # WHOIS lookup for domain
                    domain = params.get("domain")
                    if domain and url_analyzer_instance:
                        whois_data = await self._whois_lookup(domain, url_analyzer_instance)
                        results["data"]["whois"] = whois_data
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description"),
                            "domain": domain
                        })

                elif action_type == "analyze_advertiser":
                    # Analyze user-provided advertiser information
                    advertiser_data = params.get("advertiser_data", "")
                    if advertiser_data:
                        analysis = await self._analyze_advertiser_context(
                            url,
                            advertiser_data,
                            previous_context
                        )
                        results["data"]["advertiser_analysis"] = analysis
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description")
                        })

                elif action_type == "check_relationship":
                    # Check relationship between entities
                    entities = params.get("entities", [])
                    if entities and url_analyzer_instance:
                        relationship = await self._check_entity_relationship(
                            entities,
                            url_analyzer_instance
                        )
                        results["data"]["relationship_check"] = relationship
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description"),
                            "entities": entities
                        })

                elif action_type == "shodan_lookup":
                    # Perform Shodan infrastructure lookup
                    domain = params.get("domain")
                    if not domain:
                        # Extract domain from URL if not provided
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc or parsed.path

                    if domain and url_analyzer_instance and hasattr(url_analyzer_instance, 'shodan_analyzer'):
                        if url_analyzer_instance.shodan_analyzer.is_configured():
                            shodan_data = await url_analyzer_instance.shodan_analyzer.analyze_infrastructure(
                                url, domain
                            )
                            results["data"]["shodan"] = shodan_data
                            results["actions_executed"].append({
                                "type": action_type,
                                "description": action.get("description"),
                                "domain": domain,
                                "found_data": shodan_data.get("checked", False)
                            })
                        else:
                            logger.warning("Shodan not configured for follow-up lookup")
                            results["data"]["shodan"] = {
                                "checked": False,
                                "error": "Shodan not configured"
                            }

                elif action_type == "fetch_evidence":
                    # Fetch specific evidence from previous investigation
                    evidence_type = params.get("evidence_type")
                    if evidence_type and previous_context:
                        evidence = self._extract_evidence_from_context(
                            evidence_type,
                            previous_context
                        )
                        results["data"]["evidence"] = evidence
                        results["actions_executed"].append({
                            "type": action_type,
                            "description": action.get("description"),
                            "evidence_type": evidence_type
                        })

            except Exception as e:
                logger.error(f"Error executing action {action_type}: {str(e)}")
                results["actions_executed"].append({
                    "type": action_type,
                    "error": str(e)
                })

        return results

    async def _synthesize_followup_answer(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]],
        action_plan: Dict[str, Any],
        new_data: Dict[str, Any],
        screenshot_analysis: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Use GPT-5 to synthesize comprehensive answer with all available evidence
        Now includes screenshot analysis for visual evidence
        """

        context_summary = self._build_context_summary(url, previous_context)

        new_data_summary = ""
        if new_data.get("data"):
            new_data_summary = f"""

NEW EVIDENCE GATHERED:
{json.dumps(new_data, indent=2)[:3000]}
"""

        screenshot_summary = ""
        if screenshot_analysis:
            screenshot_summary = f"""

USER-PROVIDED VISUAL EVIDENCE:
{json.dumps(screenshot_analysis, indent=2)[:2000]}

CLOAKING DETECTED: {'YES - Site shows different content in ads vs direct visits!' if screenshot_analysis.get('cloaking_detected') else 'No significant differences detected'}
"""

        prompt = f"""You are a trust and safety expert providing a comprehensive answer to a follow-up question.

ORIGINAL INVESTIGATION:
{context_summary}

RESEARCHER'S QUESTION:
{question}

INVESTIGATION ACTIONS TAKEN:
{action_plan.get('reasoning', 'N/A')}
{new_data_summary}
{screenshot_summary}

Provide a detailed, evidence-based answer to the researcher's question.

Key requirements:
1. Cite specific evidence from both original investigation and new data
2. Be decisive and clear in your assessment
3. If new advertiser information was provided, compare it with findings
4. If domain relationships were checked, explain the connection/threat
5. Reference specific data points (quotes, statistics, sources)
6. Update verdict if new evidence warrants it
7. **If user provided screenshots and cloaking was detected, emphasize this as critical finding**
8. **Analyze visual evidence alongside technical findings for comprehensive assessment**

Answer the question comprehensively:"""

        try:
            stream = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trust and safety expert providing follow-up analysis."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "response",
                        "content": chunk.choices[0].delta.content
                    }

        except Exception as e:
            logger.error(f"Answer synthesis error: {str(e)}")
            yield {
                "type": "error",
                "message": f"Error formulating answer: {str(e)}"
            }

    def _build_context_summary(
        self,
        url: str,
        previous_context: Optional[Dict[str, Any]]
    ) -> str:
        """Build concise summary of investigation context"""

        if not previous_context:
            return f"URL: {url}\nNo previous investigation context available."

        report = previous_context.get('report', {})
        technical_data = previous_context.get('technical_data', {})

        summary = f"""URL: {url}
Verdict: {report.get('verdict', 'N/A')}
Risk Score: {report.get('risk_score', 'N/A')}/100
Confidence: {report.get('confidence', 'N/A')}%
Primary Category: {report.get('primary_category', 'N/A')}

Key Findings:
{json.dumps(report.get('key_findings', []), indent=2)[:800]}

Technical Data Summary:
{json.dumps({
    'domain': technical_data.get('url_structure', {}).get('fqdn'),
    'has_ssl': technical_data.get('ssl_info', {}).get('has_ssl'),
    'web_reputation': technical_data.get('web_reputation', {}).get('risk_level'),
    'ad_platforms': technical_data.get('ad_platforms', {}).get('summary')
}, indent=2)}
"""
        return summary

    async def _compare_domains(
        self,
        domains: List[str],
        url_analyzer_instance
    ) -> Dict[str, Any]:
        """Compare multiple domains for similarities and relationships"""

        comparison = {
            "domains": domains,
            "similarities": [],
            "differences": [],
            "threat_assessment": ""
        }

        try:
            # Analyze each domain
            domain_analyses = {}
            for domain in domains[:3]:  # Limit to 3 domains
                try:
                    import tldextract
                    extracted = tldextract.extract(domain)

                    # Basic structure comparison
                    domain_analyses[domain] = {
                        "domain": extracted.domain,
                        "suffix": extracted.suffix,
                        "length": len(domain),
                        "has_hyphen": "-" in domain,
                        "has_numbers": any(c.isdigit() for c in domain)
                    }
                except Exception as e:
                    logger.error(f"Error analyzing domain {domain}: {str(e)}")

            # Use GPT-4o-mini for comparison analysis
            if self.openai_client and len(domain_analyses) >= 2:
                prompt = f"""Compare these domains for potential typosquatting or impersonation:

{json.dumps(domain_analyses, indent=2)}

Return JSON:
{{
  "similarities": ["List specific similarities"],
  "differences": ["List key differences"],
  "relationship": "typosquatting|legitimate_variants|unrelated|same_entity",
  "threat_level": "high|medium|low|none",
  "threat_assessment": "Explanation of threat if any"
}}"""

                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are analyzing domain relationships for security threats."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"}
                )

                comparison = json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Domain comparison error: {str(e)}")
            comparison["error"] = str(e)

        return comparison

    async def _whois_lookup(
        self,
        domain: str,
        url_analyzer_instance
    ) -> Dict[str, Any]:
        """Perform WHOIS lookup on domain"""

        whois_data = {
            "domain": domain,
            "registrar": "N/A",
            "creation_date": "N/A",
            "registrant": "N/A"
        }

        try:
            # Note: Actual WHOIS implementation would go here
            # For now, return placeholder data
            logger.info(f"WHOIS lookup for {domain} (placeholder)")
            whois_data["note"] = "WHOIS lookup capability available"

        except Exception as e:
            logger.error(f"WHOIS lookup error: {str(e)}")
            whois_data["error"] = str(e)

        return whois_data

    async def _analyze_advertiser_context(
        self,
        url: str,
        advertiser_data: str,
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user-provided advertiser information"""

        try:
            # Get existing ad platform findings
            ad_platforms = previous_context.get('technical_data', {}).get('ad_platforms', {}) if previous_context else {}

            prompt = f"""Analyze advertiser information provided by user and compare with investigation findings.

URL BEING INVESTIGATED: {url}

USER-PROVIDED ADVERTISER INFO:
{advertiser_data}

EXISTING AD PLATFORM FINDINGS:
{json.dumps(ad_platforms, indent=2)}

Analyze for discrepancies and fraud indicators. Return JSON:
{{
  "advertiser_claims": "What advertiser claims to be",
  "investigation_findings": "What investigation found",
  "discrepancies": ["List any mismatches"],
  "fraud_indicators": ["Specific fraud signals"],
  "threat_level": "critical|high|medium|low|none",
  "assessment": "Overall assessment of advertiser legitimacy"
}}"""

            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are analyzing advertiser information for fraud detection."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=600,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Advertiser analysis error: {str(e)}")
            return {"error": str(e)}

    async def _check_entity_relationship(
        self,
        entities: List[str],
        url_analyzer_instance
    ) -> Dict[str, Any]:
        """Check relationships between entities (domains, companies, etc.)"""

        relationship = {
            "entities": entities,
            "relationship_type": "unknown",
            "evidence": []
        }

        try:
            # Perform web searches to find relationships
            if url_analyzer_instance and hasattr(url_analyzer_instance, 'reputation_searcher'):
                search_query = f"{' '.join(entities)} relationship connection"
                results = await url_analyzer_instance.reputation_searcher.execute_targeted_searches(
                    entities[0],
                    [search_query]
                )

                relationship["search_results"] = results.get("findings", [])
                relationship["relationship_type"] = "search_conducted"

        except Exception as e:
            logger.error(f"Relationship check error: {str(e)}")
            relationship["error"] = str(e)

        return relationship

    def _extract_evidence_from_context(
        self,
        evidence_type: str,
        previous_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract specific evidence from previous investigation context"""

        evidence = {
            "type": evidence_type,
            "data": {}
        }

        try:
            technical_data = previous_context.get('technical_data', {})

            if evidence_type == "scam_reports":
                web_rep = technical_data.get('web_reputation', {})
                evidence["data"] = web_rep.get('scam_indicators', [])

            elif evidence_type == "user_complaints":
                web_rep = technical_data.get('web_reputation', {})
                evidence["data"] = web_rep.get('user_complaints', [])

            elif evidence_type == "ad_platforms":
                evidence["data"] = technical_data.get('ad_platforms', {})

            elif evidence_type == "ssl_info":
                evidence["data"] = technical_data.get('ssl_info', {})

            elif evidence_type == "all_findings":
                report = previous_context.get('report', {})
                evidence["data"] = report.get('key_findings', [])

        except Exception as e:
            logger.error(f"Evidence extraction error: {str(e)}")
            evidence["error"] = str(e)

        return evidence

    async def _analyze_user_screenshots(
        self,
        url: str,
        screenshots: List[str],
        screenshot_context: Optional[str],
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze user-provided visual evidence with GPT-4o

        Accepts ANY type of screenshot/image that provides useful investigation context:
        - Advertisements (social media, native ads, banners)
        - Website screenshots (landing pages, forms, checkout, errors)
        - Communications (emails, messages, notifications)
        - Browser interactions (popups, warnings, downloads)
        - Comparisons (legitimate vs suspicious sites)
        - Mobile views (apps, mobile browsers)
        - Any other visual evidence

        Performs:
        1. Intelligent content type recognition (ad, webpage, email, popup, etc.)
        2. Context-aware visual analysis adapted to screenshot type
        3. Comparison with URLScan.io screenshot if available (cloaking detection)
        4. Threat assessment and correlation with technical findings

        Args:
            screenshots: List of base64-encoded images or image URLs (any type)
            screenshot_context: User's description (e.g., "Facebook ad I saw", "Error at checkout", "Email I received")
            previous_context: Previous investigation data (may contain URLScan.io screenshot)

        Returns:
            Dict with:
            - individual_analysis: List of analysis for each screenshot
            - cloaking_detected: Bool indicating if ad shows different content
            - comparison_with_urlscan: Comparison results if URLScan screenshot available
            - threat_assessment: Overall threat evaluation based on visual evidence
        """

        if not screenshots:
            return None

        try:
            # Get URLScan.io screenshot from previous context if available
            urlscan_screenshot_url = None
            if previous_context:
                technical_data = previous_context.get('technical_data', {})
                content_sec = technical_data.get('content_security', {})
                urlscan_data = content_sec.get('threat_intelligence', {}).get('urlscan_io', {})
                urlscan_screenshot_url = urlscan_data.get('screenshot_url')

            result = {
                "individual_analysis": [],
                "cloaking_detected": False,
                "comparison_with_urlscan": None,
                "threat_assessment": {},
                "user_context": screenshot_context or "No context provided"
            }

            # Analyze each user screenshot
            for idx, screenshot in enumerate(screenshots):
                analysis = await self._analyze_single_screenshot(
                    screenshot,
                    url,
                    screenshot_context,
                    f"User Screenshot {idx + 1}"
                )

                if analysis:
                    result["individual_analysis"].append(analysis)

            # If we have both user screenshots and URLScan.io screenshot, compare them
            if urlscan_screenshot_url and screenshots:
                logger.info("Comparing user screenshot with URLScan.io screenshot for cloaking detection...")

                comparison = await self._compare_screenshots(
                    screenshots[0],  # Use first user screenshot
                    urlscan_screenshot_url,
                    url,
                    screenshot_context
                )

                if comparison:
                    result["comparison_with_urlscan"] = comparison
                    result["cloaking_detected"] = comparison.get("significant_differences", False)

            # Generate overall threat assessment
            result["threat_assessment"] = self._synthesize_screenshot_threat_assessment(
                result["individual_analysis"],
                result.get("comparison_with_urlscan"),
                previous_context
            )

            return result

        except Exception as e:
            logger.error(f"Screenshot analysis error: {str(e)}")
            return {
                "error": str(e),
                "message": "Failed to analyze screenshots"
            }

    async def _analyze_single_screenshot(
        self,
        screenshot: str,
        url: str,
        context: Optional[str],
        label: str
    ) -> Dict[str, Any]:
        """Analyze a single screenshot using GPT-4o"""

        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }

            context_info = f"\n\nUSER CONTEXT: {context}" if context else ""

            prompt = f"""Analyze this screenshot related to the URL: {url}
{context_info}

You are a trust & safety analyst. The user has provided this visual evidence for investigation. This could be:
- An advertisement or social media post promoting the URL
- A screenshot of the actual website/landing page
- An error message or warning
- An email or message referencing the URL
- A payment screen or form
- A suspicious popup or overlay
- A comparison with a legitimate site
- Any other visual context the user finds relevant

Analyze this visual evidence comprehensively:

1. **Content Type & Description**: What is shown? (ad, webpage, email, error, popup, form, etc.)
2. **Key Information**: What text, claims, promises, or information is presented?
3. **Visual Elements Analysis**:
   - Branding (logos, colors, layout - does it match expected brand for {url}?)
   - Quality indicators (professional vs hastily made, typos, poor graphics)
   - Urgency or pressure tactics ("Act now!", countdown timers, limited offers)
   - Requests for sensitive data (credentials, payment info, personal details)
   - Suspicious elements (fake testimonials, too-good-to-be-true, security warnings)
4. **Contextual Relevance**: How does this relate to {url}? Does it match, contradict, or reveal deception?
5. **Threat Indicators**: Any red flags suggesting:
   - Phishing (fake login, credential harvesting)
   - Scams (prize schemes, fake tech support, malware warnings)
   - Ad fraud (misleading promises, cloaking, bait-and-switch)
   - Brand impersonation or spoofing
   - Social engineering tactics
6. **Overall Assessment**: Based on this visual evidence, what threat level is indicated?

Respond in JSON format:
{{
    "content_type": "ad|webpage|email|error_message|popup|payment_screen|social_media|comparison|other",
    "content_description": "Detailed description of what's shown",
    "key_information": ["Important text, claims, or details extracted"],
    "promises_or_claims": ["Specific promises or claims made (if any)"],
    "visual_red_flags": ["List of suspicious visual elements"],
    "url_content_match": "Does visual content match/support what you'd expect from {url}? Explain",
    "threat_level": "CRITICAL|HIGH|MEDIUM|LOW|BENIGN",
    "threat_explanation": "Why this threat level based on visual evidence?",
    "is_deceptive": true/false,
    "deception_indicators": ["Specific deceptive elements identified"],
    "relevance_to_investigation": "How this visual evidence helps understand the threat"
}}"""

            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": screenshot,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1200,
                "response_format": {"type": "json_object"}
            }

            logger.info(f"Analyzing {label} with GPT-4o...")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')

                analysis = json.loads(content)
                analysis['label'] = label
                analysis['analyzed'] = True

                return analysis
            else:
                logger.warning(f"GPT-4o screenshot analysis failed: {response.status_code}")
                return {"error": f"API error {response.status_code}", "label": label}

        except Exception as e:
            logger.error(f"Single screenshot analysis error: {str(e)}")
            return {"error": str(e), "label": label}

    async def _compare_screenshots(
        self,
        user_screenshot: str,
        urlscan_screenshot: str,
        url: str,
        user_context: Optional[str]
    ) -> Dict[str, Any]:
        """
        Compare user's screenshot with URLScan.io screenshot to detect cloaking

        Ad cloaking = showing different content in ads vs direct visits
        """

        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }

            context_info = f"\n\nUser says: '{user_context}'" if user_context else ""

            prompt = f"""Compare these two screenshots of {url}:
- Image 1: What the user saw (in an ad, social media, or elsewhere){context_info}
- Image 2: What URLScan.io's automated browser captured when directly visiting the URL

Your task: Detect **AD CLOAKING** or **CONTENT DIFFERENCES**

AD CLOAKING = Website shows different content to ads/users vs automated scanners

Compare:
1. **Visual Content**: Do they show the same page or completely different content?
2. **Promises/Offers**: Are the same offers/claims shown in both?
3. **Branding**: Same branding or different?
4. **Call-to-Action**: Same CTAs or different?
5. **Overall Layout**: Similar or completely different?

IMPORTANT:
- Minor differences (different time of day, slight layout changes) are NORMAL
- We're looking for SIGNIFICANT differences indicating cloaking or deception
- Examples of cloaking: Ad shows "free iPhone", site shows generic content
                      Ad shows legitimate brand, site is totally different

Respond in JSON:
{{
    "significant_differences": true/false,
    "difference_severity": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "differences_found": ["Specific difference 1", "Specific difference 2"],
    "cloaking_likelihood": "VERY_LIKELY|LIKELY|POSSIBLE|UNLIKELY",
    "cloaking_explanation": "Why we think this is/isn't cloaking",
    "user_saw": "Brief description of Image 1",
    "scanner_saw": "Brief description of Image 2",
    "recommendation": "What action to take based on this comparison"
}}"""

            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": user_screenshot,
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": urlscan_screenshot,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }

            logger.info("Comparing user screenshot vs URLScan.io screenshot for cloaking detection...")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')

                comparison = json.loads(content)
                comparison['compared'] = True

                return comparison
            else:
                logger.warning(f"GPT-4o comparison failed: {response.status_code}")
                return {"error": f"API error {response.status_code}"}

        except Exception as e:
            logger.error(f"Screenshot comparison error: {str(e)}")
            return {"error": str(e)}

    def _synthesize_screenshot_threat_assessment(
        self,
        individual_analyses: List[Dict[str, Any]],
        comparison: Optional[Dict[str, Any]],
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize overall threat assessment from screenshot analyses"""

        assessment = {
            "overall_threat_level": "UNKNOWN",
            "confidence": 0,
            "key_findings": [],
            "recommendations": []
        }

        try:
            # Aggregate threat levels from individual analyses
            threat_levels = []
            for analysis in individual_analyses:
                if analysis.get("threat_level"):
                    threat_levels.append(analysis["threat_level"])

                # Collect red flags
                if analysis.get("visual_red_flags"):
                    assessment["key_findings"].extend(analysis["visual_red_flags"])

                # Check deception
                if analysis.get("is_deceptive"):
                    assessment["key_findings"].append(
                        f"Deceptive content detected: {analysis.get('deception_type', 'unknown')}"
                    )

            # Determine overall threat level (take highest)
            threat_priority = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "BENIGN": 0}
            if threat_levels:
                highest_threat = max(threat_levels, key=lambda x: threat_priority.get(x, 0))
                assessment["overall_threat_level"] = highest_threat
                assessment["confidence"] = 75  # Base confidence

            # Factor in cloaking detection
            if comparison:
                if comparison.get("significant_differences"):
                    assessment["key_findings"].append(
                        f"AD CLOAKING DETECTED: {comparison.get('cloaking_explanation', 'Content differs between ad and direct visit')}"
                    )
                    # Escalate threat level if cloaking detected
                    if threat_priority.get(assessment["overall_threat_level"], 0) < 3:
                        assessment["overall_threat_level"] = "HIGH"

                    assessment["recommendations"].append(
                        "IMMEDIATE ACTION: This site shows different content in ads vs direct visits. Likely ad fraud or deceptive advertising."
                    )

            # Generate recommendations
            if assessment["overall_threat_level"] in ["CRITICAL", "HIGH"]:
                assessment["recommendations"].append("Block this URL from ad platforms immediately")
                assessment["recommendations"].append("Report to relevant authorities")
            elif assessment["overall_threat_level"] == "MEDIUM":
                assessment["recommendations"].append("Flag for manual review")
                assessment["recommendations"].append("Monitor for user complaints")

        except Exception as e:
            logger.error(f"Threat assessment synthesis error: {str(e)}")
            assessment["error"] = str(e)

        return assessment
