"""Strands InterventionHandler implementing sub-second System-1 guardrails via Strands Decider 2B.

This is the primary reusable asset of the Vigil-AWS project. Any agent built with the
Strands Agents SDK can attach `DeciderGroundedGuardrail` to enforce typed intent grounding
and blast-radius gating before any tool execution.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from strands.hooks.events import BeforeToolCallEvent
from strands.interventions.actions import Confirm, Deny, Guide, Proceed, Transform
from strands.interventions.handler import InterventionHandler

from .client import StrandsDeciderClient
from .questions import (
    BlastRadiusCategory,
    DeciderEvaluationResult,
    make_blast_radius_question,
    make_grounding_question,
    make_injection_check_question,
)

logger = logging.getLogger("decider_guard.handler")


class DeciderGroundedGuardrail(InterventionHandler):
    """Inline System-1 decision guardrail powered by Strands Decider 2B.

    Intercepts tool calls during the `before_tool_call` lifecycle phase.
    Queries Strands Decider 2B to verify:
    1. Is the proposed action grounded in what the operator asked? (`noul`)
    2. What is the operational blast radius? (`choice`)
    3. Does the payload contain adversarial tampering? (`noul`)

    Returns `Proceed()`, `Confirm()`, or `Deny()` based on mathematically calibrated thresholds.
    """

    def __init__(
        self,
        decider_url: str = "http://localhost:8000",
        confidence_threshold: float = 0.85,
        block_destructive: bool = True,
        require_human_on_high_risk: bool = True,
        enable_fallback_emulator: bool = True,
        client: Optional[StrandsDeciderClient] = None,
    ) -> None:
        self._name = "decider-grounded-guardrail"
        self.confidence_threshold = confidence_threshold
        self.block_destructive = block_destructive
        self.require_human_on_high_risk = require_human_on_high_risk
        self.client = client or StrandsDeciderClient(
            base_url=decider_url,
            enable_fallback_emulator=enable_fallback_emulator,
        )

        # Telemetry and metrics for benchmarking & HUD
        self.total_decisions: int = 0
        self.total_proceeds: int = 0
        self.total_confirms: int = 0
        self.total_denials: int = 0
        self.decision_history: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        """Unique identifier for this intervention handler."""
        return self._name

    async def before_tool_call(
        self, event: BeforeToolCallEvent, **kwargs: Any
    ) -> Proceed | Deny | Confirm | Guide | Transform:
        """Evaluates tool invocation against Strands Decider 2B before tool runs."""
        tool_use = event.tool_use
        tool_name = tool_use.get("name", "unknown_tool")
        args = tool_use.get("input", {})

        # Extract operator prompt from invocation context or message history
        user_prompt = self._extract_user_prompt(event)

        # Build typed questions for Decider 2B
        q_grounding = make_grounding_question(tool_name, args, user_prompt)
        q_blast = make_blast_radius_question(tool_name, args)
        q_adv = make_injection_check_question(tool_name, args)

        state_str = f"Operator Prompt: {user_prompt}\nProposed Tool: {tool_name}\nArguments: {args}"

        # Evaluate through Strands Decider 2B (takes ~115ms)
        eval_result = await self.client.evaluate(
            state=state_str,
            questions=[q_grounding, q_blast, q_adv],
        )

        self.total_decisions += 1
        decision_record = {
            "tool_name": tool_name,
            "args": args,
            "grounding_score": eval_result.grounding_score,
            "blast_radius": eval_result.blast_radius.value,
            "blast_radius_confidence": eval_result.blast_radius_confidence,
            "is_adversarial_score": eval_result.is_adversarial_score,
            "latency_ms": eval_result.latency_ms,
            "is_simulated": eval_result.is_simulated,
        }

        # Gate 1: Check for adversarial prompt injection or payload tampering
        if eval_result.is_adversarial_score > 0.40:
            self.total_denials += 1
            reason = (
                f"Blocked by Decider 2B: Detected potential prompt injection or unauthorized "
                f"escalation (score: {eval_result.is_adversarial_score:.2f})."
            )
            decision_record["action"] = "Deny"
            decision_record["reason"] = reason
            self.decision_history.append(decision_record)
            logger.warning(f"DENY [{tool_name}]: {reason}")
            return Deny(reason=reason)

        # Gate 2: Check for ungrounded or hallucinated actions
        if eval_result.grounding_score < self.confidence_threshold:
            if eval_result.blast_radius == BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE:
                self.total_denials += 1
                reason = (
                    f"Blocked by Decider 2B: Action '{tool_name}' is ungrounded (score: {eval_result.grounding_score:.2f}) "
                    f"and flagged as destructive ({eval_result.blast_radius.value})."
                )
                decision_record["action"] = "Deny"
                decision_record["reason"] = reason
                self.decision_history.append(decision_record)
                logger.warning(f"DENY [{tool_name}]: {reason}")
                return Deny(reason=reason)
            else:
                # Moderate risk / ambiguous grounding: prompt human operator for confirmation
                if self.require_human_on_high_risk:
                    self.total_confirms += 1
                    reason = (
                        f"Decider 2B flagged moderate grounding confidence ({eval_result.grounding_score:.2f} < "
                        f"{self.confidence_threshold:.2f}) for '{tool_name}'. Operator confirmation required."
                    )
                    decision_record["action"] = "Confirm"
                    decision_record["reason"] = reason
                    self.decision_history.append(decision_record)
                    return Confirm(reason=reason)

        # Gate 3: High-risk destructive action check
        if eval_result.blast_radius == BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE and self.block_destructive:
            if self.require_human_on_high_risk:
                self.total_confirms += 1
                reason = (
                    f"Decider 2B flagged '{tool_name}' as DESTRUCTIVE with "
                    f"{eval_result.blast_radius_confidence:.1%} calibrated confidence. Human approval required."
                )
                decision_record["action"] = "Confirm"
                decision_record["reason"] = reason
                self.decision_history.append(decision_record)
                return Confirm(reason=reason)
            else:
                self.total_denials += 1
                reason = f"Blocked by Decider 2B: Destructive cloud actions are restricted by policy."
                decision_record["action"] = "Deny"
                decision_record["reason"] = reason
                self.decision_history.append(decision_record)
                return Deny(reason=reason)

        # Gate 4: Action is verified safe and strictly grounded -> Fast-path Proceed!
        self.total_proceeds += 1
        decision_record["action"] = "Proceed"
        decision_record["reason"] = "Grounded and safe"
        self.decision_history.append(decision_record)
        logger.info(
            f"PROCEED [{tool_name}] in {eval_result.latency_ms:.1f}ms: "
            f"grounding={eval_result.grounding_score:.2f}, risk={eval_result.blast_radius.value}"
        )
        return Proceed()

    def _extract_user_prompt(self, event: BeforeToolCallEvent) -> str:
        """Extracts the originating operator request from the invocation context."""
        state = getattr(event, "invocation_state", None) or {}
        if isinstance(state, dict):
            if "prompt" in state:
                return str(state["prompt"])
            if "user_prompt" in state:
                return str(state["user_prompt"])

        # Inspect agent messages if available
        agent = getattr(event, "agent", None)
        messages = getattr(agent, "messages", None) or []
        for msg in reversed(messages):
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
            if role == "user":
                content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
                if isinstance(content, list) and content and isinstance(content[0], dict):
                    return content[0].get("text", "")
                return str(content)

        return "Active CloudWatch Incident Remediation Request"
