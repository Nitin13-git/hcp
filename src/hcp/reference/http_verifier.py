from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request

from hcp.verification import VerificationReport, Verifier


class HttpVerifier(Verifier):
    """Verifies a target by making an HTTP GET request and checking the response.

    `target` is a URL. A check passes when the response status matches
    `expected_status` and, if `body_contains` is set, the response body
    contains that substring too — a status code alone is a weak check on
    its own (a 200 from the wrong page still "passes"). Evidence is the
    status plus truncated body, so a caller can see why a check failed
    without re-running it.

    Use this for checking a live service's response (did the patched
    endpoint actually stop leaking data, did the flag page actually render
    the flag); use `SubprocessVerifier` for running a local test suite or
    command instead.
    """

    def __init__(
        self,
        *,
        expected_status: int = 200,
        body_contains: str | None = None,
        timeout_s: float = 10.0,
        evidence_limit: int = 4000,
    ) -> None:
        self._expected_status = expected_status
        self._body_contains = body_contains
        self._timeout_s = timeout_s
        self._evidence_limit = evidence_limit

    def run(self, target: str) -> VerificationReport:
        start = time.monotonic()
        try:
            scheme = urllib.parse.urlsplit(target).scheme.lower()
        except ValueError as exc:
            return VerificationReport(
                passed=False,
                evidence=f"malformed URL: {exc}"[: self._evidence_limit],
                duration_s=time.monotonic() - start,
            )
        if scheme not in ("http", "https"):
            return VerificationReport(
                passed=False,
                evidence=f"unsupported URL scheme {scheme!r}: only http and https are allowed",
                duration_s=time.monotonic() - start,
            )
        try:
            request = urllib.request.Request(target, method="GET")
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                status = response.status
                body = response.read().decode(errors="replace")
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read().decode(errors="replace") if exc.fp else ""
        except (urllib.error.URLError, OSError) as exc:
            duration_s = time.monotonic() - start
            return VerificationReport(
                passed=False,
                evidence=f"request failed: {exc}"[: self._evidence_limit],
                duration_s=duration_s,
            )

        passed = status == self._expected_status
        if passed and self._body_contains is not None:
            passed = self._body_contains in body

        evidence = f"status={status}\n{body}"[: self._evidence_limit]
        duration_s = time.monotonic() - start
        return VerificationReport(passed=passed, evidence=evidence, duration_s=duration_s)
