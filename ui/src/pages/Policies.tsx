import { JsonBlock } from "../components/Chrome";
import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Policies() {
  const rules = useQuery(api.policyRules, []);

  return (
    <SurfacePage
      title="Policy Configuration"
      description="Policy rule registry exposed by the backend."
      kicker="Phase 24 • F-18"
      primary={
        <DataPanel
          title="Policy Rules"
          subtitle="Persisted rule configuration records."
          loading={rules.status === "loading"}
          error={rules.error}
          data={rules.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: `${item.rule_type} • ${item.name}`,
                body: JSON.stringify(item.config),
                status: item.enabled ? "active" : "disabled",
                meta: item.project_id ?? "global",
              }))}
            />
          )}
        />
      }
      secondary={<JsonBlock value={rules.data ?? []} />}
    />
  );
}
