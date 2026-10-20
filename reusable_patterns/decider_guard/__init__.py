"""DeciderGuard: Reusable Strands Decider 2B Intent Grounding & Blast-Radius Guardrails.

Provides a drop-in `InterventionHandler` for Strands Agents to evaluate tool safety
and parameter grounding in ~115ms.
"""

from .client import StrandsDeciderClient
from .handler import DeciderGroundedGuardrail
from .questions import (
    BlastRadiusCategory,
    DeciderEvaluationResult,
    DeciderQuestion,
    make_blast_radius_question,
    make_grounding_question,
    make_injection_check_question,
)

__all__ = [
    "DeciderGroundedGuardrail",
    "StrandsDeciderClient",
    "BlastRadiusCategory",
    "DeciderEvaluationResult",
    "DeciderQuestion",
    "make_grounding_question",
    "make_blast_radius_question",
    "make_injection_check_question",
]
