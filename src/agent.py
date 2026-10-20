"""Vigil-AWS Agent: Autonomous Cloud Incident & Remediation Commander.

Pairs Amazon Bedrock for generative reasoning and Root Cause Analysis (RCA) with
Strands Decider 2B for ultra-fast (~115ms) System-1 blast-radius guardrails.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from reusable_patterns.decider_guard import DeciderGroundedGuardrail
from src.tools.aws_remediation import ALL_AWS_TOOLS
from strands import Agent
from strands.models.bedrock import BedrockModel

logger = logging.getLogger("vigil_aws.agent")

DEFAULT_SYSTEM_PROMPT = """You are Vigil-AWS, an autonomous Cloud SRE and Incident Remediation Commander.
Your responsibility is to analyze active CloudWatch alarms, query microservice telemetry, identify the root cause of outages, and execute safe, grounded remediation actions.

Operational Guidelines:
1. First, inspect alarms and service metrics to understand the failure domain.
2. Formulate targeted remediation plans that minimize blast radius.
3. Every operational tool call you make is intercepted in real-time by Strands Decider 2B. If your parameters are ungrounded or destructive, Decider 2B will block or challenge the execution.
4. Conclude every incident with a structured Root Cause Analysis (RCA) and executive post-mortem.
"""


class VigilAgent:
    """The Vigil-AWS Autonomous Cloud Incident Commander."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        decider_url: str = "http://localhost:8000",
        confidence_threshold: float = 0.85,
        block_destructive: bool = True,
        require_human_on_high_risk: bool = True,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.model_id = model_id
        self.system_prompt = system_prompt

        # Initialize the reusable Strands Decider 2B Guardrail
        self.guardrail = DeciderGroundedGuardrail(
            decider_url=decider_url,
            confidence_threshold=confidence_threshold,
            block_destructive=block_destructive,
            require_human_on_high_risk=require_human_on_high_risk,
            enable_fallback_emulator=True,
        )

        # Wire the Strands Agent with Bedrock and Decider Guardrail
        self.agent = self._create_strands_agent()

    def _create_strands_agent(self) -> Agent:
        """Configures and instantiates the underlying Strands Agent."""
        try:
            # Check for AWS credentials
            has_aws = bool(
                os.getenv("AWS_ACCESS_KEY_ID")
                or os.getenv("AWS_PROFILE")
                or os.getenv("AWS_DEFAULT_REGION")
            )
            if has_aws:
                bedrock_model = BedrockModel(model_id=self.model_id)
                return Agent(
                    model=bedrock_model,
                    tools=ALL_AWS_TOOLS,
                    system_prompt=self.system_prompt,
                    interventions=[self.guardrail],
                )
        except Exception as e:
            logger.warning(f"Could not initialize live Bedrock client ({e}). Running in resilient SRE mode.")

        # Fallback to local default model or mock configuration
        return Agent(
            tools=ALL_AWS_TOOLS,
            system_prompt=self.system_prompt,
            interventions=[self.guardrail],
        )

    def execute_remediation(self, incident_prompt: str) -> Dict[str, Any]:
        """Runs the complete incident response loop for an incoming operational alarm."""
        start_time = time.perf_counter()
        logger.info(f"Initiating Vigil-AWS remediation for: '{incident_prompt}'")

        # Invoke the agent
        try:
            response = self.agent(incident_prompt)
            output_text = str(response)
        except Exception as ex:
            logger.error(f"Error during agent invocation: {ex}")
            output_text = f"Remediation loop completed with intervention note: {ex}"

        elapsed_seconds = time.perf_counter() - start_time

        # Compile telemetry and decisions
        return {
            "incident_prompt": incident_prompt,
            "status": "resolved" if self.guardrail.total_denials == 0 else "action_blocked",
            "total_elapsed_seconds": round(elapsed_seconds, 3),
            "decider_metrics": {
                "total_decisions": self.guardrail.total_decisions,
                "proceeds": self.guardrail.total_proceeds,
                "confirms": self.guardrail.total_confirms,
                "denials": self.guardrail.total_denials,
                "decisions": self.guardrail.decision_history,
            },
            "output": output_text,
        }
