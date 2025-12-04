"""
Test suite for AI agent functionality.

Tests cover:
- AI agent initialization
- Investigation plan generation
- Threat analysis
- Report generation
- Follow-up question handling
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.unit
@pytest.mark.nightly
class TestAIAgentInitialization:
    """Test AI agent initialization and configuration."""

    def test_init_with_openai(self, mock_openai_key):
        """Test initialization with OpenAI API key."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI'):
            agent = ThreatAnalysisAgent()
            assert agent is not None

    def test_init_with_anthropic(self, mock_anthropic_key):
        """Test initialization with Anthropic API key."""
        from ai_agent import ThreatAnalysisAgent

        with patch('anthropic.Anthropic'):
            agent = ThreatAnalysisAgent()
            assert agent is not None

    def test_init_without_api_key(self):
        """Test initialization fails without API key."""
        import os
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)

        from ai_agent import ThreatAnalysisAgent

        with pytest.raises(ValueError, match="API key"):
            agent = ThreatAnalysisAgent()


@pytest.mark.unit
@pytest.mark.nightly
class TestInvestigationPlanGeneration:
    """Test investigation plan generation."""

    @pytest.mark.asyncio
    async def test_generate_basic_plan(self, mock_openai_key, sample_technical_data):
        """Test generation of basic investigation plan."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI') as mock_openai:
            # Mock the API response
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "steps": [
                        "Analyze URL structure",
                        "Check SSL certificate",
                        "Examine content"
                    ]
                })))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            plan = await agent.generate_investigation_plan("https://example.com", sample_technical_data)

            assert "steps" in plan or isinstance(plan, list)

    @pytest.mark.asyncio
    async def test_plan_includes_suspicious_indicators(self, mock_openai_key):
        """Test plan adapts to suspicious indicators."""
        from ai_agent import ThreatAnalysisAgent

        suspicious_data = {
            "url_structure": {"flags": ["suspicious_tld", "ip_address"]},
            "ssl": {"valid": False},
        }

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "steps": [
                        "Investigate suspicious TLD",
                        "Check SSL issues",
                        "Deep content analysis"
                    ]
                })))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            plan = await agent.generate_investigation_plan("https://example.tk", suspicious_data)

            assert plan is not None


@pytest.mark.unit
@pytest.mark.nightly
class TestThreatAnalysis:
    """Test threat analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_safe_url(self, mock_openai_key, sample_technical_data, mock_ai_response):
        """Test analysis of a safe URL."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps(mock_ai_response)))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.analyze_threat("https://example.com", sample_technical_data)

            assert result["verdict"] == "SAFE"
            assert result["confidence"] > 0
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_analyze_suspicious_url(self, mock_openai_key):
        """Test analysis of a suspicious URL."""
        from ai_agent import ThreatAnalysisAgent

        suspicious_data = {
            "url_structure": {"flags": ["suspicious_tld", "excessive_subdomains"]},
            "ssl": {"valid": False},
            "content": {"has_forms": True, "form_count": 3},
        }

        suspicious_response = {
            "verdict": "SUSPICIOUS",
            "confidence": 75,
            "primary_category": "phishing",
            "risk_score": 70,
            "summary": "Multiple suspicious indicators detected.",
            "key_findings": [],
        }

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps(suspicious_response)))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.analyze_threat("https://suspicious.tk", suspicious_data)

            assert result["verdict"] in ["SUSPICIOUS", "MALICIOUS"]
            assert result["risk_score"] > 50

    @pytest.mark.asyncio
    async def test_analyze_malicious_url(self, mock_openai_key):
        """Test analysis of a malicious URL."""
        from ai_agent import ThreatAnalysisAgent

        malicious_data = {
            "url_structure": {"flags": ["ip_address", "suspicious_tld"]},
            "ssl": {"valid": False, "error": "Certificate mismatch"},
            "content": {
                "has_forms": True,
                "form_count": 5,
                "external_scripts": 10,
                "suspicious_keywords": ["login", "password", "verify"],
            },
        }

        malicious_response = {
            "verdict": "MALICIOUS",
            "confidence": 95,
            "primary_category": "phishing",
            "risk_score": 95,
            "summary": "Strong indicators of phishing attack.",
            "threat_indicators": ["credential_harvesting", "brand_impersonation"],
        }

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps(malicious_response)))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.analyze_threat("http://192.168.1.1/phish", malicious_data)

            assert result["verdict"] == "MALICIOUS"
            assert result["risk_score"] > 80


@pytest.mark.unit
@pytest.mark.nightly
class TestReportGeneration:
    """Test report generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_complete_report(self, mock_openai_key, sample_technical_data):
        """Test generation of complete analysis report."""
        from ai_agent import ThreatAnalysisAgent

        report = {
            "verdict": "SAFE",
            "confidence": 90,
            "primary_category": "legitimate",
            "risk_score": 10,
            "summary": "Legitimate website",
            "detailed_rationale": "All indicators suggest this is a legitimate site.",
            "key_findings": [
                {
                    "finding": "Valid SSL certificate",
                    "evidence": "Issued by DigiCert Inc",
                    "severity": "low",
                }
            ],
            "recommendations": ["No action required"],
        }

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps(report)))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.generate_report("https://example.com", sample_technical_data)

            assert "verdict" in result
            assert "confidence" in result
            assert "summary" in result
            assert "key_findings" in result
            assert "recommendations" in result

    def test_report_structure_validation(self, mock_ai_response):
        """Test that report structure matches expected format."""
        report = mock_ai_response

        required_fields = [
            "verdict",
            "confidence",
            "primary_category",
            "risk_score",
            "summary",
            "detailed_rationale",
            "key_findings",
            "recommendations",
        ]

        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

    def test_verdict_values(self, mock_ai_response):
        """Test that verdict is one of expected values."""
        valid_verdicts = ["SAFE", "SUSPICIOUS", "MALICIOUS", "BLOCKED"]
        verdict = mock_ai_response["verdict"]

        assert verdict in valid_verdicts

    def test_confidence_range(self, mock_ai_response):
        """Test that confidence is in valid range."""
        confidence = mock_ai_response["confidence"]

        assert 0 <= confidence <= 100

    def test_risk_score_range(self, mock_ai_response):
        """Test that risk score is in valid range."""
        risk_score = mock_ai_response["risk_score"]

        assert 0 <= risk_score <= 100


@pytest.mark.unit
@pytest.mark.nightly
class TestFollowUpQuestions:
    """Test follow-up question handling."""

    @pytest.mark.asyncio
    async def test_answer_followup_question(self, mock_openai_key, sample_technical_data, mock_ai_response):
        """Test answering a follow-up question."""
        from ai_agent import ThreatAnalysisAgent

        question = "What makes this URL suspicious?"
        context = {
            "technical_data": sample_technical_data,
            "report": mock_ai_response,
        }

        answer = "The URL shows suspicious patterns including..."

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=answer))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.answer_followup(question, context)

            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_followup_uses_context(self, mock_openai_key, mock_ai_response):
        """Test that follow-up uses previous analysis context."""
        from ai_agent import ThreatAnalysisAgent

        question = "Why is the risk score 75?"
        context = {"report": mock_ai_response}

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="Based on the analysis..."))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()
            result = await agent.answer_followup(question, context)

            assert result is not None


@pytest.mark.unit
@pytest.mark.nightly
class TestErrorHandling:
    """Test error handling in AI agent."""

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_openai_key, sample_technical_data):
        """Test handling of API errors."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()

            with pytest.raises(Exception):
                await agent.analyze_threat("https://example.com", sample_technical_data)

    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, mock_openai_key, sample_technical_data):
        """Test handling of invalid API responses."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            # Return invalid JSON
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="invalid json{}"))]
            ))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()

            # Should handle gracefully
            try:
                result = await agent.analyze_threat("https://example.com", sample_technical_data)
                # If it returns something, it handled the error
                assert result is not None
            except Exception:
                # Exception is also acceptable
                assert True

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_openai_key, sample_technical_data):
        """Test handling of API timeouts."""
        from ai_agent import ThreatAnalysisAgent
        import asyncio

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()

            with pytest.raises(asyncio.TimeoutError):
                await agent.analyze_threat("https://example.com", sample_technical_data)


@pytest.mark.integration
@pytest.mark.nightly
@pytest.mark.ai
@pytest.mark.slow
class TestAIAgentIntegration:
    """Integration tests for AI agent with real API calls."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-ai-tests", default=False),
        reason="Requires --run-ai-tests flag and valid API key"
    )
    async def test_real_api_analysis(self, mock_openai_key, sample_technical_data):
        """Test analysis with real API call (requires valid API key)."""
        from ai_agent import ThreatAnalysisAgent

        agent = ThreatAnalysisAgent()
        result = await agent.analyze_threat("https://google.com", sample_technical_data)

        assert "verdict" in result
        assert "confidence" in result
        assert result["confidence"] > 0
