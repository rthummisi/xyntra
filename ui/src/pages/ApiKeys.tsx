import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function ApiKeys() {
  const keys = useQuery(api.apiKeys, []);

  return (
    <SurfacePage
      title="API Key Manager"
      description="Persistent API-key inventory with expiry and revocation status."
      kicker="Phase 24 • F-20"
      primary={
        <DataPanel
          title="API Keys"
          subtitle="Stored key metadata; raw secrets are only returned at creation and rotation time."
          loading={keys.status === "loading"}
          error={keys.error}
          data={keys.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: item.name,
                body: `preview ${item.token_preview} • expires ${item.expires_at}`,
                status: item.revoked_at ? "revoked" : item.expired ? "expired" : "active",
                meta: item.key_id,
              }))}
            />
          )}
        />
      }
    />
  );
}
