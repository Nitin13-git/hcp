from __future__ import annotations

import shlex
import subprocess
import time

from hcp.verification import VerificationReport, Verifier


class SubprocessVerifier(Verifier):
    """Verifies a target by running it as a shell command and checking exit status.

    `target` is a shell command string, e.g. "pytest tests/test_foo.py".
    Evidence is stdout+stderr, truncated, so a caller can see why a check
    failed without re-running it.
    """

    def __init__(self, *, timeout_s: float = 60.0, evidence_limit: int = 4000) -> None:
        self._timeout_s = timeout_s
        self._evidence_limit = evidence_limit

    def run(self, target: str) -> VerificationReport:
        start = time.monotonic()
        try:
            result = subprocess.run(
                shlex.split(target),
                capture_output=True,
                text=True,
                timeout=self._timeout_s,
            )
            passed = result.returncode == 0
            evidence = (result.stdout + result.stderr)[: self._evidence_limit]
        except subprocess.TimeoutExpired as exc:
            passed = False
            evidence = f"timed out after {self._timeout_s}s: {exc}"
        except OSError as exc:
            passed = False
            evidence = f"could not run command: {exc}"[: self._evidence_limit]
        duration_s = time.monotonic() - start
        return VerificationReport(passed=passed, evidence=evidence, duration_s=duration_s)
