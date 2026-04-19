import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Approvals() {
  const approvals = useQuery(api.approvals, []);

  return (
    <SurfacePage
      title="Approvals Queue"
      description="Pending and resolved approval records from the backend."
      kicker="Phase 24 • F-19"
      primary={
        <DataPanel
          title="Approval Records"
          subtitle="Operational approval state and approver identity."
          loading={approvals.status === "loading"}
          error={approvals.error}
          data={approvals.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: item.reason ?? "Approval",
                body: `Task: ${item.task_id ?? "none"}`,
                status: item.status,
                meta: item.approver_identifier ?? "unassigned",
              }))}
            />
          )}
        />
      }
    />
  );
}
