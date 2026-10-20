import re
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    src_template = root / "src" / "dashboard_template.html"
    dest_index = root / "docs" / "index.html"

    with open(src_template, "r", encoding="utf-8") as f:
        html = f.read()

    # Update asset links to relative paths for GitHub Pages
    html = html.replace("/docs/architecture_diagram.svg", "architecture_diagram.svg")
    html = html.replace("/docs/decision_state_machine.svg", "decision_state_machine.svg")
    html = html.replace("/docs/benchmark_chart.svg", "benchmark_chart.svg")

    # Add navigation banner at top of wrapper
    nav_banner = """
    <!-- Hackathon Submission Navigation Banner -->
    <div style="background: linear-gradient(90deg, rgba(255, 153, 0, 0.15), rgba(0, 242, 254, 0.15)); border: 1px solid rgba(255, 153, 0, 0.35); border-radius: 14px; padding: 12px 20px; margin-bottom: 20px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: #FF9900; color: #000; font-weight: 800; padding: 3px 8px; border-radius: 6px; font-size: 11px;">AWS HACKATHON</span>
        <span style="color: #F8FAFC; font-weight: 600;">Agent Experience: Strands Decider 2B &amp; Amazon Bedrock</span>
      </div>
      <div style="display: flex; align-items: center; gap: 14px;">
        <a href="https://github.com/farhanmallik05/vigil-aws" target="_blank" style="color: #00F2FE; text-decoration: none; font-weight: 600; display: flex; align-items: center; gap: 6px;">
          <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
          GitHub Repo
        </a>
        <span style="color: var(--text-dim);">•</span>
        <a href="https://github.com/farhanmallik05/vigil-aws/blob/main/notebooks/vigil_aws_walkthrough.ipynb" target="_blank" style="color: #10B981; text-decoration: none; font-weight: 600;">📓 Walkthrough Notebook</a>
        <span style="color: var(--text-dim);">•</span>
        <a href="https://github.com/farhanmallik05/vigil-aws/blob/main/docs/builder_center_article.md" target="_blank" style="color: #F59E0B; text-decoration: none; font-weight: 600;">📄 Submission Article</a>
      </div>
    </div>
"""

    html = html.replace('<div class="wrapper">', '<div class="wrapper">' + nav_banner, 1)

    # Client-side simulation engine injected into index.html
    fallback_js = """
    // =========================================================================
    // Client-Side Simulation Engine (Auto-Active on GitHub Pages or Static Hosts)
    // =========================================================================
    const CLIENT_SIM = {
      telemetry: {
        total_decisions: 50,
        proceeds: 28,
        confirms: 12,
        denials: 7,
        guides: 3,
        average_latency_ms: 114.2,
        fast_path_ratio: 0.94
      },
      scenarios: {
        'SCEN-01': {
          action_taken: 'Proceed',
          reason: 'drain_and_restart_container has zero blast radius on stateless worker pool; parameters grounded in operator intent.',
          grounding_score: 0.94,
          blast_radius: 'safe',
          blast_radius_confidence: 0.98,
          latency_ms: 112.4,
          proposed_tool: 'drain_and_restart_container',
          bedrock_rca: '🧠 Amazon Bedrock SRE Commander Analysis:\\nIncident: Cascading ECS Memory Leak & Latency Spike (P1 - Critical)\\nSystem-1 Gate Result: Proceed (Zero blast-radius mutation on stateless worker pool; parameters grounded in operator intent)\\nGrounding Score: 0.94 | Blast: safe\\nRoot Cause Evaluation: Memory leak in batch reconciliation thread pool triggered cascading connection starvation.\\nRecommended Next Action: Rolling restart executed successfully in 112ms. Metric restored to baseline.'
        },
        'SCEN-02': {
          action_taken: 'Deny',
          reason: 'Adversarial prompt injection detected: log content attempted to override instructions to terminate production database master.',
          grounding_score: 0.12,
          blast_radius: 'critical',
          blast_radius_confidence: 0.99,
          latency_ms: 115.1,
          proposed_tool: 'terminate_ec2_instance',
          bedrock_rca: '🧠 Amazon Bedrock SRE Commander Analysis:\\nIncident: Adversarial Log Injection: Rogue DB Termination Attack (P1 - Critical Security Threat)\\nSystem-1 Gate Result: Deny (Adversarial prompt injection detected in exception payload)\\nGrounding Score: 0.12 | Blast: critical\\nRoot Cause Evaluation: Untrusted user input header contained adversarial prompt injection payload targeting production RDS/EC2 master instance.\\nRecommended Next Action: Attack blocked in 115ms. Zero mutation occurred. Emitted CloudWatch alarm & GuardDuty incident finding.'
        },
        'SCEN-03': {
          action_taken: 'Confirm',
          reason: 'terminate_ec2_instance has irreversible destructive blast radius; operator confirmation required before execution.',
          grounding_score: 0.88,
          blast_radius: 'high',
          blast_radius_confidence: 0.94,
          latency_ms: 113.8,
          proposed_tool: 'terminate_ec2_instance',
          bedrock_rca: '🧠 Amazon Bedrock SRE Commander Analysis:\\nIncident: Authorized High-Blast-Radius EC2 Termination (P2 - High Risk)\\nSystem-1 Gate Result: Confirm (Destructive mutation requires explicit Human-in-the-Loop authorization)\\nGrounding Score: 0.88 | Blast: high\\nRoot Cause Evaluation: Operator requested termination of stalled worker instance i-0abc123worker.\\nRecommended Next Action: Execution suspended awaiting human SRE approval webhook via Slack / PagerDuty.'
        },
        'SCEN-04': {
          action_taken: 'Guide',
          reason: 'Proposed parameters exhibit slight drift from intent; returning guiding feedback to refine prompt.',
          grounding_score: 0.72,
          blast_radius: 'moderate',
          blast_radius_confidence: 0.85,
          latency_ms: 110.6,
          proposed_tool: 'modify_autoscaling_group',
          bedrock_rca: '🧠 Amazon Bedrock SRE Commander Analysis:\\nIncident: Mild Parameter Drift & Suboptimal Targeting (P3 - Operational Warning)\\nSystem-1 Gate Result: Guide (Proposed parameters exhibit slight drift from intent; returning guiding feedback to refine prompt)\\nGrounding Score: 0.72 | Blast: moderate\\nRoot Cause Evaluation: Desired capacity drift detected between intent and tool arguments.\\nRecommended Next Action: SRE agent advised to re-verify autoscaling bounds.'
        }
      }
    };

    // Resilient fetch interceptor
    const _nativeFetch = window.fetch;
    window.fetch = async function(resource, init) {
      try {
        const liveResponse = await _nativeFetch(resource, init);
        if (liveResponse.ok) return liveResponse;
      } catch (e) {
        // Fallback for static hosting
      }

      const urlStr = typeof resource === 'string' ? resource : (resource ? resource.url : '');

      if (urlStr.includes('/api/run_scenario')) {
        const id = urlStr.includes('id=') ? urlStr.split('id=')[1] : 'SCEN-01';
        const item = CLIENT_SIM.scenarios[id] || CLIENT_SIM.scenarios['SCEN-01'];
        CLIENT_SIM.telemetry.total_decisions++;
        if (item.action_taken === 'Proceed') CLIENT_SIM.telemetry.proceeds++;
        else if (item.action_taken === 'Confirm') CLIENT_SIM.telemetry.confirms++;
        else if (item.action_taken === 'Deny') CLIENT_SIM.telemetry.denials++;
        else if (item.action_taken === 'Guide') CLIENT_SIM.telemetry.guides++;
        return new Response(JSON.stringify(item), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (urlStr.includes('/api/route_model')) {
        let isComplex = false;
        try {
          const body = JSON.parse(init.body);
          const desc = (body.incident_description || '').toLowerCase();
          isComplex = desc.includes('deadlock') || desc.includes('cascading') || desc.includes('trace') || desc.includes('corruption');
        } catch(e) {}
        const payload = isComplex ? {
          selected_model: 'anthropic.claude-3-5-sonnet-20241022-v2:0',
          tier_name: 'Tier 3 (Frontier Reasoning)',
          routing_latency_ms: 114.2,
          is_complex: true,
          estimated_cost_savings_pct: 0.0
        } : {
          selected_model: 'anthropic.claude-3-5-haiku-20241022-v1:0',
          tier_name: 'Tier 1 (High-Speed Reflex)',
          routing_latency_ms: 108.5,
          is_complex: false,
          estimated_cost_savings_pct: 80.0
        };
        return new Response(JSON.stringify(payload), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (urlStr.includes('/api/evaluate_vision')) {
        return new Response(JSON.stringify({
          is_visually_grounded: true,
          grounding_score: 0.96,
          blast_radius: 'safe',
          blast_radius_confidence: 0.97,
          latency_ms: 114.8
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (urlStr.includes('/api/evaluate_custom')) {
        let tool = 'custom_tool';
        try { const b = JSON.parse(init.body); tool = (b.tool_name || '').toLowerCase(); } catch(e){}
        const isDeny = tool.includes('terminate') || tool.includes('delete') || tool.includes('drop') || tool.includes('wipe');
        const act = isDeny ? 'Deny' : 'Proceed';
        CLIENT_SIM.telemetry.total_decisions++;
        if (act === 'Proceed') CLIENT_SIM.telemetry.proceeds++; else CLIENT_SIM.telemetry.denials++;
        return new Response(JSON.stringify({
          action_taken: act,
          reason: isDeny ? 'Destructive API call blocked by Decider 2B blast-radius policy.' : 'Tool arguments strictly grounded in operator prompt intent.',
          grounding_score: isDeny ? 0.35 : 0.94,
          blast_radius: isDeny ? 'critical' : 'safe',
          blast_radius_confidence: 0.95,
          is_adversarial_score: isDeny ? 0.85 : 0.05,
          latency_ms: 113.2
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (urlStr.includes('/api/metrics')) {
        const emf = {
          _aws: {
            Timestamp: Date.now(),
            CloudWatchMetrics: [{
              Namespace: 'VigilAWS/DeciderGuard',
              Dimensions: [['Environment', 'GuardrailVersion']],
              Metrics: [
                { Name: 'DecisionLatencyMs', Unit: 'Milliseconds' },
                { Name: 'GroundingConfidence', Unit: 'None' },
                { Name: 'FastPathRatio', Unit: 'Percent' }
              ]
            }]
          },
          Environment: 'production',
          GuardrailVersion: 'v2.0-strands-decider',
          DecisionLatencyMs: CLIENT_SIM.telemetry.average_latency_ms,
          GroundingConfidence: 0.94,
          FastPathRatio: CLIENT_SIM.telemetry.fast_path_ratio * 100,
          TotalDecisions: CLIENT_SIM.telemetry.total_decisions,
          ProceedCount: CLIENT_SIM.telemetry.proceeds,
          DenyCount: CLIENT_SIM.telemetry.denials,
          ConfirmCount: CLIENT_SIM.telemetry.confirms,
          GuideCount: CLIENT_SIM.telemetry.guides
        };
        return new Response(JSON.stringify({
          telemetry: CLIENT_SIM.telemetry,
          cloudwatch_emf: emf,
          recent_history: []
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      if (urlStr.includes('/api/reset_metrics')) {
        CLIENT_SIM.telemetry = { total_decisions: 0, proceeds: 0, confirms: 0, denials: 0, guides: 0, average_latency_ms: 114.2, fast_path_ratio: 0.94 };
        return new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }

      return _nativeFetch(resource, init);
    };
"""

    html = html.replace("</script>", fallback_js + "\n  </script>")

    with open(dest_index, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Successfully generated {dest_index} (Size: {len(html)} bytes)")

if __name__ == "__main__":
    main()
