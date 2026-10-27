from pathlib import Path

from hcp.reference import FileLifecycle, JsonFileStateStore, SubprocessVerifier, TableScopeEnforcer
from hcp.validator import validate


def test_full_reference_harness_is_conformant(tmp_path: Path) -> None:
    state = JsonFileStateStore(tmp_path / "state.json")
    report = validate(
        {
            "state": state,
            "verification": SubprocessVerifier(),
            "scope": TableScopeEnforcer(),
            "lifecycle": FileLifecycle(state),
        }
    )
    assert report.conformant
    assert report.missing == frozenset()


def test_partial_harness_reports_missing_interfaces(tmp_path: Path) -> None:
    report = validate({"state": JsonFileStateStore(tmp_path / "state.json")})
    assert not report.conformant
    assert report.missing == frozenset({"verification", "scope", "lifecycle"})


def test_wrong_type_is_reported_as_error() -> None:
    report = validate({"state": object(), "verification": object(), "scope": object(), "lifecycle": object()})
    assert not report.conformant
    assert len(report.errors) == 4
