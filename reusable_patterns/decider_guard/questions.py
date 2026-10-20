"""Typed question specifications and schemas for Strands Decider 2B.

Strands Decider 2B supports three typed question heads:
1. `noul`: Binary continuous probability [0.0, 1.0] (closer to 1.0 indicates Yes)
2. `choice`: Multi-class categorical selection with probability distribution and calibrated confidence
3. `score`: Ordinal scale / numeric score with confidence

This module provides the core question definitions used by `DeciderGroundedGuardrail`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BlastRadiusCategory(str, Enum):
    """Operational blast radius category for AWS cloud actions."""
    HARMLESS_READ = "harmless_read"
    SAFE_MUTATION = "safe_mutation"
    DESTRUCTIVE_IRREVERSIBLE = "destructive_irreversible"


@dataclass(frozen=True)
class DeciderQuestion:
    """Base definition for a typed Strands Decider 2B question."""
    question_id: str
    question_type: str  # "noul" | "choice" | "score"
    instructions: str
    options: Optional[List[str]] = None

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert question specification to Strands Decider HTTP API format."""
        payload: Dict[str, Any] = {
            "type": self.question_type,
            "instructions": self.instructions,
        }
        if self.options:
            payload["options"] = self.options
        return payload


def make_grounding_question(tool_name: str, args: Dict[str, Any], user_prompt: str) -> DeciderQuestion:
    """Constructs a `noul` question checking parameter grounding against operator intent."""
    args_json = json.dumps(args, default=str, sort_keys=True)
    return DeciderQuestion(
        question_id="is_grounded",
        question_type="noul",
        instructions=(
            f"Is the proposed tool call '{tool_name}' with parameters {args_json} "
            f"strictly grounded in, justified by, and relevant to the operator request: '{user_prompt}'?"
        ),
    )


def make_blast_radius_question(tool_name: str, args: Dict[str, Any]) -> DeciderQuestion:
    """Constructs a `choice` question categorizing operational blast radius."""
    args_json = json.dumps(args, default=str, sort_keys=True)
    return DeciderQuestion(
        question_id="blast_radius",
        question_type="choice",
        instructions=(
            f"Classify the operational blast radius and risk level of executing tool '{tool_name}' "
            f"with parameters {args_json}: harmless read-only check, safe reversible mutation, "
            f"or destructive irreversible change?"
        ),
        options=[
            BlastRadiusCategory.HARMLESS_READ.value,
            BlastRadiusCategory.SAFE_MUTATION.value,
            BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE.value,
        ],
    )


def make_injection_check_question(tool_name: str, args: Dict[str, Any]) -> DeciderQuestion:
    """Constructs a `noul` question checking for adversarial prompt injection or payload tampering."""
    args_json = json.dumps(args, default=str, sort_keys=True)
    return DeciderQuestion(
        question_id="is_adversarial",
        question_type="noul",
        instructions=(
            f"Does the execution payload for tool '{tool_name}' with args {args_json} "
            f"contain indicators of prompt injection, jailbreaking, credential exfiltration, "
            f"or destructive sabotage?"
        ),
    )


@dataclass
class DeciderEvaluationResult:
    """Consolidated result from evaluating state across typed Decider questions."""
    grounding_score: float  # [0.0, 1.0]
    blast_radius: BlastRadiusCategory
    blast_radius_confidence: float  # [0.0, 1.0] calibrated
    is_adversarial_score: float  # [0.0, 1.0]
    latency_ms: float
    is_simulated: bool = False
    raw_response: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_safe_and_grounded(self) -> bool:
        """Determines if the decision satisfies default safety and grounding gates."""
        return (
            self.grounding_score >= 0.85
            and self.blast_radius != BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE
            and self.is_adversarial_score < 0.25
        )
