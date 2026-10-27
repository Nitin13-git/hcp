from pathlib import Path

from hcp.reference import FileLifecycle, JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer, resume
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


def test_scope_round_trips_through_capability_dicts() -> None:
    scope = TableScopeEnforcer()
    scope.grant(Capability(kind=CapabilityKind.PATH, pattern="/workspace/*"))
    scope.grant(Capability(kind=CapabilityKind.COMMAND, pattern="pytest"))

    # Plain string dicts, as they'd look after a JSON round trip through a
    # StateStore (or after crossing a language boundary) — not Capability
    # instances, deliberately, to exercise the actual decode path.
    exported = [{"kind": c.kind.value, "pattern": c.pattern} for c in scope.active_scope()]

    rebuilt = TableScopeEnforcer.from_capability_dicts(exported)
    assert rebuilt.check(Capability(kind=CapabilityKind.PATH, pattern="/workspace/report.md"))
    assert rebuilt.check(Capability(kind=CapabilityKind.COMMAND, pattern="pytest"))
    assert not rebuilt.check(Capability(kind=CapabilityKind.PATH, pattern="/etc/passwd"))
    assert not rebuilt.check(Capability(kind=CapabilityKind.COMMAND, pattern="rm"))


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


def test_resume_reconstructs_handle_from_state_alone(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state.json")
    lifecycle = FileLifecycle(store)
    original = lifecycle.init("investigate the login endpoint")

    # A different process, knowing only the session id, reconstructs the
    # same handle purely from what's in the store — no out-of-band task.
    resumed = resume(store, original.session_id)

    assert resumed.session_id == original.session_id
    assert resumed.task == original.task == "investigate the login endpoint"


def test_resume_raises_for_unknown_session(tmp_path: Path) -> None:
    store = JsonFileStateStore(tmp_path / "state.json")
    try:
        resume(store, "does-not-exist")
        assert False, "expected KeyError"
    except KeyError:
        pass
