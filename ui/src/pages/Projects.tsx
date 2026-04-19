import { useEffect, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Projects() {
  const projects = useQuery(api.projects, []);
  const [selected, setSelected] = useState<string>("");
  const state = useQuery(
    () => (selected ? api.projectState(selected) : Promise.resolve(null)),
    [selected],
  );

  useEffect(() => {
    if (!selected && projects.data?.[0]) {
      setSelected(projects.data[0].id);
    }
  }, [projects.data, selected]);

  return (
    <SurfacePage
      title="Projects"
      description="List projects, inspect local-only posture, and view the persisted project state document."
      kicker="Phase 19 • F-3"
      primary={
        <DataPanel
          title="Project Registry"
          subtitle="Existing projects exposed by the backend."
          loading={projects.status === "loading"}
          error={projects.error}
          data={projects.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: item.name,
                body: item.description ?? "No description",
                status: item.local_only ? "local-only" : "mixed",
                meta: item.id,
              }))}
            />
          )}
        />
      }
      secondary={
        <>
          <Panel title="Project State Viewer" subtitle="Select a project to inspect its structured state blob.">
            <select className="select-input" value={selected} onChange={(event) => setSelected(event.target.value)}>
              <option value="">Select a project</option>
              {(projects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {state.data ? <JsonBlock value={state.data} /> : <p className="muted">No project state loaded.</p>}
          </Panel>
          <Panel title="Decisions Timeline" subtitle="Decision-specific API feed is not exposed yet.">
            <p className="muted">
              Decision records are persisted server-side, but this frontend currently has no dedicated API route for timeline retrieval.
            </p>
          </Panel>
        </>
      }
    />
  );
}
