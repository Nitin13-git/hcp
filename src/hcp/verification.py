from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    evidence: str
    duration_s: float


class Verifier(ABC):
    """Independently checks whether a target's claimed state is true.

    A Verifier never takes the agent's word for it: `run` must perform its
    own check (running tests, diffing a snapshot, hitting an endpoint) and
    return evidence a caller can inspect without re-deriving the result.
    """

    @abstractmethod
    def run(self, target: str) -> VerificationReport: ...
