import { FormEvent, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";

export default function RoutingDecision() {
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

  return (
    <SurfacePage
      title="Routing Decision Viewer"
      description="Inspect classifier output, selected provider, selected model, and fallback chain."
      kicker="Phase 20 • F-9"
      primary={
        <Panel title="Route a Request" subtitle="Submit raw JSON to the routing endpoint.">
          <form className="form-stack" onSubmit={handleRoute}>
            <textarea rows={12} value={payload} onChange={(event) => setPayload(event.target.value)} />
            <button className="primary-button" type="submit">
              Evaluate Route
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
        </Panel>
      }
      secondary={
        <Panel title="Decision Output" subtitle="Normalized route decision payload.">
          {result ? <JsonBlock value={result} /> : <p className="muted">No decision computed yet.</p>}
        </Panel>
      }
    />
  );
}
