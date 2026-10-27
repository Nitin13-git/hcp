from pathlib import Path

from hcp.reference import FileLifecycle, JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer
from hcp.scope import Capability, CapabilityKind


def test_state_store_roundtrip(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state.json")
    store.write("progress", {"done": 1}, by="test")
    store.write("progress", {"done": 2}, by="test")

    latest = store.read("progress")
    assert latest is not None
    assert latest.value == {"done": 2}
    assert len(store.history("progress")) == 2


def test_checkpoint_is_idempotent(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state.json")
    first = store.checkpoint("phase-1")
    second = store.checkpoint("phase-1")
    assert first == second


def test_scope_denies_by_default() -> None:
    scope = TableScopeEnforcer()
    cap = Capability(kind=CapabilityKind.PATH, pattern="/etc/passwd")
    assert scope.check(cap) is False


def test_scope_allows_granted_pattern() -> None:
    scope = TableScopeEnforcer()
    scope.grant(Capability(kind=CapabilityKind.PATH, pattern="/repo/*"))
    assert scope.check(Capability(kind=CapabilityKind.PATH, pattern="/repo/src/main.py"))
    assert not scope.check(Capability(kind=CapabilityKind.PATH, pattern="/etc/passwd"))


def test_verifier_reports_pass_and_fail() -> None:
    verifier = SubprocessVerifier()
    ok = verifier.run("true")
    bad = verifier.run("false")
    assert ok.passed is True
    assert bad.passed is False


def test_lifecycle_records_status_transitions(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state.json")
    lifecycle = FileLifecycle(store)

    handle = lifecycle.init("demo task")
    lifecycle.checkpoint(handle)
    lifecycle.teardown(handle, reason="done")

    history = store.history(f"session:{handle.session_id}:status")
    assert [r.value for r in history][0] == "init"
    assert history[-1].value == "teardown:done"
