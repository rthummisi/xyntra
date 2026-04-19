import { useEffect, useState } from "react";
import { JsonBlock, Panel } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Memory() {
  const projects = useQuery(api.projects, []);
  const [projectId, setProjectId] = useState("");
  const sessions = useQuery(
    () => (projectId ? api.sessions(projectId) : Promise.resolve([])),
    [projectId],
  );
  const [sessionId, setSessionId] = useState("");

  useEffect(() => {
    if (!projectId && projects.data?.[0]) {
      setProjectId(projects.data[0].id);
    }
  }, [projectId, projects.data]);

  useEffect(() => {
    if (!sessionId && sessions.data?.[0]) {
      setSessionId(sessions.data[0].id);
    }
  }, [sessionId, sessions.data]);

  const selectedSession = sessions.data?.find((item) => item.id === sessionId) ?? null;
  const snapshot = useQuery(
    () =>
      projectId && selectedSession
        ? api.memorySnapshot(sessionId, projectId, selectedSession.user_id)
        : Promise.resolve(null),
    [projectId, selectedSession, sessionId],
  );

  return (
    <SurfacePage
      title="Memory Viewer"
      description="Session messages, summaries, project state, decisions, and user preference memory."
      kicker="Phase 21 • F-10"
      primary={
        <Panel title="Scope Selector" subtitle="Memory snapshots are scoped by project, session, and user.">
          <div className="form-stack">
            <select className="select-input" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
              <option value="">Select project</option>
              {(projects.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            <select className="select-input" value={sessionId} onChange={(event) => setSessionId(event.target.value)}>
              <option value="">Select session</option>
              {(sessions.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>
          </div>
          <DataPanel
            title="Session Messages"
            loading={snapshot.status === "loading"}
            error={snapshot.error}
            data={snapshot.data?.session_messages ?? null}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: String(item.role ?? "message"),
                  body: String(item.content ?? ""),
                  meta: `seq ${String(item.sequence_number ?? "—")}`,
                }))}
              />
            )}
          />
        </Panel>
      }
      secondary={
        <>
          <Panel title="Summaries & Preferences" subtitle="Compacted session memory and preference templates.">
            <JsonBlock
              value={{
                session_summaries: snapshot.data?.session_summaries ?? [],
                user_preferences: snapshot.data?.user_preferences ?? [],
                project_decisions: snapshot.data?.project_decisions ?? [],
              }}
            />
          </Panel>
          <Panel title="Project State" subtitle="Structured project memory state.">
            <JsonBlock value={snapshot.data?.project_state ?? {}} />
          </Panel>
        </>
      }
    />
  );
}
