import { useEffect, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function ContextInspector() {
  const projects = useQuery(api.projects, []);
  const [projectId, setProjectId] = useState("");
  const [modelName, setModelName] = useState("llama3.2:1b");

  useEffect(() => {
    if (!projectId && projects.data?.[0]) {
      setProjectId(projects.data[0].id);
    }
  }, [projectId, projects.data]);

  const inspection = useQuery(
    () => (projectId ? api.contextInspection(projectId, modelName) : Promise.resolve(null)),
    [projectId, modelName],
  );

  return (
    <SurfacePage
      title="Context Assembly Inspector"
      description="Retrieved context chunks and token budget breakdown for a project."
      kicker="Phase 21 • F-11"
      primary={
        <Panel title="Inspection Controls" subtitle="Project-scoped retrieval with model-aware token window.">
          <div className="form-stack">
            <select className="select-input" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">Select project</option>
              {(projects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <input value={modelName} onChange={(event) => setModelName(event.target.value)} />
          </div>
          <DataPanel
            title="Retrieved Chunks"
            loading={inspection.status === "loading"}
            error={inspection.error}
            data={inspection.data?.assembled.chunks ?? null}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: item.source,
                  body: item.content,
                  meta: `score ${item.score}`,
                }))}
              />
            )}
          />
        </Panel>
      }
      secondary={
        <Panel title="Budget Breakdown" subtitle="Reserved output and available context window.">
          <JsonBlock value={inspection.data?.assembled.budget ?? {}} />
        </Panel>
      }
    />
  );
}
