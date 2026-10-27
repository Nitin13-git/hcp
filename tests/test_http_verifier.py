from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from hcp.reference import HttpVerifier


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        if self.path == "/ok":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"flag{captured}")
        elif self.path == "/wrong-body":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"nothing to see here")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # silence default request logging to stderr


@pytest.fixture
def server_url() -> Iterator[str]:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join()


def test_passes_on_matching_status_and_body(server_url: str) -> None:
    verifier = HttpVerifier(expected_status=200, body_contains="flag{captured}")
    report = verifier.run(f"{server_url}/ok")
    assert report.passed is True
    assert "flag{captured}" in report.evidence


def test_fails_on_wrong_status(server_url: str) -> None:
    verifier = HttpVerifier(expected_status=200)
    report = verifier.run(f"{server_url}/missing")
    assert report.passed is False
    assert "status=404" in report.evidence


def test_fails_when_body_does_not_contain_expected_text(server_url: str) -> None:
    verifier = HttpVerifier(expected_status=200, body_contains="flag{captured}")
    report = verifier.run(f"{server_url}/wrong-body")
    assert report.passed is False


def test_status_only_check_ignores_body(server_url: str) -> None:
    verifier = HttpVerifier(expected_status=200)
    report = verifier.run(f"{server_url}/wrong-body")
    assert report.passed is True


def test_fails_when_nothing_is_listening() -> None:
    verifier = HttpVerifier(expected_status=200, timeout_s=1.0)
    report = verifier.run("http://127.0.0.1:1/unreachable")
    assert report.passed is False
    assert "request failed" in report.evidence
