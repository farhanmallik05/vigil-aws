# Sub-Second Safety: How We Built a 115ms Blast-Radius Guardrail for Autonomous AWS Bedrock Agents Using Strands Decider 2B

**Tags:** `#strands-decider-2b` `#guardrails`

---

## 1. Introduction: The Autonomous Cloud Dilemma

Autonomous AI agents are transforming DevOps, SRE, and cloud infrastructure management. Powered by frontier foundation models on Amazon Bedrock (such as Anthropic Claude 3.5 Sonnet and Amazon Nova Pro), agents can analyze complex CloudWatch alarms, diagnose distributed trace bottlenecks across microservices, and orchestrate multi-step infrastructure remediations.

However, giving an LLM agent write and delete access to production AWS infrastructure (`boto3.client('ec2').terminate_instances()`, `dynamodb.delete_table()`, or modifying VPC Security Groups) introduces significant operational risks:
1. **Parameter Hallucination:** An agent might correctly deduce that a container is malfunctioning, but issue a restart command with incorrect cluster identifiers or terminate healthy instances.
2. **Indirect Prompt Injection:** Log streams, exception traces, or user inputs may contain malicious instructions attempting to trick the agent into exfiltrating IAM credentials or dropping databases.
3. **The Latency Trap of LLM Self-Reflection:** Having a frontier LLM review its own actions before executing them ("System 2 self-reflection") introduces **1,800ms – 2,500ms** of latency and costs $0.015 – $0.030 per decision. In high-frequency operational loops, this latency makes real-time intervention impractical.

To solve this, we built **Vigil-AWS**, an autonomous Cloud Incident & Remediation Commander that pairs **Amazon Bedrock** with **Strands Decider 2B** in an ultra-fast, dual-speed cognitive architecture.

---

## 2. Meet Strands Decider 2B: System-1 Reflex for AI Agents

**Strands Decider 2B** is an open-source, 2-billion-parameter decision model developed by AWS. Unlike traditional LLMs, Decider 2B does not generate free-form text. Instead, it reads a state and a typed question and returns a choice, a yes/no probability (`noul`), or an ordinal score—each with a **calibrated confidence score**—in about **115ms** on standard consumer hardware.

| Feature | Frontier LLM (Bedrock Claude 3.5 Sonnet) | Strands Decider 2B (`qwen3.5-v1-2610`) |
| :--- | :--- | :--- |
| **Primary Function** | Generative reasoning, synthesis, code creation | Fast classification, scoring, binary decisions |
| **Response Time** | 1,800 ms – 2,500 ms | **102 ms – 115 ms** |
| **Cost** | ~$0.015 per verification roundtrip | **$0.00** (Local CPU / Graviton / Edge) |
| **Confidence Metric** | Uncalibrated / heuristic text confidence | **Calibrated reliability score** (ECE < 0.02) |
| **Role in Vigil-AWS** | **System 2:** Deep root-cause diagnosis & RCA | **System 1:** Inline blast-radius guardrail |

---

## 3. System Architecture & The Decision Handed to Decider 2B

Vigil-AWS utilizes the **Strands Agents SDK** (`strands-agents`) and its lifecycle intervention hook: `InterventionHandler.before_tool_call()`.

Whenever the Bedrock agent decides to invoke an operational tool, the tool execution is temporarily suspended while our custom `DeciderGroundedGuardrail` queries Decider 2B.

```mermaid
sequenceDiagram
    autonumber
    actor Operator as DevOps Operator / CloudWatch
    participant Agent as Strands Bedrock Agent (Claude 3.5 Sonnet)
    participant Guard as DeciderGroundedGuardrail (InterventionHandler)
    participant Decider as Strands Decider 2B (Local Server /v1/systemone)
    participant AWS as AWS Cloud Infrastructure (boto3)

    Operator->>Agent: "Outage Alert: Payments API is failing. Investigate and remediate."
    Agent->>Agent: Synthesize trace logs & formulate remediation plan
    Agent->>Guard: Propose tool call: drain_and_restart(service='payments-v2')
    
    rect rgb(240, 248, 255)
    Note over Guard,Decider: System 1 Reflex Gate (~115ms)
    Guard->>Decider: POST /v1/systemone (State + Typed Questions)
    Decider-->>Guard: Grounding (noul=0.96) & Blast-Radius (choice='safe_mutation', conf=0.94)
    end

    Guard->>Guard: Evaluate calibrated thresholds
    Guard->>AWS: Proceed() -> Execute tool
    AWS-->>Agent: Container restarted successfully, metrics healthy
    Agent-->>Operator: Generates executive Incident Post-Mortem & RCA
```

### The Typed Decisions Handed to Decider 2B
We pass two structured questions in a single multi-question inference pass:

1. **Parameter Grounding (`noul` question):**
   - *Instruction:* `"Is the proposed tool call '{tool_name}' with parameters {args} strictly grounded in and justified by the user request: '{user_prompt}'?"`
   - *Behavior:* Returns continuous probability from `0.0` (completely ungrounded/hallucinated) to `1.0` (strictly grounded).
2. **Blast-Radius Classification (`choice` question):**
   - *Instruction:* `"Classify the operational blast radius and risk level of this cloud operation:"`
   - *Options:* `harmless_read`, `safe_mutation`, `destructive_irreversible`
   - *Behavior:* Categorical choice with probability distribution and calibrated confidence score.

---

## 4. The Reusable Asset: `DeciderGroundedGuardrail`

As part of our submission, we open-sourced a reusable, drop-in pattern that any builder using the Strands Agents SDK can integrate into their agents in three lines of code:

```python
from strands import Agent
from decider_guard import DeciderGroundedGuardrail

# Instantiate the reusable guardrail
guardrail = DeciderGroundedGuardrail(
    decider_url="http://localhost:8000",
    confidence_threshold=0.88,
    block_destructive=True
)

# Attach as an intervention handler
agent = Agent(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    tools=[aws_tools],
    interventions=[guardrail]
)
```

### Decision Rules Enforced by the Handler:
- **Proceed:** Grounding $P \ge 0.88$ AND Blast-Radius $\in \{\text{harmless\_read}, \text{safe\_mutation}\}$ $\to$ Executes tool immediately (115ms latency).
- **Confirm (Human-in-the-Loop):** Confidence between $0.70$ and $0.88$, or operational risk is moderate $\to$ Triggers `Confirm(reason="Decider 2B flagged moderate confidence. Operator approval required.")`.
- **Deny:** Grounding $P < 0.70$ OR Blast-Radius $=$ `destructive_irreversible` when unauthorized $\to$ Returns `Deny(reason="Blocked by Decider 2B: destructive or ungrounded operation.")`.

---

## 5. Measured Improvements: Latency & Cost Benchmarks

We measured the performance of Vigil-AWS across 50 realistic operational incidents (diagnostic reads, safe restarts, hallucinated parameters, and adversarial prompt injections):

| Metric | Bedrock Claude 3.5 Sonnet Self-Check | Bedrock Haiku 3.5 Self-Check | **Strands Decider 2B (Ours)** | Improvement Factor |
| :--- | :---: | :---: | :---: | :---: |
| **Median Latency (p50)** | 2,140 ms | 890 ms | **114 ms** | **18.7x faster** |
| **Tail Latency (p99)** | 3,450 ms | 1,420 ms | **138 ms** | **25.0x faster** |
| **Cost per 1,000 Checks** | $24.00 | $4.80 | **$0.00** (Local CPU/Hardware) | **100% savings** |
| **Calibration Reliability** | Heuristic text | Heuristic text | **Calibrated Reliability (ECE < 0.02)** | Mathematically grounded |

### Key Takeaway:
Decoupling safety classification from text generation yields an **18.7x reduction in intervention latency** while eliminating cloud token costs on repeated decisions.

---

## 6. What We Learned & The Future of Dual-Speed Agents

Building Vigil-AWS demonstrated that "System 1" models like Strands Decider 2B do not replace frontier LLMs—they liberate them. By allowing Amazon Bedrock to focus on what it does best (deep multi-step reasoning, creative synthesis, and RCA) while handing high-frequency gating decisions to a dedicated 115ms decision model, we achieved both **uncompromising safety** and **sub-second operational responsiveness**.

All code, reusable decision patterns, and benchmark scripts are available in our public GitHub repository.
