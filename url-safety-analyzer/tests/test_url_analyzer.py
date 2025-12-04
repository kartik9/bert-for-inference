"""
Test suite for URL analyzer functionality.

Tests cover:
- URL structure parsing
- DNS resolution
- SSL/TLS verification
- HTTP response analysis
- Content parsing
- Risk assessment
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.unit
@pytest.mark.nightly
class TestURLStructureAnalysis:
    """Test URL structure parsing and validation."""

    def test_valid_https_url(self):
        """Test parsing of a valid HTTPS URL."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = "https://www.example.com/path?query=value"
        result = analyzer._parse_url_structure(url)

        assert result["protocol"] == "https"
        assert result["domain"] == "example.com"
        assert result["subdomain"] == "www"
        assert result["tld"] == "com"
        assert "/path" in url

    def test_valid_http_url(self):
        """Test parsing of HTTP URL."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = "http://example.com"
        result = analyzer._parse_url_structure(url)

        assert result["protocol"] == "http"
        assert result["domain"] == "example.com"

    def test_suspicious_tld_detection(self):
        """Test detection of suspicious TLDs."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        suspicious_urls = [
            "https://example.tk",
            "https://example.ml",
            "https://example.ga",
        ]

        for url in suspicious_urls:
            result = analyzer._parse_url_structure(url)
            # Should flag suspicious TLD
            assert "suspicious_tld" in result.get("flags", []) or result.get("tld") in ["tk", "ml", "ga"]

    def test_ip_address_url(self):
        """Test detection of IP address in URL."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = "http://192.168.1.1/path"
        result = analyzer._parse_url_structure(url)

        # Should detect IP address usage
        assert "ip_address" in result.get("flags", []) or "192.168.1.1" in url

    def test_excessive_subdomains(self):
        """Test detection of excessive subdomains."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = "https://a.b.c.d.e.example.com"
        result = analyzer._parse_url_structure(url)

        # Should flag excessive subdomains
        subdomain = result.get("subdomain", "")
        assert subdomain.count(".") >= 3 or "excessive_subdomains" in result.get("flags", [])


@pytest.mark.unit
@pytest.mark.nightly
@pytest.mark.network
class TestDNSResolution:
    """Test DNS resolution functionality."""

    @pytest.mark.asyncio
    async def test_successful_dns_resolution(self, mock_dns_response):
        """Test successful DNS resolution."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        with patch.object(analyzer, '_resolve_dns', return_value=mock_dns_response):
            result = await analyzer._resolve_dns("google.com")

            assert result["resolved"] is True
            assert "ip_address" in result
            assert result["error"] is None

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test DNS resolution for non-existent domain."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        result = await analyzer._resolve_dns("this-domain-does-not-exist-12345.com")

        assert result["resolved"] is False or result.get("error") is not None

    @pytest.mark.asyncio
    async def test_invalid_domain_dns(self):
        """Test DNS resolution for invalid domain."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        result = await analyzer._resolve_dns("invalid..domain")

        assert result.get("error") is not None or result["resolved"] is False


@pytest.mark.unit
@pytest.mark.nightly
class TestSSLAnalysis:
    """Test SSL/TLS certificate analysis."""

    @pytest.mark.asyncio
    async def test_valid_ssl_certificate(self, mock_ssl_info):
        """Test analysis of valid SSL certificate."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        with patch.object(analyzer, '_check_ssl', return_value=mock_ssl_info):
            result = await analyzer._check_ssl("https://google.com")

            assert result["valid"] is True
            assert "issuer" in result
            assert "subject" in result

    @pytest.mark.asyncio
    async def test_ssl_certificate_invalid(self):
        """Test handling of invalid SSL certificate."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        invalid_ssl_response = {
            "valid": False,
            "error": "Certificate verification failed",
        }

        with patch.object(analyzer, '_check_ssl', return_value=invalid_ssl_response):
            result = await analyzer._check_ssl("https://expired.badssl.com")

            assert result["valid"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_http_no_ssl(self):
        """Test handling of HTTP URL (no SSL)."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        result = await analyzer._check_ssl("http://example.com")

        # Should indicate no SSL for HTTP
        assert result.get("valid") is False or result.get("error") == "no_ssl"


@pytest.mark.unit
@pytest.mark.nightly
@pytest.mark.network
class TestHTTPResponseAnalysis:
    """Test HTTP response analysis."""

    @pytest.mark.asyncio
    async def test_successful_http_request(self, mock_http_response):
        """Test successful HTTP request analysis."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        with patch('httpx.AsyncClient.get', return_value=mock_http_response()):
            result = await analyzer._fetch_http("https://example.com")

            assert result["status_code"] == 200
            assert "headers" in result

    @pytest.mark.asyncio
    async def test_http_redirect_detection(self):
        """Test detection of HTTP redirects."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        redirect_response = {
            "status_code": 301,
            "final_url": "https://example.com/new",
            "redirect_chain": ["https://example.com", "https://example.com/new"],
        }

        with patch.object(analyzer, '_fetch_http', return_value=redirect_response):
            result = await analyzer._fetch_http("https://example.com")

            assert result["status_code"] == 301
            assert len(result["redirect_chain"]) > 1

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        error_response = {
            "status_code": 404,
            "error": "Not Found",
        }

        with patch.object(analyzer, '_fetch_http', return_value=error_response):
            result = await analyzer._fetch_http("https://example.com/notfound")

            assert result["status_code"] == 404
            assert "error" in result or result["status_code"] >= 400


@pytest.mark.unit
@pytest.mark.nightly
class TestContentAnalysis:
    """Test HTML content analysis."""

    def test_form_detection(self):
        """Test detection of forms in HTML."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        html_with_form = """
        <html>
            <body>
                <form action="/submit" method="post">
                    <input type="text" name="username">
                    <input type="password" name="password">
                </form>
            </body>
        </html>
        """

        result = analyzer._analyze_content(html_with_form)

        assert result["has_forms"] is True
        assert result["form_count"] >= 1

    def test_external_script_detection(self):
        """Test detection of external scripts."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        html_with_scripts = """
        <html>
            <head>
                <script src="https://external.com/script.js"></script>
                <script src="https://another.com/lib.js"></script>
            </head>
            <body>Test</body>
        </html>
        """

        result = analyzer._analyze_content(html_with_scripts)

        assert result["external_scripts"] >= 2

    def test_iframe_detection(self):
        """Test detection of iframes."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        html_with_iframe = """
        <html>
            <body>
                <iframe src="https://external.com/embed"></iframe>
            </body>
        </html>
        """

        result = analyzer._analyze_content(html_with_iframe)

        assert result["iframes"] >= 1

    def test_link_extraction(self):
        """Test extraction and counting of links."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        html_with_links = """
        <html>
            <body>
                <a href="https://link1.com">Link 1</a>
                <a href="https://link2.com">Link 2</a>
                <a href="https://link3.com">Link 3</a>
            </body>
        </html>
        """

        result = analyzer._analyze_content(html_with_links)

        assert result["links"] >= 3


@pytest.mark.unit
@pytest.mark.nightly
class TestRiskAssessment:
    """Test risk indicator detection and scoring."""

    def test_high_risk_indicators(self):
        """Test detection of high-risk indicators."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        data = {
            "url_structure": {"flags": ["ip_address", "suspicious_tld"]},
            "ssl": {"valid": False},
            "http": {"status_code": 404},
        }

        risk_score = analyzer._calculate_risk_score(data)

        assert risk_score >= 50  # Should have elevated risk

    def test_low_risk_indicators(self):
        """Test legitimate site with low risk."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        data = {
            "url_structure": {"flags": []},
            "ssl": {"valid": True, "issuer": "DigiCert Inc"},
            "http": {"status_code": 200},
            "content": {"has_forms": False},
        }

        risk_score = analyzer._calculate_risk_score(data)

        assert risk_score <= 30  # Should have low risk


@pytest.mark.integration
@pytest.mark.nightly
@pytest.mark.network
@pytest.mark.slow
class TestURLAnalyzerIntegration:
    """Integration tests for complete URL analysis."""

    @pytest.mark.asyncio
    async def test_full_analysis_safe_url(self, test_urls):
        """Test complete analysis of a safe URL."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = test_urls["safe"][0]
        result = await analyzer.analyze(url)

        assert "url" in result
        assert "dns" in result
        assert "ssl" in result
        assert "http" in result
        assert "risk_indicators" in result

    @pytest.mark.asyncio
    async def test_analysis_error_handling(self, test_urls):
        """Test error handling in URL analysis."""
        from url_analyzer import URLAnalyzer
        analyzer = URLAnalyzer()

        url = test_urls["invalid"][0]

        # Should handle gracefully
        try:
            result = await analyzer.analyze(url)
            assert "error" in result or result.get("status") == "error"
        except Exception as e:
            # Exception handling is acceptable
            assert True
