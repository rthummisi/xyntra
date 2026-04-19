import { FormEvent, useState } from "react";
import { Panel } from "../components/Chrome";
import { FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";

export default function Compare() {
  const [models, setModels] = useState("ollama:llama3.2:1b,openai:gpt-4o-mini");
  const [prompt, setPrompt] = useState("Summarize the role of Xyntra in one sentence.");
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState<Array<{ title: string; body: string; meta: string }>>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await api.compare({
        models: models.split(",").map((item) => item.trim()).filter(Boolean),
        messages: [{ role: "user", content: prompt }],
      });
      setResults(
        response.results.map((item) => ({
          title: `${item.provider}:${item.model}`,
          body: item.response.content,
          meta: `finish=${item.response.finish_reason ?? "unknown"}`,
        })),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Compare request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <SurfacePage
      title="Output Comparison"
      description="Run the same prompt against multiple models and inspect normalized responses side by side."
      kicker="Phase 20 • F-7"
      primary={
        <Panel title="Compare Models" subtitle="Use provider:model values separated by commas.">
          <form className="form-stack" onSubmit={handleCompare}>
            <label>
              <span>Models</span>
              <input value={models} onChange={(event) => setModels(event.target.value)} />
            </label>
            <label>
              <span>Prompt</span>
              <textarea rows={5} value={prompt} onChange={(event) => setPrompt(event.target.value)} />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              {busy ? "Comparing…" : "Run Comparison"}
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
        </Panel>
      }
      secondary={
        <Panel title="Responses" subtitle="Each card represents one provider/model result.">
          <FeedList items={results} />
        </Panel>
      }
    />
  );
}
