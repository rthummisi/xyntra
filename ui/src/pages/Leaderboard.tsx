import { DataPanel, SimpleTable, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Leaderboard() {
  const leaderboard = useQuery(api.leaderboard, []);

  return (
    <SurfacePage
      title="Model Leaderboard"
      description="Sortable model capability matrix sourced from the provider capability registry."
      kicker="Phase 20 • F-6"
      primary={
        <DataPanel
          title="Capability Matrix"
          subtitle="Provider, quality, cost, latency, and context window."
          loading={leaderboard.status === "loading"}
          error={leaderboard.error}
          data={leaderboard.data}
          render={(items) => (
            <SimpleTable
              columns={["Provider", "Model", "Quality", "Cost", "Latency", "Context", "Local"]}
              rows={items.map((item) => [
                item.provider,
                item.model,
                item.quality_tier,
                item.cost_tier,
                item.latency_tier,
                item.context_window.toLocaleString(),
                item.local_only ? "Yes" : "No",
              ])}
            />
          )}
        />
      }
    />
  );
}
