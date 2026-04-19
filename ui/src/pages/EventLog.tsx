import { StatusPill } from "../components/Chrome";
import { DataPanel, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function EventLog() {
  const events = useQuery(() => api.events(""), []);

  return (
    <SurfacePage
      title="Event Log"
      description="Persisted webhook and system event records with delivery state."
      kicker="Phase 23 • F-17"
      primary={
        <DataPanel
          title="Event Stream"
          subtitle="Latest events persisted by the event bus."
          loading={events.status === "loading"}
          error={events.error}
          data={events.data}
          render={(items) => (
            <SimpleTable
              columns={["Type", "Delivery", "Attempts", "Event ID"]}
              rows={items.map((item) => [
                item.event_type,
                <StatusPill key={item.id} value={item.delivery_status} />,
                item.attempt_count,
                item.id,
              ])}
            />
          )}
        />
      }
    />
  );
}
