"""End-to-end integration and API tests for Vigil-AWS Web Dashboard."""

import json
import threading
import time
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pytest

from src.web_dashboard import DashboardRequestHandler


@pytest.fixture(scope="module")
def dashboard_server():
    """Spawns an ephemeral test instance of DashboardRequestHandler."""
    server = HTTPServer(("127.0.0.1", 0), DashboardRequestHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    time.sleep(0.1)
    yield base_url
    server.shutdown()
    server.server_close()


def http_get(url: str):
    """Helper to perform HTTP GET."""
    req = Request(url)
    with urlopen(req, timeout=5) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def http_post(url: str, payload: dict):
    """Helper to perform HTTP POST."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def test_index_page(dashboard_server):
    """Verify that root URL serves the interactive HTML dashboard."""
    status, content_type, body = http_get(f"{dashboard_server}/")
    assert status == 200
    assert "text/html" in content_type
    html = body.decode("utf-8")
    assert "Vigil-AWS" in html
    assert "Strands Decider 2B" in html


def test_svg_chart_route(dashboard_server):
    """Verify that /docs/benchmark_chart.svg returns SVG image data."""
    status, content_type, body = http_get(f"{dashboard_server}/docs/benchmark_chart.svg")
    assert status == 200
    assert "image/svg+xml" in content_type or "xml" in content_type
    svg = body.decode("utf-8")
    assert "<svg" in svg
    assert "17.96x" in svg or "BENCHMARK" in svg


def test_svg_architecture_diagram_route(dashboard_server):
    """Verify that /docs/architecture_diagram.svg returns the architecture diagram."""
    status, content_type, body = http_get(f"{dashboard_server}/docs/architecture_diagram.svg")
    assert status == 200
    assert "image/svg+xml" in content_type or "xml" in content_type
    svg = body.decode("utf-8")
    assert "<svg" in svg
    assert "VIGIL-AWS: DUAL-SPEED AGENT ARCHITECTURE" in svg


def test_svg_state_machine_route(dashboard_server):
    """Verify that /docs/decision_state_machine.svg returns the state machine diagram."""
    status, content_type, body = http_get(f"{dashboard_server}/docs/decision_state_machine.svg")
    assert status == 200
    assert "image/svg+xml" in content_type or "xml" in content_type
    svg = body.decode("utf-8")
    assert "<svg" in svg
    assert "DECIDERGUARD STATE MACHINE" in svg


def test_api_scenarios_list(dashboard_server):
    """Verify that /api/scenarios lists all operational scenarios."""
    status, content_type, body = http_get(f"{dashboard_server}/api/scenarios")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 4
    scenario_ids = [s["id"] for s in data]
    assert "SCEN-01" in scenario_ids
    assert "SCEN-02" in scenario_ids
    assert "SCEN-03" in scenario_ids
    assert "SCEN-04" in scenario_ids


def test_api_run_scenario_proceed(dashboard_server):
    """Verify running SCEN-01 returns a Proceed decision in sub-200ms."""
    status, content_type, body = http_get(f"{dashboard_server}/api/run_scenario?id=SCEN-01")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["scenario_id"] == "SCEN-01"
    assert data["action_taken"] == "Proceed"
    assert data["latency_ms"] > 0
    assert data["grounding_score"] >= 0.85


def test_api_run_scenario_deny(dashboard_server):
    """Verify running SCEN-02 returns Deny on prompt injection."""
    status, content_type, body = http_get(f"{dashboard_server}/api/run_scenario?id=SCEN-02")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["scenario_id"] == "SCEN-02"
    assert data["action_taken"] == "Deny"


def test_api_run_scenario_confirm(dashboard_server):
    """Verify running SCEN-03 returns Confirm for destructive EC2 termination."""
    status, content_type, body = http_get(f"{dashboard_server}/api/run_scenario?id=SCEN-03")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["scenario_id"] == "SCEN-03"
    assert data["action_taken"] == "Confirm"


def test_api_run_scenario_guide(dashboard_server):
    """Verify running SCEN-04 returns Guide on parameter drift."""
    status, content_type, body = http_get(f"{dashboard_server}/api/run_scenario?id=SCEN-04")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["scenario_id"] == "SCEN-04"
    assert data["action_taken"] == "Guide"


def test_api_metrics(dashboard_server):
    """Verify /api/metrics returns consolidated telemetry and CloudWatch EMF."""
    status, content_type, body = http_get(f"{dashboard_server}/api/metrics")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "telemetry" in data
    assert "cloudwatch_emf" in data
    assert data["telemetry"]["total_decisions"] >= 0


def test_api_evaluate_custom(dashboard_server):
    """Verify POST /api/evaluate_custom allows arbitrary tool evaluation."""
    payload = {
        "tool_name": "restart_service",
        "args": {"service": "payments-api"},
        "user_prompt": "Please restart payments-api safely",
    }
    status, content_type, body = http_post(f"{dashboard_server}/api/evaluate_custom", payload)
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "action_taken" in data
    assert "grounding_score" in data
    assert data["latency_ms"] > 0


def test_api_route_model(dashboard_server):
    """Verify POST /api/route_model dynamically evaluates model routing."""
    payload = {"incident_description": "Query latency metrics for payments-api"}
    status, content_type, body = http_post(f"{dashboard_server}/api/route_model", payload)
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "selected_model" in data
    assert "haiku" in data["selected_model"]
    assert data["estimated_cost_savings_pct"] == 80.0


def test_api_evaluate_vision(dashboard_server):
    """Verify POST /api/evaluate_vision processes multimodal grounding."""
    payload = {
        "image_b64": "TU9DS19JTUFHRQ==",
        "proposed_action": "drain_and_restart_container",
        "target_resource": "payments-api",
    }
    status, content_type, body = http_post(f"{dashboard_server}/api/evaluate_vision", payload)
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "is_visually_grounded" in data
    assert data["latency_ms"] > 0


def test_api_invalid_json(dashboard_server):
    """Verify POST with invalid JSON returns 400 Bad Request."""
    req = Request(
        f"{dashboard_server}/api/evaluate_custom",
        data=b"INVALID_JSON_PAYLOAD",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(HTTPError) as exc_info:
        urlopen(req, timeout=5)
    assert exc_info.value.code == 400


def test_404_not_found(dashboard_server):
    """Verify non-existent endpoints return 404."""
    req = Request(f"{dashboard_server}/non_existent_endpoint")
    with pytest.raises(HTTPError) as exc_info:
        urlopen(req, timeout=5)
    assert exc_info.value.code == 404
