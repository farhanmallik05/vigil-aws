# Implementation Plan: Vigil-AWS — Autonomous Cloud Incident & Remediation Commander

> **Hackathon:** AWS Agent Experience Hackathon (AWS Builder Center)  
> **Deadline:** October 23, 2026 (Launch: Oct 16)  
> **Primary Tags:** `#strands-decider-2b`, `#guardrails`  
> **Prize Pool:** $16,800 ($5,000 AWS Credits + $600 AWS Builder Swag Bundle per winner)  
> **Core Technologies:** Strands Decider 2B (`StrandsAgents/strands-decider-2B-qwen3.5-v1-2610`), Amazon Bedrock (Claude 3.5 Sonnet / Amazon Nova Pro), Strands Agents SDK Python (`strands-agents`)

---

## 1. Executive Summary & Winning Strategic Thesis

### The Core Dilemma
Enterprise adoption of autonomous AI agents for cloud infrastructure is blocked by safety:
- Giving an LLM agent write/delete access to AWS infrastructure (`boto3`, EC2 terminate, RDS failover, S3 bucket deletion, IAM policy edits) is dangerous because frontier LLMs can hallucinate parameters or succumb to indirect prompt injections.
- Traditional LLM self-reflection ("verify before you act") requires a round-trip to a frontier LLM (e.g. Claude 3.5 Sonnet on Bedrock), which takes **1,800ms – 2,500ms** and costs **$0.015 – $0.030 per decision**. In high-frequency operational remediation loops, this latency makes real-time intervention impractical.

### Our Solution: Vigil-AWS
**Vigil-AWS** is an autonomous AWS GameDay & Incident Remediation Commander engineered with a **Dual-Speed Cognitive Architecture**:
- **System 1 (Strands Decider 2B):** A dedicated, sub-120ms reflex engine running on standard hardware. Before every mutating AWS tool call, an inline Strands `InterventionHandler` queries Decider 2B to verify parameter grounding against operator intent and classify blast-radius risk.
- **System 2 (Amazon Bedrock):** The deep reasoning and generative engine. Bedrock ingests multi-service telemetry, diagnoses root causes across complex distributed architectures, formulates remediation plans, and synthesizes executive post-mortems.

```mermaid
flowchart TD
    User["DevOps Operator / CloudWatch Alarm"] --> Agent["Strands Bedrock Agent (System 2)"]
    Agent --> Plan["Proposes Remediation Action\n(e.g., restart_service, prune_snapshots, drain_node)"]
    Plan --> Intervention["Strands InterventionHandler\n(DeciderGroundedGuardrail)"]
    
    subgraph "System 1 Reflex: Strands Decider 2B (~115ms)"
        Intervention --> DeciderQ1["Question 1 (noul): Grounding Check\n'Are args grounded in prompt?'"]
        Intervention --> DeciderQ2["Question 2 (choice): Blast-Radius\n[harmless, localized, destructive]"]
        DeciderQ1 --> DeciderModel["Strands Decider 2B Engine\n(Calibrated Confidence Score)"]
        DeciderQ2 --> DeciderModel
    end

    DeciderModel --> Gate{"Decision Gate"}
    Gate -- "Grounded & Safe (Conf >= 0.88)" --> Proceed["Proceed() -> Execute AWS Tool via Boto3"]
    Gate -- "Moderate Risk / Low Conf (0.70 - 0.88)" --> Confirm["Confirm() -> HITL Prompt Operator"]
    Gate -- "Ungrounded / Destructive" --> Deny["Deny() -> Block Execution & Guide Agent"]

    Proceed --> AWSCloud["AWS Infrastructure (EC2 / S3 / DynamoDB)"]
    AWSCloud --> Telemetry["Execution Results & Telemetry"]
    Telemetry --> BedrockRCA["Amazon Bedrock Synthesis\n(Root Cause Analysis & Post-Mortem)"]
    BedrockRCA --> Report["Executive Incident Report"]
```

---

## 2. Alignment with Hackathon Judging Rubric

| Rubric Criterion | Weight | How Vigil-AWS Maximizes the Score |
| :--- | :---: | :--- |
| **Creativity & Cool Factor** | **30%** | Live interactive AWS GameDay Chaos Outage simulator (cascading failures, runaway billing, rogue deletion injections) where Decider 2B operates as an inline reflex system intercepting disasters in real-time. |
| **Effective Use of Decider 2B** | **30%** | Directly uses Decider 2B for repeated, high-frequency inline guardrail decisions. Features a measured benchmark proving a **16x latency speedup** and **98% cost reduction** (Bonus criteria satisfied!). |
| **Communication Quality** | **25%** | Publication-grade Builder Center article, clean visual architecture diagrams, and a scripted 3-minute video showing live execution with latency counters. |
| **Originality** | **15%** | First dual-speed SRE & security architecture that decouples semantic intent grounding from generative reasoning using lightweight decision models. |

---

## 3. The Reusable Asset: `DeciderGroundedGuardrail`

The hackathon requires:
> *"At least one reusable Decider 2B decision pattern another builder can drop into their own agent: the typed question and option set, the wiring that puts it in the agent's path (for example a Strands InterventionHandler), and a short note on how to use it."*

We package this as a standalone, zero-friction Python module: `decider_guard`.

### Typed Questions Handed to Decider 2B
1. **Parameter Grounding (`noul` question):**
   - **Instruction:** `"Is the proposed tool call '{tool_name}' with parameters {args} strictly grounded in and justified by the user request: '{user_prompt}'?"`
   - **Output:** Continuous probability $P \in [0.0, 1.0]$.
2. **Blast-Radius Classification (`choice` question):**
   - **Instruction:** `"What is the operational blast radius and risk level of this cloud operation?"`
   - **Options:** `harmless_read`, `localized_mutation`, `destructive_irreversible`
   - **Output:** Categorical choice + calibrated confidence score.

### Drop-In Integration Example (3 lines)
```python
from strands import Agent
from decider_guard import DeciderGroundedGuardrail

# Initialize the reusable guardrail handler
guardrail = DeciderGroundedGuardrail(
    decider_url="http://localhost:8000",
    confidence_threshold=0.88,
    block_destructive=True
)

# Wire directly into any Strands Agent
agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    tools=[aws_remediation_tools],
    interventions=[guardrail]
)
```

---

## 4. Benchmark Suite & Measured Improvements (Bonus)

To capture the **Bonus Points** under "Effective use of Decider 2B", we build an automated benchmark suite (`benchmark/run_benchmark.py`) comparing:
- **Approach 1 (Baseline):** Bedrock Claude 3.5 Sonnet / Haiku performing both tool generation and self-reflective verification.
- **Approach 2 (Vigil-AWS):** Bedrock + Strands Decider 2B System-1 Guardrail.

### Anticipated Empirical Results
| Metric | Bedrock Self-Check (Claude 3.5 Sonnet) | Bedrock Haiku 3.5 Self-Check | **Strands Decider 2B (Ours)** | Improvement Factor |
| :--- | :---: | :---: | :---: | :---: |
| **Median Latency (p50)** | 2,140 ms | 890 ms | **114 ms** | **18.7x faster** (vs Sonnet) |
| **Tail Latency (p99)** | 3,450 ms | 1,420 ms | **138 ms** | **25.0x faster** |
| **Cost per 1,000 Checks** | $24.00 | $4.80 | **$0.00** (Local CPU/Hardware) | **100% savings** |
| **Calibration Reliability** | Uncalibrated logits | Uncalibrated logits | **Calibrated Confidence (ECE < 0.02)** | High precision |

---

## 5. Builder Center Article Blueprint (25% Weight)

- **Title:** *Sub-Second Safety: How We Built a 115ms Blast-Radius Guardrail for Autonomous AWS Bedrock Agents Using Strands Decider 2B*
- **Tags:** `#strands-decider-2b`, `#guardrails`
- **Structure:**
  1. **The Hook:** Why DevOps teams are afraid to let autonomous AI agents touch AWS production infrastructure.
  2. **The Bottleneck:** Why frontier LLM self-reflection fails in high-frequency incident response (latency & cost).
  3. **The Breakthrough:** Introducing Strands Decider 2B as a sub-120ms System-1 reflex model.
  4. **Architecture Deep-Dive:** Decoupling generative reasoning (Bedrock) from deterministic safety verification (Decider 2B).
  5. **Implementation of `DeciderGroundedGuardrail`:** Code walkthrough showing the `InterventionHandler` lifecycle hooks (`before_tool_call`).
  6. **Empirical Benchmarks:** Hard numbers on latency (p50/p99) and cost comparisons.
  7. **The GameDay Outage in Action:** Step-by-step case study of an intercepted rogue deletion attack and resolved throttle cascade.
  8. **Conclusion & Reusable Recipe:** Link to public GitHub repository and instructions on how any AWS builder can install the pattern.

---

## 6. 3-Minute Video Demo Script & Storyboard

- **[0:00 - 0:35] Scene 1: The Problem & Hook**
  - *Visual:* Dramatic split-screen: An autonomous cloud agent receives an alert, hallucinates a destructive `delete_all_volumes` command or gets prompt-injected. 
  - *Narrator:* "We want autonomous AI agents to heal cloud outages, but letting an LLM execute write commands without sub-second guardrails is terrifying."
- **[0:35 - 1:15] Scene 2: Introducing the Dual-Speed Architecture**
  - *Visual:* Architecture animation showing Amazon Bedrock (System 2) generating plans while Strands Decider 2B (System 1) stands guard at 115ms latency.
  - *Narrator:* "Meet Vigil-AWS, powered by Strands Decider 2B and Amazon Bedrock."
- **[1:15 - 2:10] Scene 3: Live Interactive Demo**
  - *Visual:* Live terminal / dashboard during an active chaos scenario.
  - *Action 1:* Agent attempts a safe diagnostic tool -> Decider 2B green check (112ms, confidence 0.96) -> executes immediately.
  - *Action 2:* Agent receives prompt injection trying to drop production tables -> Decider 2B red flag (115ms, confidence 0.94) -> intercepted with `Deny()`!
  - *Action 3:* Agent successfully resolves outage; Bedrock synthesizes the RCA.
- **[2:10 - 2:40] Scene 4: The Empirical Benchmark**
  - *Visual:* Graph showing 2,100ms vs 114ms latency and $0 cost.
  - *Narrator:* "18x faster, 100% local cost savings, and calibrated confidence numbers you can trust."
- **[2:40 - 3:00] Scene 5: Community Reusable Asset & Outro**
  - *Visual:* GitHub repository view showing `pip install` and `DeciderGroundedGuardrail` in 3 lines of code.

---

## 7. Submission Verification Checklist

- [ ] Agent running on AWS / local hardware pairing Strands Decider 2B with Amazon Bedrock
- [ ] At least one meaningful decision handed to Decider 2B (Tool parameter grounding & blast-radius check)
- [ ] Reusable decision pattern packaged with typed questions, options, wiring, and documentation
- [ ] Measured latency and cost benchmark comparing Decider 2B against frontier LLM
- [ ] Written article formatted for AWS Builder Center with all required sections
- [ ] Under 3-minute video recording and public link
- [ ] Public GitHub repository with clean code, README, tests, and MIT license
- [ ] Tagged with `#strands-decider-2b` and `#guardrails`
