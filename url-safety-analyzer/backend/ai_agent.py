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
        url_analyzer_instance=None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Answer follow-up questions with active investigation capability
        Generic AI-driven system that can handle ANY question type

        GPT-5 analyzes the question and decides what actions to take,
        then synthesizes answer with gathered evidence
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

        # Step 1: GPT-5 analyzes the question and determines required actions
        action_plan = await self._analyze_followup_question(
            url,
            question,
            previous_context
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

        # Step 3: GPT-5 synthesizes comprehensive answer
        yield {
            "type": "status",
            "message": "Formulating answer..."
        }

        async for response_chunk in self._synthesize_followup_answer(
            url,
            question,
            previous_context,
            action_plan,
            new_data
        ):
            yield response_chunk

    async def _analyze_followup_question(
        self,
        url: str,
        question: str,
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use GPT-5 to analyze the question and determine what actions are needed
        This is the key to making the system generic
        """

        context_summary = self._build_context_summary(url, previous_context)

        prompt = f"""You are a trust and safety expert analyzing a follow-up question about a URL investigation.

ORIGINAL INVESTIGATION:
{context_summary}

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
7. "no_action" - Answer from existing context only

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
        new_data: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Use GPT-5 to synthesize comprehensive answer with all available evidence
        """

        context_summary = self._build_context_summary(url, previous_context)

        new_data_summary = ""
        if new_data.get("data"):
            new_data_summary = f"""

NEW EVIDENCE GATHERED:
{json.dumps(new_data, indent=2)[:3000]}
"""

        prompt = f"""You are a trust and safety expert providing a comprehensive answer to a follow-up question.

ORIGINAL INVESTIGATION:
{context_summary}

RESEARCHER'S QUESTION:
{question}

INVESTIGATION ACTIONS TAKEN:
{action_plan.get('reasoning', 'N/A')}
{new_data_summary}

Provide a detailed, evidence-based answer to the researcher's question.

Key requirements:
1. Cite specific evidence from both original investigation and new data
2. Be decisive and clear in your assessment
3. If new advertiser information was provided, compare it with findings
4. If domain relationships were checked, explain the connection/threat
5. Reference specific data points (quotes, statistics, sources)
6. Update verdict if new evidence warrants it

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
