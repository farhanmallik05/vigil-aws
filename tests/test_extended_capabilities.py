"""Unit tests for DeciderVisionGuardrail and DeciderModelRouter."""

import pytest
from reusable_patterns.decider_guard.client import StrandsDeciderClient
from reusable_patterns.decider_guard.router import DeciderModelRouter
from reusable_patterns.decider_guard.vision_guard import DeciderVisionGuardrail


@pytest.fixture
def client():
    return StrandsDeciderClient(enable_fallback_emulator=True)


@pytest.mark.asyncio
async def test_vision_guardrail_evaluation(client):
    """Verify that DeciderVisionGuardrail processes visual architecture queries."""
    vision_guard = DeciderVisionGuardrail(client=client)

    result = await vision_guard.verify_action_against_diagram(
        image_bytes=b"MOCK_PNG_IMAGE_BYTES",
        proposed_action="drain_and_restart_container",
        target_resource="payments-api",
    )

    assert result.latency_ms > 0
    assert result.grounding_score >= 0.85
    assert result.is_safe_and_grounded is True


@pytest.mark.asyncio
async def test_model_router_simple_incident(client):
    """Verify that routine single-service alerts route to Bedrock Claude 3.5 Haiku."""
    router = DeciderModelRouter(client=client)

    result = await router.route_incident("Query API latency metrics for payments-api over the last 15 minutes.")
    assert result["is_complex"] is False
    assert "haiku" in result["selected_model"]
    assert result["estimated_cost_savings_pct"] == 80.0


@pytest.mark.asyncio
async def test_model_router_complex_incident(client):
    """Verify that cascading multi-tier outages route to Bedrock Claude 3.5 Sonnet."""
    router = DeciderModelRouter(client=client)

    result = await router.route_incident("Cascading deadlock between DynamoDB provisioned throughput and ECS gateway.")
    assert result["is_complex"] is True
    assert "sonnet" in result["selected_model"]
    assert result["estimated_cost_savings_pct"] == 0.0
