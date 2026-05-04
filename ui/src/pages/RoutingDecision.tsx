import { FormEvent, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";
import {
  presetInput,
  simulateRoutingDecision,
  type SimulationInput,
  type SimulationPreset,
} from "../lib/routingSimulator";

export default function RoutingDecision() {
  const [preset, setPreset] = useState<SimulationPreset>("rate-limit-recovery");
  const [simulation, setSimulation] = useState<SimulationInput>(
    presetInput("rate-limit-recovery"),
  );
  const [payload, setPayload] = useState(
    JSON.stringify(
      {
        model: "llama3.2:1b",
        local_only: true,
        strategy: "balanced",
        messages: [{ role: "user", content: "Decide the best route for this request." }],
      },
      null,
      2,
    ),
  );
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const simulatedDecision = simulateRoutingDecision(simulation, preset);

  async function handleRoute(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const parsed = JSON.parse(payload) as Record<string, unknown>;
      const response = await api.route(parsed);
      setResult(response as unknown as Record<string, unknown>);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Route request failed");
    }
  }

  function loadPreset(nextPreset: SimulationPreset) {
    setPreset(nextPreset);
    setSimulation(presetInput(nextPreset));
  }

  return (
    <SurfacePage
      title="Routing Decision Viewer"
      description="Inspect live route output and simulate how privacy, latency, and provider health change the fallback chain."
      kicker="Phase 20 • F-9"
      primary={
        <div style={{ display: "grid", gap: "20px" }}>
          <Panel
            title="Policy Simulation"
            subtitle="Preview route behavior before sending production traffic."
          >
            <div className="form-stack">
              <label>
                Demo scenario
                <select
                  value={preset}
                  onChange={(event) =>
                    loadPreset(event.target.value as SimulationPreset)
                  }
                >
                  <option value="rate-limit-recovery">
                    Rate-limit recovery
                  </option>
                  <option value="local-private-repair">
                    Local-only private repair
                  </option>
                  <option value="vision-fallback">
                    Vision fallback
                  </option>
                </select>
              </label>
              <label>
                Objective
                <textarea
                  rows={4}
                  value={simulation.objective}
                  onChange={(event) =>
                    setSimulation((current) => ({
                      ...current,
                      objective: event.target.value,
                    }))
                  }
                />
              </label>
              <label>
                Strategy
                <select
                  value={simulation.strategy}
                  onChange={(event) =>
                    setSimulation((current) => ({
                      ...current,
                      strategy: event.target.value as SimulationInput["strategy"],
                    }))
                  }
                >
                  <option value="balanced">Balanced</option>
                  <option value="cost">Cost</option>
                  <option value="latency">Latency</option>
                  <option value="quality">Quality</option>
                  <option value="privacy">Privacy</option>
                </select>
              </label>
              <div
                style={{
                  display: "grid",
                  gap: "10px",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                }}
              >
                <label>
                  <input
                    type="checkbox"
                    checked={simulation.localOnly}
                    onChange={(event) =>
                      setSimulation((current) => ({
                        ...current,
                        localOnly: event.target.checked,
                      }))
                    }
                  />
                  {" "}
                  Local-only
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={simulation.containsPii}
                    onChange={(event) =>
                      setSimulation((current) => ({
                        ...current,
                        containsPii: event.target.checked,
                      }))
                    }
                  />
                  {" "}
                  Contains PII
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={simulation.requiresVision}
                    onChange={(event) =>
                      setSimulation((current) => ({
                        ...current,
                        requiresVision: event.target.checked,
                      }))
                    }
                  />
                  {" "}
                  Requires vision
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={simulation.strictLatency}
                    onChange={(event) =>
                      setSimulation((current) => ({
                        ...current,
                        strictLatency: event.target.checked,
                      }))
                    }
                  />
                  {" "}
                  Strict latency SLA
                </label>
              </div>
              <label>
                Preferred provider
                <select
                  value={simulation.preferredProvider}
                  onChange={(event) =>
                    setSimulation((current) => ({
                      ...current,
                      preferredProvider: event.target.value,
                    }))
                  }
                >
                  <option value="openai">openai</option>
                  <option value="anthropic">anthropic</option>
                  <option value="gemini">gemini</option>
                  <option value="groq">groq</option>
                  <option value="ollama">ollama</option>
                </select>
              </label>
              <label>
                Degraded providers
                <select
                  multiple
                  value={simulation.degradedProviders}
                  onChange={(event) =>
                    setSimulation((current) => ({
                      ...current,
                      degradedProviders: Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                      ),
                    }))
                  }
                >
                  <option value="openai">openai</option>
                  <option value="anthropic">anthropic</option>
                  <option value="gemini">gemini</option>
                  <option value="groq">groq</option>
                  <option value="ollama">ollama</option>
                </select>
              </label>
            </div>
          </Panel>
          <Panel
            title="Route a Request"
            subtitle="Submit raw JSON to the live routing endpoint."
          >
          <form className="form-stack" onSubmit={handleRoute}>
            <textarea rows={12} value={payload} onChange={(event) => setPayload(event.target.value)} />
            <button className="primary-button" type="submit">
              Evaluate Route
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
          </Panel>
        </div>
      }
      secondary={
        <div style={{ display: "grid", gap: "20px" }}>
          <Panel
            title="Simulation Output"
            subtitle={simulatedDecision.summary}
          >
            <div className="feed-list">
              <article className="feed-item">
                <div className="feed-row">
                  <h4>
                    {simulatedDecision.selected.provider}/
                    {simulatedDecision.selected.model}
                  </h4>
                  <span className="status-pill ready">
                    score={simulatedDecision.selected.score}
                  </span>
                </div>
                <p>
                  preset={simulatedDecision.presetLabel} • local=
                  {String(simulatedDecision.selected.local)} • vision=
                  {String(simulatedDecision.selected.vision)}
                </p>
              </article>
              <article className="feed-item">
                <h4>Fallback chain</h4>
                {simulatedDecision.fallbackChain.length > 0 ? (
                  <ul className="plain-list">
                    {simulatedDecision.fallbackChain.map((candidate) => (
                      <li key={`${candidate.provider}-${candidate.model}`}>
                        {candidate.provider}/{candidate.model} (score=
                        {candidate.score})
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">No additional candidates remained.</p>
                )}
              </article>
              <article className="feed-item">
                <h4>Decision trail</h4>
                <ul className="plain-list">
                  {simulatedDecision.reasoning.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </div>
          </Panel>
          <Panel
            title="Decision Output"
            subtitle="Normalized route decision payload from the running API."
          >
            {result ? (
              <JsonBlock value={result} />
            ) : (
              <p className="muted">No live route decision computed yet.</p>
            )}
          </Panel>
        </div>
      }
    />
  );
}
