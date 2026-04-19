import { useEffect, useState } from "react";
import { Panel } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Sessions() {
  const projects = useQuery(api.projects, []);
  const [projectId, setProjectId] = useState("");
  const sessions = useQuery(
    () => (projectId ? api.sessions(projectId) : Promise.resolve([])),
    [projectId],
  );

  useEffect(() => {
    if (!projectId && projects.data?.[0]) {
      setProjectId(projects.data[0].id);
    }
  }, [projectId, projects.data]);

  return (
    <SurfacePage
      title="Sessions"
      description="Inspect project-scoped sessions and branch topology readiness."
      kicker="Phase 19 • F-4"
      primary={
        <Panel title="Session Explorer" subtitle="Sessions are listed per project.">
          <select className="select-input" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">Select project</option>
            {(projects.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <DataPanel
            title="Live Sessions"
            loading={sessions.status === "loading"}
            error={sessions.error}
            data={sessions.data}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: item.title,
                  body: `Parent session: ${item.parent_session_id ?? "root"}`,
                  status: item.status,
                  meta: item.id,
                }))}
              />
            )}
          />
        </Panel>
      }
      secondary={
        <Panel title="Threading & Branches" subtitle="Message retrieval endpoint is not present yet.">
          <p className="muted">
            The backend supports creating messages and branching sessions, but it does not currently expose a session message listing route. This page surfaces the branch topology boundary clearly instead of fabricating a thread view.
          </p>
        </Panel>
      }
    />
  );
}
