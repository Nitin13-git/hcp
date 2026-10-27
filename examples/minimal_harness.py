"""Wire up the reference implementation and run one session end to end.

Run with: python examples/minimal_harness.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from hcp.reference import FileLifecycle, JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer
from hcp.scope import Capability, CapabilityKind
from hcp.validator import validate


def main() -> None:
    with TemporaryDirectory() as tmp:
        state = JsonFileStateStore(Path(tmp) / "state.json")
        scope = TableScopeEnforcer()
        verifier = SubprocessVerifier()
        lifecycle = FileLifecycle(state)

        report = validate(
            {"state": state, "verification": verifier, "scope": scope, "lifecycle": lifecycle}
        )
        print(f"conformant: {report.conformant}")

        scope.grant(Capability(kind=CapabilityKind.PATH, pattern=f"{tmp}/*"))
        handle = lifecycle.init("run the test suite")

        result = verifier.run("true")
        state.write("last_verification", result.passed, by="example")
        lifecycle.checkpoint(handle)

        print(f"verification passed: {result.passed}")
        print(f"state history: {[r.value for r in state.history('last_verification')]}")

        lifecycle.teardown(handle, reason="example complete")


if __name__ == "__main__":
    main()
