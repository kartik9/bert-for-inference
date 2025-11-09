"""
AI Safety Analysis Agent with Token Metrics Tracking
Extends SafetyAnalysisAgent to track GPT token consumption
"""

import os
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, List
from datetime import datetime

from openai import AsyncOpenAI
import httpx

from ai_agent import SafetyAnalysisAgent
from token_metrics import TokenMetricsTracker, TokenUsage

logger = logging.getLogger(__name__)


class SafetyAnalysisAgentWithMetrics(SafetyAnalysisAgent):
    """
    Extended AI agent with comprehensive token metrics tracking

    Tracks all OpenAI API calls with:
    - Model-specific token usage
    - Text vs Image token breakdown
    - Operation-level metrics
    - Cost estimation
    """

    def __init__(self, metrics_tracker: Optional[TokenMetricsTracker] = None):
        """
        Initialize AI client with metrics tracking

        Args:
            metrics_tracker: Optional TokenMetricsTracker instance. If None, creates new one.
        """
        super().__init__()
        self.metrics_tracker = metrics_tracker or TokenMetricsTracker()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def create_investigation_plan(
        self, url: str, technical_data: Dict[str, Any]
    ) -> List[str]:
        """Create investigation plan with token tracking"""
        if not self.is_configured():
            return await super().create_investigation_plan(url, technical_data)

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

            # Track token usage
            self.metrics_tracker.track_from_response(
                response,
                model=self.model,
                operation="create_investigation_plan",
                metadata={"url": url}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("investigation_steps", [
                "Analyze technical indicators",
                "Investigate web reputation",
                "Assess threat level"
            ])

        except Exception as e:
            logger.error(f"GPT-5 investigation plan error: {str(e)}")
            return [
                "Analyze domain and hosting infrastructure for anomalies",
                "Examine URL structure for brand impersonation patterns",
                "Investigate SSL/TLS certificate validity and trust",
                "Review web content for malicious elements and social engineering",
                "Analyze web reputation and user complaints",
                "Assess overall risk level and threat classification"
            ]

    async def investigate_url_iterative(
        self,
        url: str,
        technical_data: Dict[str, Any],
        investigation_plan: List[str],
        url_analyzer_instance=None,
        max_iterations: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Iterative investigation with token tracking"""

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
            yield {
                "type": "iteration",
                "iteration": iteration,
                "max_iterations": max_iterations,
                "message": f"Investigation Round {iteration}/{max_iterations}"
            }

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

                # Stream investigation with token tracking
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
                    stream=True,
                    stream_options={"include_usage": True}  # Get usage stats with streaming
                )

                # Track streaming tokens
                total_prompt_tokens = 0
                total_completion_tokens = 0

                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
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

                    # Capture usage stats if provided
                    if hasattr(chunk, 'usage') and chunk.usage:
                        total_prompt_tokens = chunk.usage.prompt_tokens
                        total_completion_tokens = chunk.usage.completion_tokens

                # Track tokens for this investigation round
                usage = TokenUsage(
                    prompt_tokens=total_prompt_tokens,
                    completion_tokens=total_completion_tokens,
                    total_tokens=total_prompt_tokens + total_completion_tokens,
                    text_tokens=total_prompt_tokens + total_completion_tokens,
                    image_tokens=0
                )
                self.metrics_tracker.track_api_call(
                    model=self.model,
                    usage=usage,
                    operation=f"investigate_iteration_{iteration}",
                    metadata={"url": url, "iteration": iteration}
                )

                investigation_history.append({
                    "iteration": iteration,
                    "reasoning": collected_reasoning[:500]
                })

                # Assess confidence
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

                # Plan follow-up if needed
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

                    # Execute follow-up actions
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
        """Assess confidence with token tracking"""

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

            # Track token usage
            self.metrics_tracker.track_from_response(
                response,
                model=self.model,
                operation="assess_confidence",
                metadata={"url": url, "iteration": iteration}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Confidence assessment error: {str(e)}")
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
        """Plan follow-up actions with token tracking"""

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

            # Track token usage
            self.metrics_tracker.track_from_response(
                response,
                model=self.model,
                operation="plan_followup_actions",
                metadata={"url": url}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"Follow-up planning error: {str(e)}")
            return {
                "actions": [],
                "reasoning": f"Unable to plan follow-up actions due to error: {str(e)}"
            }

    async def generate_report(
        self,
        url: str,
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate report with token tracking"""

        if not self.is_configured():
            return self._generate_fallback_report(url, technical_data)

        # Use parent class method but track tokens
        # Build the same prompt as parent class
        prompt = self._build_report_prompt(url, technical_data)

        try:
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

            # Track token usage
            self.metrics_tracker.track_from_response(
                response,
                model=self.model,
                operation="generate_report",
                metadata={"url": url}
            )

            report_text = response.choices[0].message.content.strip()
            report = json.loads(report_text)
            return report

        except Exception as e:
            logger.error(f"GPT-5 report generation error: {str(e)}")
            return self._generate_fallback_report(url, technical_data)

    def _build_report_prompt(self, url: str, technical_data: Dict[str, Any]) -> str:
        """Build report generation prompt (simplified version)"""
        return f"""Based on the complete investigation of URL: {url}

Technical Data Summary:
{json.dumps(technical_data, indent=2)[:3000]}

Generate a comprehensive final report in JSON format with verdict, confidence, risk assessment, and findings."""

    async def _analyze_user_screenshots(
        self,
        url: str,
        screenshots: List[str],
        screenshot_context: Optional[str],
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze screenshots with token tracking (tracks image tokens)"""

        if not screenshots:
            return None

        try:
            result = {
                "individual_analysis": [],
                "cloaking_detected": False,
                "comparison_with_urlscan": None,
                "threat_assessment": {},
                "user_context": screenshot_context or "No context provided"
            }

            # Analyze each screenshot
            for idx, screenshot in enumerate(screenshots):
                analysis = await self._analyze_single_screenshot(
                    screenshot,
                    url,
                    screenshot_context,
                    f"User Screenshot {idx + 1}"
                )

                if analysis:
                    result["individual_analysis"].append(analysis)

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
        """Analyze single screenshot with token tracking (GPT-4o with image)"""

        try:
            context_info = f"\n\nUSER CONTEXT: {context}" if context else ""

            prompt = f"""Analyze this screenshot related to the URL: {url}
{context_info}

Analyze comprehensively for trust & safety concerns. Return JSON with threat analysis."""

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

            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                http_response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )

            if http_response.status_code == 200:
                result = http_response.json()

                # Track token usage (with image tokens)
                usage_data = result.get('usage', {})
                usage = TokenUsage(
                    prompt_tokens=usage_data.get('prompt_tokens', 0),
                    completion_tokens=usage_data.get('completion_tokens', 0),
                    total_tokens=usage_data.get('total_tokens', 0)
                )

                # Estimate image tokens (rough approximation)
                # High detail images: ~765 tokens, low detail: ~85 tokens
                estimated_image_tokens = 765  # High detail
                usage.image_tokens = estimated_image_tokens
                usage.text_tokens = usage.total_tokens - estimated_image_tokens

                self.metrics_tracker.track_api_call(
                    model="gpt-4o",
                    usage=usage,
                    operation="analyze_screenshot",
                    metadata={
                        "url": url,
                        "has_images": True,
                        "estimated_image_tokens": estimated_image_tokens
                    }
                )

                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                analysis = json.loads(content)
                analysis['label'] = label
                analysis['analyzed'] = True

                return analysis
            else:
                logger.warning(f"GPT-4o screenshot analysis failed: {http_response.status_code}")
                return {"error": f"API error {http_response.status_code}", "label": label}

        except Exception as e:
            logger.error(f"Single screenshot analysis error: {str(e)}")
            return {"error": str(e), "label": label}

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get token metrics summary for this agent"""
        return self.metrics_tracker.get_summary()

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        self.metrics_tracker.export_to_json(filepath)

    def print_metrics(self):
        """Print metrics summary"""
        self.metrics_tracker.print_summary()
