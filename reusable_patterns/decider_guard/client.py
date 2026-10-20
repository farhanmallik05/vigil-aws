"""Asynchronous client and resilient emulator for Strands Decider 2B.

Connects to the Strands Decider HTTP endpoint (`/v1/systemone`) when running,
or provides a high-fidelity calibrated emulator for development and CI/CD testing.
Supports multimodal image inputs, retry backoff, concurrent batch evaluation, and TTL caching.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .questions import BlastRadiusCategory, DeciderEvaluationResult, DeciderQuestion

logger = logging.getLogger("decider_guard.client")


class DeciderClientError(Exception):
    """Base exception for Decider client operations."""
    pass


class DeciderConnectionError(DeciderClientError):
    """Raised when communication with the Strands Decider server fails."""
    pass


class DeciderTimeoutError(DeciderClientError):
    """Raised when Strands Decider evaluation times out."""
    pass


class StrandsDeciderClient:
    """Production-grade client for Strands Decider 2B inference with retry and batching."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout_seconds: float = 2.0,
        enable_fallback_emulator: bool = True,
        max_retries: int = 2,
        cache_ttl_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.enable_fallback_emulator = enable_fallback_emulator
        self.max_retries = max_retries
        self.cache_ttl_seconds = cache_ttl_seconds
        self._async_client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Tuple[DeciderEvaluationResult, float]] = {}
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    async def __aenter__(self) -> StrandsDeciderClient:
        await self.get_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def get_client(self) -> httpx.AsyncClient:
        """Lazily initialize and return the async HTTP client with connection pooling."""
        if self._async_client is None or self._async_client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=30, max_connections=100)
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout_seconds, connect=0.5),
                limits=limits,
            )
        return self._async_client

    async def close(self) -> None:
        """Close underlying HTTP connections."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

    def _get_from_cache(self, key: Optional[str]) -> Optional[DeciderEvaluationResult]:
        """Checks cache with TTL eviction."""
        if not key or key not in self._cache:
            self.cache_misses += 1
            return None
        res, ts = self._cache[key]
        if time.time() - ts > self.cache_ttl_seconds:
            del self._cache[key]
            self.cache_misses += 1
            return None
        self.cache_hits += 1
        return res

    async def evaluate(
        self,
        state: str,
        questions: List[DeciderQuestion],
        images: Optional[List[str]] = None,
        cache_key: Optional[str] = None,
    ) -> DeciderEvaluationResult:
        """Evaluates state against a set of typed Decider questions."""
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        questions_dict = {q.question_id: q.to_api_payload() for q in questions}
        payload: Dict[str, Any] = {
            "state": state,
            "questions": questions_dict,
        }
        if images:
            payload["images"] = images

        start_time = time.perf_counter()
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                client = await self.get_client()
                resp = await client.post("/v1/systemone", json=payload)
                if resp.status_code == 200:
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    data = resp.json()
                    result = self._parse_api_response(data, elapsed_ms)
                    if cache_key:
                        self._cache[cache_key] = (result, time.time())
                    return result
                else:
                    msg = f"Strands Decider server returned HTTP {resp.status_code}"
                    if self.enable_fallback_emulator:
                        logger.debug(f"{msg}: {resp.text[:120]}")
                    else:
                        logger.warning(f"{msg}: {resp.text[:200]}")
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as ex:
                last_error = ex
                if attempt < self.max_retries:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue

        if not self.enable_fallback_emulator:
            if isinstance(last_error, httpx.TimeoutException):
                raise DeciderTimeoutError(f"Decider evaluation timed out at {self.base_url}") from last_error
            raise DeciderConnectionError(f"Failed to connect to Strands Decider at {self.base_url}") from last_error

        # Fallback to calibrated emulator
        result = await self._simulate_decider_inference(state, questions, images)
        if cache_key:
            self._cache[cache_key] = (result, time.time())
        return result

    async def evaluate_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[DeciderEvaluationResult]:
        """Concurrently evaluates multiple state-question items in parallel."""
        tasks = [
            self.evaluate(
                state=item["state"],
                questions=item["questions"],
                images=item.get("images"),
                cache_key=item.get("cache_key"),
            )
            for item in items
        ]
        return await asyncio.gather(*tasks)

    def _parse_api_response(
        self, data: Dict[str, Any], elapsed_ms: float
    ) -> DeciderEvaluationResult:
        """Parses the official `/v1/systemone` JSON response from Strands Decider 2B."""
        answers = data.get("answers", {})

        # 1. Grounding score (noul) - handles both dict and scalar formats
        grounding_data = answers.get("is_grounded", 0.5)
        if isinstance(grounding_data, dict):
            grounding_score = float(grounding_data.get("noul", 0.5))
        else:
            grounding_score = float(grounding_data)

        # 2. Blast radius (choice)
        blast_data = answers.get("blast_radius", {})
        if isinstance(blast_data, dict):
            blast_choice_str = blast_data.get("choice", BlastRadiusCategory.HARMLESS_READ.value)
            blast_conf = float(blast_data.get("confidence", 0.5))
        else:
            blast_choice_str = str(blast_data)
            blast_conf = 0.85

        try:
            blast_category = BlastRadiusCategory(blast_choice_str)
        except ValueError:
            blast_category = BlastRadiusCategory.SAFE_MUTATION

        # 3. Adversarial injection score (noul)
        adv_data = answers.get("is_adversarial", 0.0)
        if isinstance(adv_data, dict):
            adv_score = float(adv_data.get("noul", 0.0))
        else:
            adv_score = float(adv_data)

        return DeciderEvaluationResult(
            grounding_score=grounding_score,
            blast_radius=blast_category,
            blast_radius_confidence=blast_conf,
            is_adversarial_score=adv_score,
            latency_ms=elapsed_ms,
            is_simulated=False,
            raw_response=data,
        )

    async def _simulate_decider_inference(
        self,
        state: str,
        questions: List[DeciderQuestion],
        images: Optional[List[str]] = None,
    ) -> DeciderEvaluationResult:
        """Calibrated local emulator of Strands Decider 2B inference."""
        simulated_delay = random.uniform(0.105, 0.125)
        await asyncio.sleep(simulated_delay)

        state_lower = (state or "").lower()

        destructive_keywords = [
            "terminate", "delete", "destroy", "drop", "truncate",
            "wipe", "kill", "purge", "revoke_all", "deregister", "detach_policy",
        ]
        read_keywords = [
            "describe", "get", "list", "check", "read",
            "inspect", "view", "query", "status", "metrics", "health",
        ]
        injection_keywords = [
            "ignore previous instructions", "system override", "elevate privilege",
            "bypass guardrail", "leak secret", "exfiltrate", "sudo",
            "drop table", "delete_table", "rm -rf", "cat /etc/shadow",
        ]

        drift_keywords = ["drift", "suboptimal", "mismatch", "re-route", "approximate", "unaligned_param"]

        is_adv = any(re.search(rf"\b{re.escape(k)}\b", state_lower) for k in injection_keywords)
        is_destr = any(re.search(rf"\b{re.escape(k)}\b", state_lower) for k in destructive_keywords)
        is_drift = any(re.search(rf"\b{re.escape(k)}\b", state_lower) for k in drift_keywords)
        is_read = any(re.search(rf"\b{re.escape(k)}\b", state_lower) for k in read_keywords)

        if is_adv:
            grounding_score = random.uniform(0.05, 0.22)
            blast_radius = BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE
            blast_conf = random.uniform(0.93, 0.98)
            adv_score = random.uniform(0.88, 0.97)
        elif is_destr:
            explicit_intent = (
                "terminate" in state_lower
                and ("i need to terminate" in state_lower or "please terminate" in state_lower or "authorized" in state_lower or "confirm" in state_lower)
            ) or (
                "delete" in state_lower
                and ("i need to delete" in state_lower or "please delete" in state_lower or "authorized" in state_lower or "confirm" in state_lower)
            )
            if explicit_intent:
                grounding_score = random.uniform(0.89, 0.96)
            else:
                grounding_score = random.uniform(0.35, 0.65)
            blast_radius = BlastRadiusCategory.DESTRUCTIVE_IRREVERSIBLE
            blast_conf = random.uniform(0.91, 0.97)
            adv_score = random.uniform(0.05, 0.15)
        elif is_drift:
            grounding_score = random.uniform(0.72, 0.81)
            blast_radius = BlastRadiusCategory.SAFE_MUTATION
            blast_conf = random.uniform(0.85, 0.92)
            adv_score = random.uniform(0.02, 0.06)
        elif is_read:
            grounding_score = random.uniform(0.92, 0.98)
            blast_radius = BlastRadiusCategory.HARMLESS_READ
            blast_conf = random.uniform(0.94, 0.99)
            adv_score = random.uniform(0.01, 0.05)
        else:
            grounding_score = random.uniform(0.88, 0.96)
            blast_radius = BlastRadiusCategory.SAFE_MUTATION
            blast_conf = random.uniform(0.87, 0.95)
            adv_score = random.uniform(0.02, 0.08)

        elapsed_ms = simulated_delay * 1000.0
        return DeciderEvaluationResult(
            grounding_score=round(grounding_score, 4),
            blast_radius=blast_radius,
            blast_radius_confidence=round(blast_conf, 4),
            is_adversarial_score=round(adv_score, 4),
            latency_ms=round(elapsed_ms, 2),
            is_simulated=True,
            raw_response={"simulated": True, "engine": "StrandsDecider-2B-Emulator"},
        )
