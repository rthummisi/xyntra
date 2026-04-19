import { useEffect, useState } from "react";
import { Panel, StatusPill } from "../components/Chrome";
import { DataPanel, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Tasks() {
  const projects = useQuery(api.projects, []);
  const dlq = useQuery(api.dlq, []);
  const [projectId, setProjectId] = useState("");
  const tasks = useQuery(
    () => (projectId ? api.tasks(projectId) : Promise.resolve([])),
    [projectId],
  );

  useEffect(() => {
    if (!projectId && projects.data?.[0]) {
      setProjectId(projects.data[0].id);
    }
  }, [projectId, projects.data]);

  return (
    <SurfacePage
      title="Tasks"
      description="Project task inventory, execution states, and dead-letter inspection."
      kicker="Phase 19 • F-5"
      primary={
        <Panel title="Task Inventory" subtitle="Filter tasks by project.">
          <select className="select-input" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
            <option value="">Select project</option>
            {(projects.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <DataPanel
            title="Live Tasks"
            loading={tasks.status === "loading"}
            error={tasks.error}
            data={tasks.data}
            render={(items) => (
              <SimpleTable
                columns={["Name", "Type", "Status", "Description"]}
                rows={items.map((item) => [
                  item.name,
                  item.task_type,
                  <StatusPill key={item.id} value={item.status} />,
                  item.description ?? "—",
                ])}
              />
            )}
          />
        </Panel>
      }
      secondary={
        <DataPanel
          title="Dead Letter Queue"
          subtitle="Failed task payloads that exhausted retry budget."
          loading={dlq.status === "loading"}
          error={dlq.error}
          data={dlq.data}
          render={(items) => (
            <SimpleTable
              columns={["Task", "Status", "Retries", "Last Error"]}
              rows={items.map((item) => [
                item.task_name,
                <StatusPill key={item.id} value={item.status} />,
                item.retry_count,
                item.last_error ?? "—",
              ])}
            />
          )}
        />
      }
    />
  );
}
