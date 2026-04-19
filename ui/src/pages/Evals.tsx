import { FormEvent, useState } from "react";
import { Panel } from "../components/Chrome";
import { FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";

export default function Evals() {
  const [models, setModels] = useState("ollama:llama3.2:1b,openai:gpt-4o-mini");
  const [prompt, setPrompt] = useState("Evaluate which model gives the clearest answer.");
  const [results, setResults] = useState<Array<{ title: string; body: string; meta: string }>>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleEval(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const response = await api.evals({
        models: models.split(",").map((item) => item.trim()).filter(Boolean),
        messages: [{ role: "user", content: prompt }],
      });
      setResults(
        (response.results as Array<Record<string, unknown>>).map((item) => ({
          title: String(item.model),
          body: String(item.reasoning),
          meta: `score=${String(item.score)}`,
        })),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Eval failed");
    }
  }

  return (
    <SurfacePage
      title="Eval Harness"
      description="Run lightweight model evaluation against a shared prompt and inspect scored results."
      kicker="Phase 24 • F-22"
      primary={
        <Panel title="Run Eval" subtitle="Submit a prompt across multiple models.">
          <form className="form-stack" onSubmit={handleEval}>
            <input value={models} onChange={(event) => setModels(event.target.value)} />
            <textarea rows={5} value={prompt} onChange={(event) => setPrompt(event.target.value)} />
            <button className="primary-button" type="submit">
              Evaluate
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
        </Panel>
      }
      secondary={
        <Panel title="Scores" subtitle="Returned eval results sorted by score.">
          <FeedList items={results} />
        </Panel>
      }
    />
  );
}
