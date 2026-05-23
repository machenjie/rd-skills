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


class CaptureLogger:
    def __init__(self) -> None:
        self.records: list[str] = []

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        if args:
            message = message % args
        self.records.append(f"warning {message} {kwargs}")


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


class SSRFSecurityTests(unittest.TestCase):
    def test_rejects_private_and_metadata_addresses_before_fetch(self) -> None:
        url = "https://preview.example.com/card"
        denied_addresses = [
            "127.0.0.1",
            "10.0.0.10",
            "172.16.0.10",
            "192.168.1.10",
            "169.254.169.254",
            "::1",
        ]

        for address in denied_addresses:
            with self.subTest(address=address):
                http = RecordingHTTP({url: Response(text="<title>internal</title>")})
                result = app.fetch_preview(
                    url,
                    http_get=http,
                    resolver=resolver_for({"preview.example.com": [address]}),
                )

                self.assertFalse(result_ok(result))
                self.assertEqual(http.calls, [])

    def test_revalidates_redirect_targets_before_second_fetch(self) -> None:
        initial = "https://preview.example.com/redirect"
        metadata_url = "http://169.254.169.254/latest/meta-data?token=secret-token"
        http = RecordingHTTP(
            {
                initial: Response(status_code=302, headers={"Location": metadata_url}),
                metadata_url: Response(text="<title>metadata</title>"),
            }
        )

        result = app.fetch_preview(
            initial,
            http_get=http,
            resolver=resolver_for({"preview.example.com": ["93.184.216.34"]}),
        )

        self.assertFalse(result_ok(result))
        self.assertEqual(http.calls, [initial])
        denial_text = result_text(result)
        self.assertNotIn("169.254.169.254", denial_text)
        self.assertNotIn("secret-token", denial_text)

    def test_denial_logs_reason_without_sensitive_url_values(self) -> None:
        url = "https://preview.example.com/card?token=secret-token"
        logger = CaptureLogger()
        result = app.fetch_preview(
            url,
            http_get=RecordingHTTP({url: Response(text="<title>internal</title>")}),
            resolver=resolver_for({"preview.example.com": ["10.0.0.10"]}),
            logger=logger,
        )

        self.assertFalse(result_ok(result))
        logs = " ".join(logger.records)
        self.assertTrue(logger.records)
        self.assertRegex(logs.casefold(), r"blocked|denied|private|metadata")
        self.assertNotIn("token=", logs)
        self.assertNotIn("secret-token", logs)


if __name__ == "__main__":
    unittest.main()
