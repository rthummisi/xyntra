import { FormEvent, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";

export default function Chat() {
  const [model, setModel] = useState("llama3.2:1b");
  const [prompt, setPrompt] = useState("Reply with a short control-plane status.");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await api.chat({
        model,
        local_only: true,
        messages: [{ role: "user", content: prompt }],
      });
      setResult(response as unknown as Record<string, unknown>);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <SurfacePage
      title="Chat / Inference"
      description="Drive a unified inference request against the backend router, with a bias toward local-only execution."
      kicker="Phase 19 • F-2"
      primary={
        <Panel title="Run Inference" subtitle="This form calls the backend chat endpoint directly.">
          <form className="form-stack" onSubmit={handleSubmit}>
            <label>
              <span>Model</span>
              <input value={model} onChange={(event) => setModel(event.target.value)} />
            </label>
            <label>
              <span>Prompt</span>
              <textarea
                rows={6}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              {busy ? "Running…" : "Send Local Request"}
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
        </Panel>
      }
      secondary={
        <>
          <Panel title="Live Response" subtitle="Decision metadata and normalized provider response.">
            {result ? <JsonBlock value={result} /> : <p className="muted">No inference run yet.</p>}
          </Panel>
          <Panel title="Branching Notes" subtitle="Session branch UI depends on the session message APIs.">
            <FeedList
              items={[
                {
                  title: "Current mode",
                  body: "Direct inference requests work. Session-backed branch creation belongs in the Sessions surface.",
                },
                {
                  title: "Streaming",
                  body: "The backend exposes SSE streaming; this surface currently focuses on stable request/response execution.",
                },
              ]}
            />
          </Panel>
        </>
      }
    />
  );
}
