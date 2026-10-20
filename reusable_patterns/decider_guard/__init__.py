"""DeciderGuard: Reusable Strands Decider 2B Intent Grounding & Blast-Radius Guardrails.

Provides drop-in `InterventionHandler`, Multimodal Vision Guardrail, and Model Router
for Strands Agents to evaluate tool safety and routing in ~115ms.
"""

from .client import (
    DeciderClientError,
    DeciderConnectionError,
    DeciderTimeoutError,
    StrandsDeciderClient,
)
from .handler import DeciderGroundedGuardrail
from .questions import (
    BlastRadiusCategory,
    DeciderEvaluationResult,
    DeciderQuestion,
    make_blast_radius_question,
    make_grounding_question,
    make_injection_check_question,
)
from .router import DeciderModelRouter
from .vision_guard import DeciderVisionGuardrail

__all__ = [
    "DeciderGroundedGuardrail",
    "DeciderVisionGuardrail",
    "DeciderModelRouter",
    "StrandsDeciderClient",
    "DeciderClientError",
    "DeciderConnectionError",
    "DeciderTimeoutError",
    "BlastRadiusCategory",
    "DeciderEvaluationResult",
    "DeciderQuestion",
    "make_grounding_question",
    "make_blast_radius_question",
    "make_injection_check_question",
]
