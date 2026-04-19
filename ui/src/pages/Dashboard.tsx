import { useMemo } from "react";
import { Panel, StatusPill } from "../components/Chrome";
import { DataPanel, FeedList, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Dashboard() {
  const providers = useQuery(api.providers, []);
  const health = useQuery(api.providerHealth, []);
  const spend = useQuery(api.spendDashboard, []);
  const events = useQuery(() => api.events(""), []);
  const providerCount = providers.data?.length ?? 0;
  const healthyCount = health.data?.filter((item) => item.status === "healthy").length ?? 0;
  const spendUsd = Number(spend.data?.summary?.cost_usd ?? 0).toFixed(2);
  const eventCount = events.data?.length ?? 0;
  const healthRows = useMemo(
    () =>
      (health.data ?? []).map((item) => [
        item.provider,
        <StatusPill key={`${item.provider}-status`} value={item.status} />,
        String(item.details.circuit_failures ?? 0),
      ]),
    [health.data],
  );

  return (
    <SurfacePage
      title="System Dashboard"
      description="Live overview of providers, spend posture, event traffic, and the local execution fabric."
      kicker="Phase 19 • F-1"
      metrics={[
        { label: "Providers", value: providerCount, detail: "Registry coverage" },
        { label: "Healthy", value: healthyCount, detail: "Circuit-open providers excluded" },
        { label: "Spend USD", value: spendUsd, detail: "Dashboard summary" },
        { label: "Events", value: eventCount, detail: "Persisted event log records" },
      ]}
      primary={
        <>
          <DataPanel
            title="Provider Health"
            subtitle="Live provider status, including circuit-breaker state."
            loading={health.status === "loading"}
            error={health.error}
            data={health.data}
            render={() => (
              <SimpleTable columns={["Provider", "Status", "Circuit Failures"]} rows={healthRows} />
            )}
          />
          <Panel title="Spend Summary" subtitle="Aggregated cost and usage grouping from the analytics dashboard.">
            <pre className="json-block">{JSON.stringify(spend.data?.summary ?? {}, null, 2)}</pre>
          </Panel>
        </>
      }
      secondary={
        <>
          <DataPanel
            title="Recent Event Feed"
            subtitle="Latest persisted webhook and task events."
            loading={events.status === "loading"}
            error={events.error}
            data={events.data?.slice(0, 6) ?? null}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: item.event_type,
                  body: JSON.stringify(item.payload),
                  status: item.delivery_status,
                  meta: item.id,
                }))}
              />
            )}
          />
          <DataPanel
            title="Provider Registry"
            subtitle="Configured providers and advertised model counts."
            loading={providers.status === "loading"}
            error={providers.error}
            data={providers.data}
            render={(items) => (
              <FeedList
                items={items.map((item) => ({
                  title: item.provider,
                  body: `${item.models.length} models exposed`,
                  status: item.local_only ? "local-only" : "hosted",
                  meta: item.models.slice(0, 3).join(", "),
                }))}
              />
            )}
          />
        </>
      }
    />
  );
}
