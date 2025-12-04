"""
Pytest configuration and shared fixtures for URL Safety Analyzer tests.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import httpx

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.fixture(scope="session")
def test_urls():
    """Fixture providing safe test URLs."""
    return {
        "safe": [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.wikipedia.org",
        ],
        "http_only": [
            "http://example.com",
        ],
        "suspicious_patterns": [
            "http://192.168.1.1",  # IP address
            "https://example.tk",  # Suspicious TLD
        ],
        "invalid": [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "",
        ],
    }


@pytest.fixture
def mock_http_response():
    """Fixture providing a mock HTTP response."""
    def _create_response(
        status_code=200,
        content=b"<html><body>Test</body></html>",
        headers=None,
    ):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.content = content
        response.text = content.decode('utf-8') if isinstance(content, bytes) else content
        response.headers = headers or {"content-type": "text/html"}
        response.url = "https://example.com"
        return response
    return _create_response


@pytest.fixture
def mock_dns_response():
    """Fixture providing mock DNS response data."""
    return {
        "ip_address": "93.184.216.34",
        "resolved": True,
        "error": None,
    }


@pytest.fixture
def mock_ssl_info():
    """Fixture providing mock SSL certificate info."""
    return {
        "valid": True,
        "issuer": "DigiCert Inc",
        "subject": "example.com",
        "expiration": "2025-12-31",
        "san": ["example.com", "www.example.com"],
    }


@pytest.fixture
def mock_whois_info():
    """Fixture providing mock WHOIS data."""
    return {
        "domain_name": "example.com",
        "registrar": "Example Registrar, Inc.",
        "creation_date": "1995-08-14",
        "expiration_date": "2025-08-13",
        "name_servers": ["ns1.example.com", "ns2.example.com"],
    }


@pytest.fixture
def mock_ai_response():
    """Fixture providing mock AI API response."""
    return {
        "verdict": "SAFE",
        "confidence": 95,
        "primary_category": "legitimate",
        "secondary_categories": [],
        "risk_score": 5,
        "summary": "This URL appears to be safe and legitimate.",
        "detailed_rationale": "Based on the analysis, this URL shows no signs of malicious activity.",
        "key_findings": [
            {
                "finding": "Valid SSL certificate",
                "evidence": "Certificate issued by trusted CA",
                "severity": "low",
                "citation": "ssl_analysis",
            }
        ],
        "recommendations": ["No action required"],
        "threat_indicators": [],
        "timestamp": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
async def mock_url_analyzer():
    """Fixture providing a mock URL analyzer."""
    from url_analyzer import URLAnalyzer

    analyzer = Mock(spec=URLAnalyzer)
    analyzer.analyze = AsyncMock(return_value={
        "url": "https://example.com",
        "dns": {"ip_address": "93.184.216.34", "resolved": True},
        "ssl": {"valid": True, "issuer": "DigiCert Inc"},
        "http": {"status_code": 200, "redirects": []},
        "content": {"has_forms": False, "external_scripts": 0},
        "risk_indicators": [],
    })
    return analyzer


@pytest.fixture
def mock_ai_client():
    """Fixture providing a mock AI client (OpenAI/Anthropic)."""
    client = Mock()

    # Mock OpenAI-style completion
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock(return_value=Mock(
        choices=[Mock(
            message=Mock(content='{"verdict": "SAFE", "confidence": 95}')
        )]
    ))

    return client


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Fixture providing a temporary cache directory."""
    cache_dir = tmp_path / "url_cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def sample_technical_data():
    """Fixture providing sample technical analysis data."""
    return {
        "url_structure": {
            "protocol": "https",
            "domain": "example.com",
            "subdomain": "www",
            "tld": "com",
            "path": "/test",
            "suspicious_patterns": [],
        },
        "dns": {
            "ip_address": "93.184.216.34",
            "resolved": True,
            "error": None,
        },
        "ssl": {
            "valid": True,
            "issuer": "DigiCert Inc",
            "subject": "example.com",
            "expiration": "2025-12-31",
        },
        "http": {
            "status_code": 200,
            "final_url": "https://example.com/test",
            "redirect_chain": [],
            "headers": {
                "server": "nginx",
                "content-type": "text/html",
            },
        },
        "content": {
            "title": "Example Domain",
            "has_forms": False,
            "form_count": 0,
            "external_scripts": 0,
            "iframes": 0,
            "links": 3,
        },
        "risk_indicators": [],
    }


@pytest.fixture
def sample_dataset_entry():
    """Fixture providing a sample dataset entry for evaluation."""
    return {
        "url": "https://example.com",
        "label": "safe",
        "category": "legitimate",
        "source": "test",
        "metadata": {
            "added_date": "2024-01-01",
            "verified": True,
        },
    }


@pytest.fixture(autouse=True)
def reset_env():
    """Auto-use fixture to reset environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Fixture to set a mock OpenAI API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")


@pytest.fixture
def mock_anthropic_key(monkeypatch):
    """Fixture to set a mock Anthropic API key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
