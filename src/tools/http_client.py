"""Async HTTP client with user-agent support for ad-crawler simulation."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import httpx

from src.models.data_models import HTTPTestResult, TestConfig


class AsyncHTTPClient:
    """Thin wrapper around httpx for crawling tests."""

    def __init__(self, config: Optional[TestConfig] = None) -> None:
        self.config = config or TestConfig()

    async def fetch(
        self,
        url: str,
        user_agent: str,
        *,
        follow_redirects: bool = True,
        timeout: Optional[int] = None,
        proxy: Optional[str] = None,
    ) -> HTTPTestResult:
        timeout_val = timeout or self.config.timeout_seconds
        headers = {"User-Agent": user_agent}
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(
                follow_redirects=follow_redirects,
                timeout=httpx.Timeout(timeout_val),
                max_redirects=self.config.max_redirects,
                proxy=proxy,
            ) as client:
                resp = await client.get(url, headers=headers)
                elapsed = (time.monotonic() - start) * 1000
                return HTTPTestResult(
                    url=url,
                    user_agent=user_agent,
                    status_code=resp.status_code,
                    response_time_ms=round(elapsed, 2),
                    headers=dict(resp.headers),
                    content_length=len(resp.content),
                    location=resp.headers.get("location"),
                )
        except httpx.TooManyRedirects:
            elapsed = (time.monotonic() - start) * 1000
            return HTTPTestResult(
                url=url,
                user_agent=user_agent,
                status_code=0,
                response_time_ms=round(elapsed, 2),
                headers={},
                content_length=0,
                error="Too many redirects",
            )
        except httpx.TimeoutException:
            elapsed = (time.monotonic() - start) * 1000
            return HTTPTestResult(
                url=url,
                user_agent=user_agent,
                status_code=0,
                response_time_ms=round(elapsed, 2),
                headers={},
                content_length=0,
                error="Request timed out",
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = (time.monotonic() - start) * 1000
            return HTTPTestResult(
                url=url,
                user_agent=user_agent,
                status_code=0,
                response_time_ms=round(elapsed, 2),
                headers={},
                content_length=0,
                error=str(exc),
            )

    async def fetch_with_agents(
        self,
        url: str,
        user_agents: Optional[Dict[str, str]] = None,
    ) -> List[HTTPTestResult]:
        agents = user_agents or self.config.user_agents
        results: List[HTTPTestResult] = []
        for _name, ua in agents.items():
            results.append(await self.fetch(url, ua))
        return results

    async def fetch_redirect_chain(
        self, url: str, user_agent: Optional[str] = None
    ) -> List[HTTPTestResult]:
        ua = user_agent or self.config.user_agents["browser"]
        chain: List[HTTPTestResult] = []
        current = url
        seen: set[str] = set()
        for _ in range(self.config.max_redirects + 1):
            if current in seen:
                break
            seen.add(current)
            result = await self.fetch(current, ua, follow_redirects=False)
            chain.append(result)
            if result.status_code in (301, 302, 303, 307, 308) and result.location:
                current = result.location
            else:
                break
        return chain
