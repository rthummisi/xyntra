import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function Webhooks() {
  const webhooks = useQuery(api.webhooks, []);

  return (
    <SurfacePage
      title="Webhook Manager"
      description="Subscription registry and delivery target overview."
      kicker="Phase 24 • F-21"
      primary={
        <DataPanel
          title="Subscriptions"
          subtitle="Registered webhook subscriptions."
          loading={webhooks.status === "loading"}
          error={webhooks.error}
          data={webhooks.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: item.target_url,
                body: item.event_types.join(", "),
                status: item.is_active ? "active" : "inactive",
                meta: item.project_id ?? "global",
              }))}
            />
          )}
        />
      }
    />
  );
}
