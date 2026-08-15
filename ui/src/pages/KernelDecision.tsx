import { useState } from "react";
import { api } from "../lib/api";
import { MetricCard, Panel, PageHeader, StatusPill } from "../components/Chrome";

const COMPLEXITY_COLOR: Record<string, string> = {
  trivial: "#22d3ee",
  moderate: "#5ec4aa",
  complex: "#e8b84b",
  extreme: "#f43f5e",
};

const COMPUTE_COLOR: Record<string, string> = {
  api: "#7c9ef8",
  local_gpu: "#5ec4aa",
  local_cpu: "#94a3b8",
  hybrid: "#e8b84b",
};

export default function KernelDecision() {
  const [input, setInput] = useState("");
  const [localOnly, setLocalOnly] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function decide() {
    if (!input.trim()) return;
    setRunning(true);
    setError(null);
    try {
      const res = await api.kernelDecide({
        messages: [{ role: "user", content: input }],
        local_only: localOnly,
      }) as Record<string, unknown>;
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kernel error");
    } finally {
      setRunning(false);
    }
  }

  const cls = result?.classification as Record<string, unknown> | null;
  const sel = result?.selection as Record<string, unknown> | null;
  const hw = result?.hardware as Record<string, unknown> | null;

  return (
    <div className="surface-page">
      <PageHeader
        title="Kernel Decisions"
        kicker="OS KERNEL · CLASSIFY"
        description="Submit any prompt and see exactly how the kernel classifies it: complexity, sensitivity, compute target, and model selection."
      />

      <Panel title="Task Input">
        <div className="kernel-form">
          <label className="field-label">PROMPT TO CLASSIFY</label>
          <textarea
            className="mission-input"
            placeholder="Paste any prompt or task description…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={5}
          />
          <div className="kernel-options">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={localOnly}
                onChange={(e) => setLocalOnly(e.target.checked)}
              />
              <span>LOCAL ONLY (force local GPU routing)</span>
            </label>
          </div>
          {error && <p className="error-inline">{error}</p>}
          <button className="launch-btn" onClick={decide} disabled={running || !input.trim()}>
            {running ? "CLASSIFYING…" : "RUN KERNEL"}
          </button>
        </div>
      </Panel>

      {result && cls && sel && (
        <>
          <div className="metrics-row">
            <MetricCard
              label="COMPLEXITY"
              value={String(cls.complexity ?? "").toUpperCase()}
              detail="Task complexity tier"
              alert={cls.complexity === "extreme"}
            />
            <MetricCard
              label="SENSITIVITY"
              value={String(cls.sensitivity ?? "").toUpperCase()}
              detail="Data sensitivity class"
            />
            <MetricCard
              label="COMPUTE"
              value={String(cls.compute_target ?? "").replace("_", " ").toUpperCase()}
              detail="Where this runs"
            />
            <MetricCard
              label="EST TOKENS"
              value={String(cls.estimated_tokens ?? 0)}
              detail="Input token estimate"
            />
            <MetricCard
              label="MULTI-AGENT"
              value={cls.multi_agent_recommended ? "YES" : "NO"}
              detail="Parallel fleet recommended"
              live={Boolean(cls.multi_agent_recommended)}
            />
          </div>

          <div className="kernel-result-grid">
            <Panel title="Classification" subtitle="Kernel reasoning trace.">
              <div className="kernel-trace">
                <div className="trace-row">
                  <span className="trace-key">TASK TYPE</span>
                  <StatusPill value={String(cls.task_type ?? "")} />
                </div>
                <div className="trace-row">
                  <span className="trace-key">COMPLEXITY</span>
                  <span className="trace-val" style={{ color: COMPLEXITY_COLOR[String(cls.complexity)] }}>
                    {String(cls.complexity).toUpperCase()}
                  </span>
                </div>
                <div className="trace-row">
                  <span className="trace-key">COMPUTE TARGET</span>
                  <span className="trace-val" style={{ color: COMPUTE_COLOR[String(cls.compute_target)] }}>
                    {String(cls.compute_target).replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <div className="trace-row">
                  <span className="trace-key">STRATEGY</span>
                  <span className="trace-val mono">{String(cls.preferred_strategy)}</span>
                </div>
                <div className="trace-row">
                  <span className="trace-key">MULTIMODAL</span>
                  <span className="trace-val">{cls.requires_multimodal ? "YES" : "NO"}</span>
                </div>
                <div className="trace-row">
                  <span className="trace-key">TOOLS REQUIRED</span>
                  <span className="trace-val">{cls.requires_tools ? "YES" : "NO"}</span>
                </div>
                {(cls.agent_roles_suggested as string[])?.length > 0 && (
                  <div className="trace-row">
                    <span className="trace-key">SUGGESTED ROLES</span>
                    <span className="trace-val mono">
                      {(cls.agent_roles_suggested as string[]).join(", ")}
                    </span>
                  </div>
                )}
                <div className="trace-reasoning mono">{String(cls.reasoning)}</div>
              </div>
            </Panel>

            <Panel title="Model Selection" subtitle="Recommended provider, model, and quantization.">
              <div className="selection-block">
                <div className="selection-primary">
                  <span className="sel-provider mono">{String(sel.provider)}</span>
                  <span className="sel-slash">/</span>
                  <span className="sel-model mono">{String(sel.model)}</span>
                  <StatusPill value={String(sel.quantization)} />
                </div>
                <p className="sel-rationale mono">{String(sel.rationale)}</p>
                {(sel.fallback_chain as Array<[string, string]>)?.length > 0 && (
                  <div className="sel-fallbacks">
                    <span className="trace-key">FALLBACK CHAIN</span>
                    <div className="fallback-list">
                      {(sel.fallback_chain as Array<[string, string]>).map(([p, m], i) => (
                        <span key={i} className="fallback-item mono">{p}/{m}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {hw && (
                <div className="hw-summary">
                  <span className="trace-key">HARDWARE</span>
                  <span className="mono">
                    {hw.gpu_count as number} GPU · {(hw.free_vram_gb as number).toFixed(1)}GB free ·
                    {hw.has_cuda ? " CUDA" : hw.has_mps ? " MPS" : " CPU only"}
                  </span>
                </div>
              )}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
