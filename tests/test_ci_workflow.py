from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "test.yml"


def _text() -> str:
    assert WORKFLOW.exists(), "test.yml workflow is missing"
    return WORKFLOW.read_text()


def test_workflow_runs_on_pull_requests_and_main_pushes() -> None:
    text = _text()
    assert "pull_request" in text
    assert "push:" in text and "main" in text


def test_workflow_runs_python_suite() -> None:
    text = _text()
    assert 'pip install -e ".[dev]"' in text
    assert "pytest" in text


def test_workflow_runs_typescript_suite_on_node_matrix() -> None:
    text = _text()
    assert "npm ci" in text and "npm test" in text
    assert "18" in text and "22" in text


def test_workflow_runs_interop_proof() -> None:
    assert "interop/run_interop.sh" in _text()
