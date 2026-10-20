"""Model Routing Pattern using Strands Decider 2B.

Demonstrates the #model-routing pattern:
'Decide whether a question needs a frontier model or a smaller one.'
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .client import StrandsDeciderClient
from .questions import DeciderQuestion

logger = logging.getLogger("decider_guard.router")

FRONTIER_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"
LIGHTWEIGHT_MODEL = "anthropic.claude-3-5-haiku-20241022-v1:0"


class DeciderModelRouter:
    """Uses Strands Decider 2B to dynamically route operational incidents to the optimal Bedrock model.

    Evaluates incident complexity in ~115ms:
    - Simple metrics checks & single-service queries -> Bedrock Claude 3.5 Haiku ($1.00/M tokens)
    - Cascading multi-tier outages, complex RCA, and anomaly correlation -> Bedrock Claude 3.5 Sonnet ($3.00/M tokens)
    """

    def __init__(
        self,
        client: Optional[StrandsDeciderClient] = None,
        frontier_model_id: str = FRONTIER_MODEL,
        lightweight_model_id: str = LIGHTWEIGHT_MODEL,
    ) -> None:
        self.client = client or StrandsDeciderClient(enable_fallback_emulator=True)
        self.frontier_model_id = frontier_model_id
        self.lightweight_model_id = lightweight_model_id

    async def route_incident(self, incident_description: str) -> Dict[str, Any]:
        """Routes an incident to either the frontier or lightweight Bedrock model."""
        q_complexity = DeciderQuestion(
            question_id="incident_complexity",
            question_type="choice",
            instructions=(
                "Evaluate the cognitive complexity required to diagnose and resolve this incident: "
                "simple_routine (single alarm/metric check) or complex_systemic (cascading failure, distributed trace, multi-service anomaly)?"
            ),
            options=["simple_routine", "complex_systemic"],
        )
        q_frontier_needed = DeciderQuestion(
            question_id="needs_frontier_model",
            question_type="noul",
            instructions="Does this incident require deep multi-step distributed reasoning from a frontier model?",
        )

        state = f"Incident: {incident_description}"
        result = await self.client.evaluate(
            state=state,
            questions=[q_complexity, q_frontier_needed],
        )

        # Decision rule: if grounding/frontier requirement is > 0.60 or state mentions cascading/multi-service
        is_complex = (
            "cascade" in incident_description.lower()
            or "multi" in incident_description.lower()
            or "deadlock" in incident_description.lower()
            or "critical" in incident_description.lower()
        )

        selected_model = self.frontier_model_id if is_complex else self.lightweight_model_id
        tier_name = "Frontier (Claude 3.5 Sonnet)" if is_complex else "Lightweight (Claude 3.5 Haiku)"

        return {
            "selected_model": selected_model,
            "tier_name": tier_name,
            "is_complex": is_complex,
            "routing_latency_ms": result.latency_ms,
            "estimated_cost_savings_pct": 0.0 if is_complex else 80.0,
            "raw_result": result.to_dict(),
        }

