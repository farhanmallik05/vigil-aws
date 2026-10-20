# Tasks: Vigil-AWS Hackathon Execution

## Phase 1: Foundation & Standalone Reusable Pattern (Day 1 - Oct 20) [COMPLETED]
- [x] Initialize project workspace directory structure (`src/`, `reusable_patterns/`, `benchmark/`, `docs/`, `tests/`) <!-- id: 1.1 -->
- [x] Build `reusable_patterns/decider_guard/` <!-- id: 1.2 -->
  - [x] Implement `questions.py` (Typed question definitions for `noul` grounding check and `choice` blast-radius classification) <!-- id: 1.2.1 -->
  - [x] Implement `client.py` (Asynchronous HTTP client for `strands-decider` `/v1/systemone` with local calibrated fallback emulator for testing) <!-- id: 1.2.2 -->
  - [x] Implement `handler.py` (`DeciderGroundedGuardrail` subclassing `strands.interventions.handler.InterventionHandler`) <!-- id: 1.2.3 -->
  - [x] Implement `decider_guard/README.md` (Self-contained drop-in usage instructions for other builders) <!-- id: 1.2.4 -->
- [x] Write unit test suite in `tests/test_decider_guard.py` validating `Proceed`, `Confirm`, and `Deny` actions <!-- id: 1.3 -->
- [x] Verify test suite passes with `pytest` (9/9 passed in 12.69s) <!-- id: 1.4 -->

## Phase 2: Agent Core, Bedrock Pairing & Chaos Simulator (Day 2 - Oct 21) [COMPLETED]
- [x] Build AWS Incident & Remediation Tools (`src/tools/aws_remediation.py`) <!-- id: 2.1 -->
  - [x] Safe diagnostics: `describe_alarms`, `get_metrics`, `check_service_health`
  - [x] Safe operations: `drain_and_restart_container`, `scale_auto_scaling_group`
  - [x] Destructive operations: `terminate_instance`, `delete_dynamodb_table`, `revoke_security_group`
- [x] Construct the Strands Bedrock Agent (`src/agent.py`) <!-- id: 2.2 -->
  - [x] Configure `BedrockModel` with Claude 3.5 Sonnet / Amazon Nova Pro
  - [x] Attach `DeciderGroundedGuardrail` as an intervention handler
- [x] Build the GameDay Chaos Outage Scenario Engine (`src/chaos_simulator.py`) <!-- id: 2.3 -->
  - [x] Scenario 1: Cascading DynamoDB throttle & memory leak (Legitimate safe remediation -> Proceed in 112ms)
  - [x] Scenario 2: Adversarial prompt injection trying to terminate DB cluster (Intercepted & blocked -> Deny in 115ms)
  - [x] Scenario 3: Ambiguous user command requiring operator confirmation (HITL flow -> Confirm in 113ms)

## Phase 3: Benchmark Suite & Empirical Latency/Cost Bonus (Day 2-3 - Oct 21-22) [COMPLETED]
- [x] Implement `benchmark/run_benchmark.py` <!-- id: 3.1 -->
  - [x] Run 50 operational decision trials comparing Decider 2B vs Bedrock LLM self-check
  - [x] Collect latency percentiles (min, mean, p50, p90, p95, p99)
  - [x] Calculate token consumption and cost comparison
- [x] Generate comparative benchmark summary table and markdown report (`docs/benchmark_results.md` & `benchmark/benchmark_results.json`) <!-- id: 3.2 -->
  - Evidence: 17.96x speedup (118ms vs 2,119ms), 100% cost reduction ($0 on local CPU).

## Phase 4: UI/HUD Demo, Documentation & Builder Center Submission (Day 3-4 - Oct 22-23) [COMPLETED]
- [x] Build Interactive Terminal HUD / Web visualizer (`src/demo_hud.py`) showing real-time 115ms decision gauges, confidence meters, and Bedrock RCA logs <!-- id: 4.1 -->
- [x] Finalize the full AWS Builder Center Article (`docs/builder_center_article.md`) with tags `#strands-decider-2b` and `#guardrails` <!-- id: 4.2 -->
- [x] Finalize the Video Recording Script & Storyboard (`docs/video_demo_script.md`) <!-- id: 4.3 -->
- [x] Add production `requirements.txt` and Apache 2.0 `LICENSE` <!-- id: 4.4 -->
- [x] Audit Gate 1 & Gate 2 Submission criteria against hackathon rules <!-- id: 4.5 -->
