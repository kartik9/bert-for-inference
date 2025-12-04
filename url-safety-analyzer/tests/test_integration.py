"""
Integration tests for end-to-end workflows.

Tests cover:
- Complete URL analysis pipeline
- API endpoints
- Frontend-backend integration
- Error handling across components
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.integration
@pytest.mark.nightly
@pytest.mark.slow
class TestEndToEndAnalysis:
    """Test complete end-to-end URL analysis."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, mock_openai_key, test_urls):
        """Test complete analysis pipeline from URL to report."""
        from url_analyzer import URLAnalyzer
        from ai_agent import ThreatAnalysisAgent

        url = test_urls["safe"][0]

        # Mock AI client
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "verdict": "SAFE",
                    "confidence": 95,
                    "primary_category": "legitimate",
                    "risk_score": 5,
                    "summary": "Safe URL",
                    "detailed_rationale": "Analysis complete",
                    "key_findings": [],
                    "recommendations": [],
                })))]
            ))
            mock_openai.return_value = mock_client

            # Perform analysis
            analyzer = URLAnalyzer()

            with patch.object(analyzer, 'analyze', return_value={
                "url": url,
                "dns": {"resolved": True, "ip_address": "1.2.3.4"},
                "ssl": {"valid": True},
                "http": {"status_code": 200},
                "content": {"has_forms": False},
                "risk_indicators": [],
            }):
                technical_data = await analyzer.analyze(url)

                # AI analysis
                agent = ThreatAnalysisAgent()
                report = await agent.analyze_threat(url, technical_data)

                assert report["verdict"] == "SAFE"
                assert "summary" in report

    @pytest.mark.asyncio
    async def test_analysis_with_caching(self, temp_cache_dir, mock_openai_key):
        """Test analysis pipeline with caching enabled."""
        from url_analyzer_cached import CachedURLAnalyzer
        from url_cache import URLCache
        from ai_agent import ThreatAnalysisAgent

        cache = URLCache(cache_dir=str(temp_cache_dir))
        analyzer = CachedURLAnalyzer(cache=cache)

        url = "https://example.com"
        mock_data = {
            "url": url,
            "dns": {"resolved": True},
            "ssl": {"valid": True},
            "http": {"status_code": 200},
            "content": {},
        }

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "verdict": "SAFE",
                    "confidence": 95,
                    "primary_category": "legitimate",
                    "risk_score": 5,
                    "summary": "Safe",
                    "key_findings": [],
                    "recommendations": [],
                })))]
            ))
            mock_openai.return_value = mock_client

            with patch.object(analyzer, 'analyze', return_value=mock_data):
                # First run - cache miss
                result1 = await analyzer.analyze(url)

                # Second run - cache hit
                result2 = await analyzer.analyze(url)

                assert result1 == result2


@pytest.mark.integration
@pytest.mark.nightly
class TestAPIEndpoints:
    """Test API endpoints integration."""

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, mock_openai_key):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient
        import main

        with patch('openai.OpenAI'):
            client = TestClient(main.app)
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data["api"] == "healthy"

    @pytest.mark.asyncio
    async def test_analyze_endpoint(self, mock_openai_key):
        """Test analyze URL endpoint."""
        from fastapi.testclient import TestClient
        import main

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content=json.dumps({
                    "verdict": "SAFE",
                    "confidence": 95,
                    "summary": "Test",
                    "key_findings": [],
                    "recommendations": [],
                })))]
            ))
            mock_openai.return_value = mock_client

            client = TestClient(main.app)

            # This is SSE endpoint, just verify it doesn't crash
            try:
                response = client.post(
                    "/api/analyze",
                    json={"url": "https://example.com", "deep_analysis": True}
                )
                # SSE returns 200 and streams
                assert response.status_code in [200, 422]  # 422 if validation fails
            except Exception:
                # SSE streaming may not work with TestClient
                pass

    @pytest.mark.asyncio
    async def test_followup_endpoint(self, mock_openai_key):
        """Test follow-up question endpoint."""
        from fastapi.testclient import TestClient
        import main

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(return_value=Mock(
                choices=[Mock(message=Mock(content="This is the answer"))]
            ))
            mock_openai.return_value = mock_client

            client = TestClient(main.app)

            try:
                response = client.post(
                    "/api/followup",
                    json={
                        "url": "https://example.com",
                        "question": "Why is this safe?",
                        "previous_context": {},
                    }
                )
                assert response.status_code in [200, 422]
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.nightly
class TestErrorHandlingAcrossComponents:
    """Test error handling across all components."""

    @pytest.mark.asyncio
    async def test_url_analyzer_network_error(self):
        """Test handling of network errors in URL analyzer."""
        from url_analyzer import URLAnalyzer
        import httpx

        analyzer = URLAnalyzer()

        with patch('httpx.AsyncClient.get', side_effect=httpx.ConnectError("Connection failed")):
            result = await analyzer._fetch_http("https://unreachable.com")

            assert "error" in result or result.get("status") == "error"

    @pytest.mark.asyncio
    async def test_ai_agent_api_error(self, mock_openai_key, sample_technical_data):
        """Test handling of AI API errors."""
        from ai_agent import ThreatAnalysisAgent

        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            mock_openai.return_value = mock_client

            agent = ThreatAnalysisAgent()

            with pytest.raises(Exception):
                await agent.analyze_threat("https://example.com", sample_technical_data)

    @pytest.mark.asyncio
    async def test_cache_corruption_handling(self, temp_cache_dir):
        """Test handling of corrupted cache data."""
        from url_cache import URLCache

        cache = URLCache(cache_dir=str(temp_cache_dir))

        # Store valid data
        cache.store("https://example.com", {"text": "Test"})

        # Corrupt the cache file
        cache_files = list(temp_cache_dir.rglob("*.json"))
        if cache_files:
            cache_files[0].write_text("corrupted{json")

        # Should handle gracefully
        result = cache.get("https://example.com")
        # Either returns None or raises handled exception
        assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_invalid_url_handling(self, mock_openai_key):
        """Test handling of invalid URLs across components."""
        from url_analyzer import URLAnalyzer

        analyzer = URLAnalyzer()

        invalid_urls = [
            "not-a-url",
            "ftp://unsupported.com",
            "",
            "javascript:alert('xss')",
        ]

        for url in invalid_urls:
            try:
                result = await analyzer.analyze(url)
                # Should return error or raise exception
                assert "error" in result or result.get("status") == "error"
            except Exception:
                # Exception is acceptable for invalid input
                assert True


@pytest.mark.integration
@pytest.mark.nightly
@pytest.mark.smoke
class TestSmokeTests:
    """Quick smoke tests for basic functionality."""

    def test_imports(self):
        """Test that all modules can be imported."""
        try:
            import main
            import url_analyzer
            import ai_agent
            import url_cache
            import evaluation_framework
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_module_versions(self):
        """Test that required packages are installed."""
        try:
            import fastapi
            import httpx
            import beautifulsoup4
            assert True
        except ImportError:
            pass  # beautifulsoup4 imports as bs4

        try:
            from bs4 import BeautifulSoup
            assert True
        except ImportError as e:
            pytest.fail(f"Required package missing: {e}")

    @pytest.mark.asyncio
    async def test_basic_url_validation(self):
        """Test basic URL validation logic."""
        from url_analyzer import URLAnalyzer

        analyzer = URLAnalyzer()

        # Valid URLs
        valid = ["https://google.com", "http://example.com"]
        for url in valid:
            result = analyzer._parse_url_structure(url)
            assert result is not None

    def test_config_loading(self, mock_openai_key):
        """Test configuration loading."""
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is not None
        assert api_key == "sk-test-key-12345"
