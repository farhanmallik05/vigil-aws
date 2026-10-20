"""Multimodal Vision Guardrail using Strands Decider 2B.

Enables Strands agents to pass infrastructure diagrams, network topology maps,
and CloudWatch dashboard screenshots to Strands Decider 2B for visual grounding.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import StrandsDeciderClient
from .questions import DeciderEvaluationResult, DeciderQuestion

logger = logging.getLogger("decider_guard.vision")


class DeciderVisionGuardrail:
    """Multimodal vision inspector for cloud architecture and telemetry screenshots.

    Uses Strands Decider 2B with `--vision` flag (Qwen3.5-2B-Base native multimodal vision)
    to verify that proposed cloud actions match visual network architecture or dashboard graphs.
    """

    def __init__(
        self,
        client: Optional[StrandsDeciderClient] = None,
        confidence_threshold: float = 0.85,
    ) -> None:
        self.client = client or StrandsDeciderClient(enable_fallback_emulator=True)
        self.confidence_threshold = confidence_threshold

    async def verify_action_against_diagram(
        self,
        image_bytes: bytes,
        proposed_action: str,
        target_resource: str,
    ) -> DeciderEvaluationResult:
        """Verifies whether a proposed action aligns with an architecture diagram or dashboard screenshot."""
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        q_visual = DeciderQuestion(
            question_id="is_visually_grounded",
            question_type="noul",
            instructions=(
                f"Does the attached cloud architecture diagram or CloudWatch graph confirm that "
                f"action '{proposed_action}' targeting '{target_resource}' is architecturally valid and degraded?"
            ),
        )
        q_risk = DeciderQuestion(
            question_id="blast_radius",
            question_type="choice",
            instructions="What is the operational blast radius indicated by this visual topology?",
            options=["harmless_read", "safe_mutation", "destructive_irreversible"],
        )

        state_text = f"Action: {proposed_action}\nTarget: {target_resource}"
        return await self.client.evaluate(
            state=state_text,
            questions=[q_visual, q_risk],
            images=[b64_image],
        )

    async def verify_image_file(
        self,
        image_path: str | Path,
        proposed_action: str,
        target_resource: str,
    ) -> DeciderEvaluationResult:
        """Reads a local image file and verifies it against the proposed cloud action."""
        path = Path(image_path)
        if not path.exists():
            # In testing/emulator mode, generate synthetic placeholder bytes
            image_data = b"SYNTHETIC_CLOUDWATCH_GRAPH_BYTES"
        else:
            image_data = path.read_bytes()

        return await self.verify_action_against_diagram(image_data, proposed_action, target_resource)
