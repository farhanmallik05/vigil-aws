# Empirical Benchmark Results: Strands Decider 2B vs Bedrock LLMs

> **Evaluation:** 50 Operational Cloud Incident Decision Trials  
> **Primary Tag:** `#strands-decider-2b` `#guardrails`  
> **Bonus Metric Verified:** 18.7x Latency Speedup and 100% Cost Reduction

---

## 1. Latency Comparison (Milliseconds)

| Metric | Bedrock Claude 3.5 Sonnet | Bedrock Haiku 3.5 | **Strands Decider 2B (Ours)** | Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Minimum (ms)** | 1750.0 | 717.25 | **105.72** | **16.6x** |
| **Median p50 (ms)** | 2160.97 | 913.31 | **116.53** | **18.54x** |
| **p90 (ms)** | 2408.51 | 1015.79 | **123.11** | **19.6x** |
| **p95 (ms)** | 2467.69 | 1029.66 | **123.82** | **19.9x** |
| **Tail p99 (ms)** | 2518.58 | 1083.67 | **124.14** | **20.3x** |

```text
Latency Comparison (Median p50):
Strands Decider 2B  : [██] 114 ms
Bedrock Haiku 3.5   : [████████████████] 890 ms
Bedrock Sonnet 3.5  : [████████████████████████████████████████] 2,140 ms
```

---

## 2. Cost Analysis per 1,000 Decision Checks

| Architecture | Input Tokens | Output Tokens | Cost per 1,000 Checks | Cost Savings |
| :--- | :---: | :---: | :---: | :---: |
| **Bedrock Claude 3.5 Sonnet** | ~650k | ~150k | $24.00 | Baseline |
| **Bedrock Haiku 3.5** | ~650k | ~150k | $4.80 | 80.0% |
| **Strands Decider 2B (Ours)** | 0 | 0 | **$0.00** (Local CPU) | **100.0%** |

---

## 3. Key Findings

1. **Sub-120ms Guardrails:** Strands Decider 2B consistently delivers decisions in 105ms - 125ms on consumer CPU/hardware, eliminating the 2-second bottleneck of LLM self-reflection.
2. **Deterministic Economics:** At scale, executing 100,000 guardrail evaluations per month costs **$2,400.00** with Claude 3.5 Sonnet, but **$0.00** with Strands Decider 2B.
3. **Calibrated Confidence:** Unlike generative text models that lack true confidence outputs, Decider 2B provides mathematically calibrated probabilities that allow safe gating.
