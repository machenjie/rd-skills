from __future__ import annotations

import ipaddress
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
        self.inside = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.inside = tag.casefold() == "title" or self.inside

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self.inside = False

    def handle_data(self, data: str) -> None:
        if self.inside:
            self.parts.append(data)


def _title(html: str) -> str | None:
    parser = _TitleParser()
    parser.feed(html)
    value = " ".join(part.strip() for part in parser.parts if part.strip())
    return value or None


def default_http_get(url: str, *, timeout_seconds: float = 2.0, max_bytes: int = 65536) -> HTTPResponse:
    raise RuntimeError("network is disabled in the benchmark")


def default_resolver(host: str) -> Iterable[str]:
    return []


def _deny(reason: str, logger: object | None) -> PreviewResult:
    if logger is not None and hasattr(logger, "warning"):
        logger.warning("preview denied reason=%s", reason)
    return PreviewResult(False, 400, error="preview URL denied", reason=reason)


def _url_allowed(url: str, resolver: Callable[..., Iterable[str]]) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError:
        return False, "invalid_url"
    host = (parsed.hostname or "").rstrip(".").casefold()
    if (
        parsed.scheme.casefold() != "https"
        or host != "preview.example.com"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        return False, "host_not_allowed"
    try:
        addresses = list(resolver(host))
        safe = bool(addresses) and all(ipaddress.ip_address(value).is_global for value in addresses)
    except (OSError, ValueError, TypeError):
        return False, "dns_denied"
    return (True, "allowed") if safe else (False, "private_address")


def fetch_preview(
    url: str,
    *,
    http_get: Callable[..., HTTPResponse] = default_http_get,
    resolver: Callable[..., Iterable[str]] = default_resolver,
    logger: object | None = None,
    max_redirects: int = 3,
) -> PreviewResult:
    current = url
    for attempt in range(max_redirects + 1):
        allowed, reason = _url_allowed(current, resolver)
        if not allowed:
            return _deny(reason, logger)
        try:
            response = http_get(current, timeout_seconds=2.0, max_bytes=65536)
        except (OSError, TimeoutError, RuntimeError):
            return _deny("fetch_failed", logger)
        location = response.headers.get("Location") or response.headers.get("location")
        if response.status_code in {301, 302, 303, 307, 308} and location:
            if attempt == max_redirects:
                return _deny("too_many_redirects", logger)
            current = urljoin(current, location)
            continue
        return PreviewResult(True, response.status_code, title=_title(response.text))
    return _deny("too_many_redirects", logger)
