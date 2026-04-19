import { FormEvent, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { SurfacePage } from "../components/SurfaceTemplates";
import { api } from "../lib/api";

export default function Replay() {
  const [taskRunId, setTaskRunId] = useState("");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleReplay(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const response = await api.replay(taskRunId);
      setPayload(response.payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Replay failed");
    }
  }

  return (
    <SurfacePage
      title="Trace / Replay"
      description="Replay a task run by ID and inspect the step payload returned by the backend."
      kicker="Phase 23 • F-16"
      primary={
        <Panel title="Replay Task Run" subtitle="Enter an existing task_run UUID.">
          <form className="form-stack" onSubmit={handleReplay}>
            <input value={taskRunId} onChange={(event) => setTaskRunId(event.target.value)} placeholder="task_run_id" />
            <button className="primary-button" type="submit">
              Replay
            </button>
          </form>
          {error ? <div className="error-state">{error}</div> : null}
        </Panel>
      }
      secondary={
        <Panel title="Replay Payload" subtitle="The backend currently returns a replay payload object.">
          {payload ? <JsonBlock value={payload} /> : <p className="muted">No replay loaded yet.</p>}
        </Panel>
      }
    />
  );
}
