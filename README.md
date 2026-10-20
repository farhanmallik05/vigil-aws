# Vigil-AWS: Autonomous Cloud Incident & Remediation Commander
### *Sub-120ms System-1 Blast-Radius Guardrails & Intent Grounding for Autonomous AWS Bedrock Agents using Strands Decider 2B*

[![Hackathon](https://img.shields.io/badge/AWS%20Hackathon-Agent%20Experience-FF9900?logo=amazon-aws&logoColor=white)](https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon)
[![Model](https://img.shields.io/badge/Model-Strands%20Decider%202B-10B981)](https://strandsagents.com/blog/introducing-strands-decider/)
[![Tag](https://img.shields.io/badge/Pattern-%23guardrails-blue)](#)
[![Tag](https://img.shields.io/badge/Tag-%23strands--decider--2b-purple)](#)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Overview

**Vigil-AWS** is an autonomous AWS Incident & Chaos Remediation Commander engineered with a **Dual-Speed Cognitive Architecture**:
- **System 1 (Strands Decider 2B):** An ultra-fast (~115ms) reflex engine running on local hardware/CPU that intercepts every proposed operational tool call. It performs typed intent grounding (`noul`), blast-radius risk classification (`choice`), and prompt-injection detection with calibrated confidence scores before any action executes on AWS.
- **System 2 (Amazon Bedrock):** A frontier reasoning engine (Anthropic Claude 3.5 Sonnet / Amazon Nova Pro) that analyzes distributed trace telemetry, discovers root causes across microservices, and synthesizes executive post-mortems.

---

## Key Highlights

- **17.96x Faster Inline Guardrails:** Evaluates safety and intent grounding in **118.03 ms** median latency compared to 2,119.78 ms for LLM self-reflection.
- **100% Cost Savings on Safety Decisions:** Runs locally on CPU/Graviton at **$0 token cost** for repeated operational decisions.
- **Calibrated Reliability:** Utilizes Decider 2B's mathematically calibrated confidence probabilities (ECE < 0.02) to dynamically trigger `Proceed()`, `Confirm()` (Human-in-the-Loop), `Deny()`, or `Guide()`.
- **Multimodal Architecture Guardrail:** Uses Decider 2B's native vision tower to verify actions against CloudWatch dashboard graphs and network topology diagrams.
- **Dual-Pattern Synergy (Model Routing):** Dynamically routes simple alerts to Bedrock Claude 3.5 Haiku and complex cascading outages to Bedrock Claude 3.5 Sonnet.
- **Reusable Strands Asset:** Includes `decider_guard`, a drop-in package installable via `pip install .` for the Strands Agents SDK (`strands-agents`).

---

## Architecture

```mermaid
flowchart TD
    Alarm["CloudWatch Alarm / Operator Prompt"] --> Agent["Strands Bedrock Agent (System 2)"]
    Agent --> ToolCall["Proposes Tool Call (e.g. restart_service)"]
    ToolCall --> Guardrail["DeciderGroundedGuardrail (InterventionHandler)"]
    
    subgraph "Strands Decider 2B (System 1 ~115ms)"
        Guardrail --> Q1["Question 1 (noul): Grounding Check"]
        Guardrail --> Q2["Question 2 (choice): Blast-Radius [harmless, safe, destructive]"]
        Guardrail --> Q3["Question 3 (noul): Injection Check"]
        Q1 --> Decider["Decider 2B Engine"]
        Q2 --> Decider
        Q3 --> Decider
    end

    Decider --> Logic{"Gating Logic"}
    Logic -- "Grounded & Safe (Conf >= 0.88)" --> Exec["Proceed() -> Execute AWS Boto3 Tool"]
    Logic -- "Moderate Risk (0.70 <= Conf < 0.88)" --> HITL["Confirm() -> Operator Sign-off"]
    Logic -- "Ungrounded / Destructive" --> Block["Deny() -> Abort & Guide Agent"]

    Exec --> Cloud["AWS Cloud Infrastructure"]
    Cloud --> BedrockSummary["Amazon Bedrock Synthesis (RCA & Post-Mortem)"]
```

---

## Reusable Asset: 3-Line Drop-In Guardrail

Any builder using the Strands Agents SDK can integrate `DeciderGroundedGuardrail` into their own agent:

```python
from strands import Agent
from reusable_patterns.decider_guard import DeciderGroundedGuardrail

# 1. Initialize the guardrail
guard = DeciderGroundedGuardrail(
    decider_url="http://localhost:8000",
    confidence_threshold=0.88
)

# 2. Attach to any Strands agent
agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    tools=[my_aws_tools],
    interventions=[guard]
)
```

---

## Measured Performance Benchmarks

Results across 50 simulated operational incident scenarios:

| Metric | Bedrock Claude 3.5 Sonnet | Bedrock Haiku 3.5 | **Strands Decider 2B (Ours)** | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Minimum Latency (ms)** | 1,750.0 ms | 680.0 ms | **105.16 ms** | **16.6x faster** |
| **Median Latency p50 (ms)** | 2,119.78 ms | 910.23 ms | **118.03 ms** | **17.96x faster** |
| **Tail Latency p99 (ms)** | 2,649.47 ms | 1,082.61 ms | **124.88 ms** | **21.2x faster** |
| **Cost / 1k Invocations** | $24.00 | $4.80 | **$0.00** | **100% cost reduction** |

---

## Quickstart & Demos

### 1. Run the Interactive Web Dashboard
Launch the modern glassmorphism web HUD at `http://localhost:8501`:
```bash
python src/web_dashboard.py
```

### 2. Run the Terminal Console HUD
```bash
python src/demo_hud.py
```

### 3. Run the Automated Benchmark Suite
```bash
python benchmark/run_benchmark.py
```

### 4. Run the Full Test Suite
```bash
python -m pytest tests/ -v
```

---

## Directory Structure

```text
├── .github/workflows/
│   └── ci.yml                      # Automated CI testing workflow
├── docs/
│   ├── implementation_plan.md      # Detailed hackathon execution plan
│   ├── tasks.md                    # Milestone & task checklist
│   ├── benchmark_results.md        # Empirical latency and cost report
│   ├── builder_center_article.md   # Written article for AWS Builder Center
│   └── video_demo_script.md        # Script & storyboard for 3-minute video demo
├── reusable_patterns/
│   └── decider_guard/              # Reusable Strands Decider 2B Guardrail package
│       ├── handler.py              # Strands InterventionHandler implementation
│       ├── client.py               # Asynchronous Decider 2B client & emulator
│       ├── questions.py            # Typed questions (noul & choice)
│       ├── vision_guard.py         # Multimodal diagram & graph grounding
│       ├── router.py               # Incident model routing (Haiku vs Sonnet)
│       └── README.md               # Quickstart guide for the community
├── benchmark/
│   ├── benchmark_results.json      # Hard data from 50 operational decision trials
│   └── run_benchmark.py            # Latency and cost benchmarking harness
├── src/
│   ├── agent.py                    # Vigil-AWS Agent implementation
│   ├── chaos_simulator.py          # Simulated GameDay chaos incidents
│   ├── demo_hud.py                 # Real-time interactive terminal HUD
│   ├── web_dashboard.py            # Reactive dark-mode web application HUD
│   └── tools/
│       └── aws_remediation.py      # Safe & destructive AWS remediation tools
├── tests/
│   ├── test_decider_guard.py       # Core guardrail pytest suite
│   └── test_extended_capabilities.py # Vision and model router pytest suite
├── pyproject.toml                  # Python package configuration
├── requirements.txt
└── README.md
```

---

## Hackathon Submission Details

- **Event:** AWS Agent Experience Hackathon
- **Required Tag:** `#strands-decider-2b`
- **Pattern Tag:** `#guardrails`
- **Article:** [AWS Builder Center Submission Article](docs/builder_center_article.md)
- **Demo Video Script:** [Link to Demo Video Storyboard](docs/video_demo_script.md)
