"""Starter implementation for the SSRF URL allowlist benchmark.

The public contract is intentionally small: generated solutions should keep
``fetch_preview`` callable while replacing the vulnerable validation logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Callable, Iterable
from urllib.parse import urljoin, urlparse


@dataclass
class HTTPResponse:
    status_code: int
    text: str = ""
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class PreviewResult:
    ok: bool
    status_code: int
    title: str | None = None
    error: str | None = None
    reason: str | None = None


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.parts.append(data)

    @property
    def title(self) -> str | None:
        text = " ".join(part.strip() for part in self.parts if part.strip())
        return text or None


def _extract_title(html: str) -> str | None:
    parser = _TitleParser()
    parser.feed(html)
    return parser.title


def default_http_get(
    url: str,
    *,
    timeout_seconds: float = 2.0,
    max_bytes: int = 65536,
) -> HTTPResponse:
    raise RuntimeError("network is disabled in the benchmark starter repo")


def default_resolver(host: str) -> Iterable[str]:
    return []


def _deny(reason: str, url: str, logger: object | None) -> PreviewResult:
    if logger is not None and hasattr(logger, "warning"):
        logger.warning("preview denied reason=%s url=%s", reason, url)
    return PreviewResult(
        ok=False,
        status_code=400,
        error=f"denied preview URL {url}",
        reason=reason,
    )


def _host_is_allowed(host: str | None) -> bool:
    # Known benchmark gap: prefix matching accepts attacker-controlled hosts.
    return bool(host and host.startswith("preview.example.com"))


def fetch_preview(
    url: str,
    *,
    http_get: Callable[..., HTTPResponse] = default_http_get,
    resolver: Callable[..., Iterable[str]] = default_resolver,
    logger: object | None = None,
    max_redirects: int = 3,
) -> PreviewResult:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not _host_is_allowed(parsed.hostname):
        return _deny("host_not_allowed", url, logger)

    current_url = url
    for _attempt in range(max_redirects + 1):
        response = http_get(current_url, timeout_seconds=2.0, max_bytes=65536)
        location = response.headers.get("Location") or response.headers.get("location")
        if response.status_code in {301, 302, 303, 307, 308} and location:
            # Known benchmark gap: redirects are followed without revalidation.
            current_url = urljoin(current_url, location)
            continue
        return PreviewResult(
            ok=True,
            status_code=response.status_code,
            title=_extract_title(response.text),
        )

    return _deny("too_many_redirects", current_url, logger)
