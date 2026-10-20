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

## Phase 5: Extended Capabilities & Enterprise Reliability [COMPLETED]
- [x] Mathematical confidence calibration engine (`reusable_patterns/decider_guard/calibration.py`): ECE, MCE, Brier score, Temperature scaling, ASCII Reliability Diagrams <!-- id: 5.1 -->
- [x] AWS CloudWatch Embedded Metrics (EMF) structured logging for real-time telemetry <!-- id: 5.2 -->
- [x] Multimodal Vision Guardrail (`reusable_patterns/decider_guard/vision_guard.py`): Decider 2B Vision Tower diagram/topology grounding <!-- id: 5.3 -->
- [x] Dynamic Incident Model Router (`reusable_patterns/decider_guard/router.py`): Haiku 3.5 vs Claude 3.5 Sonnet routing (`#model-routing`) <!-- id: 5.4 -->
- [x] Comprehensive packaging: `pyproject.toml` and GitHub Actions CI workflow (`.github/workflows/ci.yml`) <!-- id: 5.5 -->

## Phase 6: Recursive Refinement & Verification (Loops 1–3) [COMPLETED]
- [x] **Loop 1 — Robustness & API Hardening:**
  - [x] Identified and fixed JSON serialization bug in `router.py` (`DeciderEvaluationResult.to_dict()`)
  - [x] Implemented thread-safe persistent async event loop runner (`run_async`) in `src/web_dashboard.py`
  - [x] Implemented 7 full REST API endpoints (`/api/scenarios`, `/api/run_scenario`, `/api/metrics`, `/api/evaluate_custom`, `/api/route_model`, `/api/evaluate_vision`, `/api/reset_metrics`)
  - [x] Automated integration test suite `tests/test_web_dashboard.py` (all tests passing)
- [x] **Loop 2 — Cyber-SRE Mission Control UI & Soundscape:**
  - [x] Created `src/dashboard_template.html` (Cyber-SRE Glassmorphic aesthetic, 6 interactive tabs)
  - [x] Integrated Web Audio API tactile feedback (chimes, sonar pings, alert buzzers, sweeps)
  - [x] Built interactive canvas constellation background with real-time particle physics
  - [x] Built interactive ROI cost-savings radar with real-time dollar impact calculator
- [x] **Loop 3 — Advanced Graphics, State Machine & Complete Reverification:**
  - [x] Created vector SVG architecture diagram (`docs/architecture_diagram.svg`)
  - [x] Created vector SVG 4-way reflex state machine diagram (`docs/decision_state_machine.svg`)
  - [x] Added SVG serving routes in `web_dashboard.py` and automated tests in `test_web_dashboard.py`
  - [x] Embedded all graphics and `#model-routing` tags into `README.md`, `builder_center_article.md`, and `video_demo_script.md`
  - [x] Full test suite reverification: **39/39 passing** with zero errors or warnings

## Phase 7: Official Submission Readiness, Portal Guide & Winning Strategy [COMPLETED]
- [x] Fetched and audited official AWS Builder Center portal requirements (`https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon-strands-decider`)
- [x] Converted all diagrams to high-contrast Light Mode (`docs/architecture_diagram.svg`, `docs/decision_state_machine.svg`, `docs/benchmark_chart.svg`)
- [x] Authored `docs/submission_checklist_and_guide.md` with 10-field copy-paste submission package, Gate 1 & Gate 2 rubric alignment, and video script breakdown
- [x] Verified 100% compliance across all 4 judging rubric categories (Creativity 30%, Effective Use + Bonus 30%, Communication 25%, Originality 15%)
- [x] Confirmed all 39 automated tests passing cleanly


