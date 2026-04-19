import { StatusPill } from "../components/Chrome";
import { DataPanel, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function ProviderHealth() {
  const health = useQuery(api.providerHealth, []);

  return (
    <SurfacePage
      title="Provider Health"
      description="Provider availability, health status, and circuit-breaker details."
      kicker="Phase 20 • F-8"
      primary={
        <DataPanel
          title="Health Matrix"
          subtitle="Pulled from live provider health checks."
          loading={health.status === "loading"}
          error={health.error}
          data={health.data}
          render={(items) => (
            <SimpleTable
              columns={["Provider", "Status", "Circuit Healthy", "Failures"]}
              rows={items.map((item) => [
                item.provider,
                <StatusPill key={item.provider} value={item.status} />,
                String(item.details.circuit_healthy ?? "—"),
                String(item.details.circuit_failures ?? 0),
              ])}
            />
          )}
        />
      }
    />
  );
}
