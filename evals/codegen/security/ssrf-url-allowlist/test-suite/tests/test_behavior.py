from __future__ import annotations

import unittest

import app


class Response:
    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}


class RecordingHTTP:
    def __init__(self, routes: dict[str, Response]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, url: str, **kwargs: object) -> Response:
        self.calls.append(url)
        if url not in self.routes:
            raise AssertionError(f"unexpected fetch: {url}")
        return self.routes[url]


def resolver_for(mapping: dict[str, list[str]]):
    def resolve(host: str, *args: object, **kwargs: object) -> list[str]:
        return mapping.get(host, [])

    return resolve


def result_ok(result: object) -> bool:
    if isinstance(result, dict):
        return result.get("ok") is True
    return getattr(result, "ok", False) is True


def result_text(result: object) -> str:
    if isinstance(result, dict):
        values = result.values()
    else:
        values = (
            getattr(result, "error", None),
            getattr(result, "reason", None),
            getattr(result, "title", None),
        )
    return " ".join(str(value) for value in values if value is not None)


class SSRFBehaviorTests(unittest.TestCase):
    def test_allowed_https_host_fetches_preview(self) -> None:
        url = "https://preview.example.com/card"
        http = RecordingHTTP(
            {
                url: Response(
                    text="<html><head><title>Example card</title></head></html>"
                )
            }
        )

        result = app.fetch_preview(
            url,
            http_get=http,
            resolver=resolver_for({"preview.example.com": ["93.184.216.34"]}),
        )

        self.assertTrue(result_ok(result))
        self.assertEqual(http.calls, [url])
        self.assertIn("Example card", result_text(result))

    def test_rejects_prefix_allowlist_bypass_before_fetch(self) -> None:
        url = "https://preview.example.com.evil.test/card?token=secret-token"
        http = RecordingHTTP(
            {
                url: Response(text="<html><title>attacker</title></html>"),
            }
        )

        result = app.fetch_preview(
            url,
            http_get=http,
            resolver=resolver_for(
                {"preview.example.com.evil.test": ["93.184.216.34"]}
            ),
        )

        self.assertFalse(result_ok(result))
        self.assertEqual(http.calls, [])
        self.assertNotIn("secret-token", result_text(result))


if __name__ == "__main__":
    unittest.main()
