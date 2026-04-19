import { Panel } from "../components/Chrome";
import { DataPanel, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function SpendAnalytics() {
  const dashboard = useQuery(api.spendDashboard, []);

  return (
    <SurfacePage
      title="Spend Analytics"
      description="Cost and usage trends sourced from the spend dashboard endpoint."
      kicker="Phase 23 • F-15"
      metrics={[
        {
          label: "Total Cost",
          value: Number(dashboard.data?.summary?.cost_usd ?? 0).toFixed(2),
          detail: "USD",
        },
        {
          label: "Input Tokens",
          value: Number(dashboard.data?.summary?.input_tokens ?? 0).toLocaleString(),
        },
        {
          label: "Output Tokens",
          value: Number(dashboard.data?.summary?.output_tokens ?? 0).toLocaleString(),
        },
      ]}
      primary={
        <DataPanel
          title="Spend by Project"
          subtitle="Grouped analytics rollup by project."
          loading={dashboard.status === "loading"}
          error={dashboard.error}
          data={dashboard.data?.by_project ?? null}
          render={(items) => (
            <SimpleTable
              columns={Object.keys(items[0] ?? { project_id: "", cost_usd: "" })}
              rows={items.map((item) => Object.values(item))}
            />
          )}
        />
      }
      secondary={
        <Panel title="Model & Date Breakdown" subtitle="Raw dashboard payload for deeper inspection.">
          <pre className="json-block">{JSON.stringify(dashboard.data ?? {}, null, 2)}</pre>
        </Panel>
      }
    />
  );
}
