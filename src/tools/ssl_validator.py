"""SSL/TLS certificate validation tool."""

from __future__ import annotations

import ssl
import socket
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from src.models.data_models import SSLTestResult


class SSLValidator:
    """Validate SSL/TLS certificates."""

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _extract_host_port(self, url: str) -> tuple[str, int]:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        host = parsed.hostname or url
        port = parsed.port or 443
        return host, port

    async def validate(self, url: str) -> SSLTestResult:
        host, port = self._extract_host_port(url)
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

            if not cert:
                return SSLTestResult(url=url, valid=False, error="No certificate returned")

            # Parse dates
            not_before = datetime.strptime(
                cert["notBefore"], "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=timezone.utc)
            not_after = datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=timezone.utc)
            days_left = (not_after - datetime.now(timezone.utc)).days

            issuer_parts = dict(x[0] for x in cert.get("issuer", ()))
            subject_parts = dict(x[0] for x in cert.get("subject", ()))

            return SSLTestResult(
                url=url,
                valid=days_left > 0,
                issuer=issuer_parts.get("organizationName"),
                subject=subject_parts.get("commonName"),
                not_before=not_before,
                not_after=not_after,
                days_until_expiry=days_left,
                protocol_version=version,
                cipher_suite=cipher[0] if cipher else None,
            )
        except ssl.SSLCertVerificationError as exc:
            return SSLTestResult(url=url, valid=False, error=f"Certificate verification failed: {exc}")
        except ssl.SSLError as exc:
            return SSLTestResult(url=url, valid=False, error=f"SSL error: {exc}")
        except socket.timeout:
            return SSLTestResult(url=url, valid=False, error="Connection timed out")
        except Exception as exc:  # noqa: BLE001
            return SSLTestResult(url=url, valid=False, error=str(exc))
