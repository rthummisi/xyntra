import { useEffect, useState } from "react";
import { Panel } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Artifacts() {
  const projects = useQuery(api.projects, []);
  const [projectId, setProjectId] = useState("");
  const artifacts = useQuery(
    () => (projectId ? api.artifacts(projectId) : Promise.resolve([])),
    [projectId],
  );

  useEffect(() => {
    if (!projectId && projects.data?.[0]) {
      setProjectId(projects.data[0].id);
    }
  }, [projectId, projects.data]);

  return (
    <SurfacePage
      title="Artifacts"
      description="Browse versioned artifacts and inspect saved file paths and metadata."
      kicker="Phase 22 • F-13"
      primary={
        <Panel title="Artifact Browser" subtitle="Artifacts are scoped per project.">
          <select className="select-input" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">Select project</option>
            {(projects.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <DataPanel
            title="Versions"
            loading={artifacts.status === "loading"}
            error={artifacts.error}
            data={artifacts.data}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: `${item.name} v${item.version}`,
                  body: `${item.kind} • ${item.file_path}`,
                  meta: item.id,
                }))}
              />
            )}
          />
        </Panel>
      }
      secondary={
        <Panel title="Diff & Export" subtitle="Backend export support exists; diff/export UI is next-layer enhancement.">
          <p className="muted">
            The backend supports JSON, Markdown, and ZIP export plus diff generation. This screen currently exposes the artifact inventory and storage path without a dedicated diff retrieval endpoint.
          </p>
        </Panel>
      }
    />
  );
}
