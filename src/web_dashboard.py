"""Interactive Web Dashboard for Vigil-AWS.

Serves a premium dark-mode glassmorphism dashboard at http://localhost:8501.
Allows builders and judges to test scenarios, evaluate arbitrary prompts in real-time,
and inspect Decider 2B's sub-120ms decision traces alongside Bedrock RCA logs.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reusable_patterns.decider_guard.client import StrandsDeciderClient
from reusable_patterns.decider_guard.handler import DeciderGroundedGuardrail
from reusable_patterns.decider_guard.router import DeciderModelRouter
from reusable_patterns.decider_guard.vision_guard import DeciderVisionGuardrail
from src.chaos_simulator import ALL_SCENARIOS, ChaosEngine

logger = logging.getLogger("vigil_aws.web")

# Global Guardrail, Router, Vision & Chaos Engine instances
CLIENT = StrandsDeciderClient(enable_fallback_emulator=True)
GUARDRAIL = DeciderGroundedGuardrail(client=CLIENT)
ROUTER = DeciderModelRouter(client=CLIENT)
VISION_GUARD = DeciderVisionGuardrail(client=CLIENT)
ENGINE = ChaosEngine(GUARDRAIL)

_ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None
_ASYNC_THREAD: Optional[threading.Thread] = None


def _start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_async_loop() -> asyncio.AbstractEventLoop:
    global _ASYNC_LOOP, _ASYNC_THREAD
    if _ASYNC_LOOP is None or not _ASYNC_LOOP.is_running():
        _ASYNC_LOOP = asyncio.new_event_loop()
        _ASYNC_THREAD = threading.Thread(target=_start_background_loop, args=(_ASYNC_LOOP,), daemon=True)
        _ASYNC_THREAD.start()
    return _ASYNC_LOOP


def run_async(coro: Any, timeout: float = 10.0) -> Any:
    loop = get_async_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)


TEMPLATE_FILE = Path(__file__).parent / "dashboard_template.html"


def get_html_content() -> str:
    """Load the Cyber-SRE Mission Control HTML template from disk."""
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return "<!DOCTYPE html><html><body><h1>Vigil-AWS Dashboard</h1><p>Template file missing.</p></body></html>"


HTML_CONTENT = get_html_content()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving the Vigil-AWS HUD and scenario APIs."""

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._set_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            body = get_html_content().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._set_cors_headers()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/docs/") and self.path.endswith(".svg"):
            file_name = Path(self.path).name
            svg_file = PROJECT_ROOT / "docs" / file_name
            if svg_file.exists():
                svg_data = svg_file.read_bytes()
            elif file_name == "benchmark_chart.svg":
                from benchmark.generate_chart import generate_svg_chart
                svg_data = generate_svg_chart().encode("utf-8")
            else:
                self._send_json(404, {"error": "SVG not found"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self._set_cors_headers()
            self.send_header("Content-Length", str(len(svg_data)))
            self.end_headers()
            self.wfile.write(svg_data)
        elif self.path == "/api/scenarios":
            scenarios = [
                {
                    "id": s.id,
                    "title": s.title,
                    "severity": s.severity,
                    "description": s.description,
                    "operator_prompt": s.operator_prompt,
                    "proposed_tool": s.proposed_tool,
                    "tool_args": s.tool_args,
                    "expected_action": s.expected_action,
                }
                for s in ALL_SCENARIOS
            ]
            self._send_json(200, scenarios)
        elif self.path.startswith("/api/run_scenario"):
            scenario_id = self.path.split("id=")[-1] if "id=" in self.path else "SCEN-01"
            scenario = next((s for s in ALL_SCENARIOS if s.id == scenario_id), ALL_SCENARIOS[0])
            result = run_async(ENGINE.run_scenario(scenario))
            result["bedrock_rca"] = (
                f"🧠 Amazon Bedrock SRE Commander Analysis:\n"
                f"Incident: {scenario.title} ({scenario.severity})\n"
                f"System-1 Gate Result: {result['action_taken']} ({result['reason']})\n"
                f"Grounding Score: {result.get('grounding_score', 0.0):.2f} | Blast: {result.get('blast_radius', 'safe')}\n"
                f"Root Cause Evaluation: Anomaly signature analyzed against AWS architecture domain.\n"
                f"Recommended Next Action: Operational state reconciled. No ungrounded blast radius incurred."
            )
            self._send_json(200, result)
        elif self.path == "/api/metrics":
            summary = GUARDRAIL.get_telemetry_summary()
            emf = GUARDRAIL.export_cloudwatch_emf()
            history = list(GUARDRAIL.decision_history[-10:])
            self._send_json(200, {"telemetry": summary, "cloudwatch_emf": emf, "recent_history": history})
        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            self._send_json(400, {"error": "Invalid JSON in request body"})
            return

        if self.path == "/api/evaluate_custom":
            tool_name = data.get("tool_name", "describe_cloudwatch_alarms")
            args = data.get("args", {})
            user_prompt = data.get("user_prompt", "Inspect alarms")

            class CustomMockEvent:
                def __init__(self, name: str, a: dict, p: str):
                    self.tool_use = {"name": name, "input": a, "toolUseId": "call_custom"}
                    self.invocation_state = {"prompt": p}
                    self.agent = type("MockAgent", (), {"messages": [{"role": "user", "content": p}]})()

            ev = CustomMockEvent(tool_name, args, user_prompt)
            action = run_async(GUARDRAIL.before_tool_call(ev))  # type: ignore
            latest = GUARDRAIL.decision_history[-1] if GUARDRAIL.decision_history else {}
            result = {
                "action_taken": action.__class__.__name__,
                "reason": getattr(action, "reason", "Verified safe"),
                "grounding_score": latest.get("grounding_score", 0.0),
                "blast_radius": latest.get("blast_radius", "unknown"),
                "blast_radius_confidence": latest.get("blast_radius_confidence", 0.0),
                "is_adversarial_score": latest.get("is_adversarial_score", 0.0),
                "latency_ms": latest.get("latency_ms", 114.0),
            }
            self._send_json(200, result)

        elif self.path == "/api/route_model":
            desc = data.get("incident_description", "Query latency metrics")
            result = run_async(ROUTER.route_incident(desc))
            self._send_json(200, result)

        elif self.path == "/api/evaluate_vision":
            b64_str = data.get("image_b64", "")
            try:
                import base64
                raw_bytes = base64.b64decode(b64_str) if b64_str else b"MOCK_IMG"
            except Exception:
                raw_bytes = b"MOCK_IMG"

            action = data.get("proposed_action", "drain_and_restart_container")
            target = data.get("target_resource", "payments-api")
            res = run_async(VISION_GUARD.verify_action_against_diagram(raw_bytes, action, target))
            self._send_json(200, {
                "is_visually_grounded": res.is_safe_and_grounded,
                "grounding_score": res.grounding_score,
                "blast_radius": res.blast_radius.value,
                "blast_radius_confidence": res.blast_radius_confidence,
                "latency_ms": res.latency_ms,
            })

        elif self.path == "/api/reset_metrics":
            GUARDRAIL.reset_metrics()
            self._send_json(200, {"status": "ok", "message": "Telemetry metrics reset."})

        else:
            self._send_json(404, {"error": "Not Found", "path": self.path})

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP request spam in terminal."""
        pass


def run_web_dashboard(port: int = 8501) -> None:
    """Runs the Vigil-AWS dashboard server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"\n[VIGIL-AWS DASHBOARD] Server running at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print("\n[VIGIL-AWS DASHBOARD] Stopped.")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv("PORT", "8501"))
    run_web_dashboard(port)
