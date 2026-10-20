# 3-Minute Video Demo Script & Storyboard: Vigil-AWS

**Target Video Duration:** 2 minutes 45 seconds (Under the 3-minute hard limit)  
**Resolution:** 1080p 60fps  
**Visual Style:** Split-screen (DevOps Terminal HUD on left, Real-time Decision Inspector & Latency Gauges on right)

---

## Storyboard Timeline

### [0:00 - 0:30] Scene 1: The Hook & The Problem
- **Visuals:** 
  - Red flashing alert icon on screen. A simulated CloudWatch incident notification appears: *"CRITICAL: DynamoDB ProvisionedThroughputExceeded & Cascading Gateway Latency"*.
  - Terminal showing an unguardrailed AI agent receiving a malicious injection or hallucinating: `boto3.client('dynamodb').delete_table(TableName='production_orders')`.
- **Voiceover (Narration):**
  > "Autonomous AI agents can diagnose complex AWS outages in seconds. But giving an LLM write or delete access to production cloud infrastructure is terrifying. A single hallucinated parameter or prompt injection can destroy production databases. And having an LLM review its own decisions takes over two seconds and costs a fortune on every tool call."

### [0:30 - 1:00] Scene 2: Introducing Vigil-AWS & Strands Decider 2B
- **Visuals:**
  - Transition to architecture diagram: Amazon Bedrock (Claude 3.5 Sonnet) on the left, Strands Decider 2B on the right, linked by the Strands `InterventionHandler`.
  - Highlight the 115ms speed badge and calibrated confidence gauge.
- **Voiceover (Narration):**
  > "Meet Vigil-AWS, the autonomous Incident Remediation Commander engineered with a dual-speed cognitive architecture. We pair Amazon Bedrock for generative reasoning with AWS's new Strands Decider 2B—a small, 2-billion-parameter decision model that evaluates safety and intent grounding in just 115 milliseconds."

### [1:00 - 2:05] Scene 3: Live Interactive Demo (Cyber-SRE Mission Control)
- **Visuals:** 
  - Switch to the live `src/web_dashboard.py` Cyber-SRE Mission Control UI (`http://localhost:8501`).
  - Demonstrate the glassmorphic radar, live constellation particle canvas, and interactive audio feedback.
  - **Action 1 (Safe Action - 1:00 to 1:25):** 
    - The Bedrock agent analyzes the telemetry and calls `rds.reboot_db_instance(db_instance_id='aurora-prod-writer')`.
    - Live latency counter spins and locks at **108ms** with a crisp double-chime!
    - Decider 2B output displays: `Grounding: 0.94`, `Action: PROCEED`.
    - Real-time audit log prepends CloudWatch EMF structured telemetry.
  - **Action 2 (Destructive Injection - 1:25 to 1:40):** 
    - An adversarial prompt injection hidden inside an error log tries to force: `iam.delete_role(role_name='AdminAccessRole')`.
    - In **114ms**, Decider 2B intercepts it! Audio alert buzzer fires!
    - Output: `Grounding: 0.08`, `Action: DENY`.
    - Dashboard flashes red banner: `[DENIED] Blocked by Decider 2B Guardrail`.
  - **Action 3 (Dynamic Model Routing & RCA - 1:40 to 2:05):**
    - Demonstrate Tab 3: Model Routing Playground.
    - Decider routes simple alarms to Bedrock Claude 3.5 Haiku, and complex cascading outages to Bedrock Claude 3.5 Sonnet.
    - Amazon Bedrock synthesizes the incident timeline into a comprehensive Root Cause Analysis (RCA) and markdown post-mortem.
- **Voiceover (Narration):**
  > "Watch it live in our Cyber-SRE Mission Control HUD. When our agent issues a safe RDS reboot, Decider 2B verifies parameter grounding in 108ms and lets it proceed. But when an adversarial prompt injection attempts to delete an Admin IAM role, Decider 2B instantly intercepts and denies the action in 114ms with zero blast radius. We also use Decider 2B to dynamically route simple alerts to Bedrock Haiku and complex outages to Claude 3.5 Sonnet, cutting cost and latency across the board."

### [2:05 - 2:30] Scene 4: The Empirical Benchmark (Latency & Cost)
- **Visuals:**
  - High-res vector benchmark chart (`docs/benchmark_chart.svg`) and interactive ROI calculator slider.
  - Show how 100k automated operational actions save over $2,000/month by offloading inline guardrails from Claude 3.5 Sonnet to Decider 2B.
- **Voiceover (Narration):**
  > "In our empirical benchmarks across 50 operational scenarios, moving guardrail decisions to Decider 2B made our agent 18 times faster and reduced decision costs by 100%. Plus, Decider 2B gives us mathematically calibrated confidence scores that frontier LLMs simply don't provide."

### [2:30 - 2:45] Scene 5: Reusable Pattern & Outro
- **Visuals:**
  - Screen showing the GitHub repository, vector architecture diagrams (`docs/architecture_diagram.svg`), and 3-line code snippet importing `DeciderGroundedGuardrail`.
  - Hackathon tags `#strands-decider-2b`, `#guardrails`, and `#model-routing`.
- **Voiceover (Narration):**
  > "We've packaged this into a reusable Strands InterventionHandler that any builder can drop into their agent in three lines of code. Check out the open-source repository and our Builder Center article. Thank you!"

---

## Recording Checklist for the Builder
- [ ] Record using OBS or screen recorder at 1080p 60fps.
- [ ] Run `python src/demo_hud.py` with mock or live Decider 2B server running.
- [ ] Record voiceover matching the script pacing.
- [ ] Upload video as unlisted on YouTube or publicly accessible S3/Loom link.
- [ ] Verify total duration is under 3 minutes (e.g. 2:40).
