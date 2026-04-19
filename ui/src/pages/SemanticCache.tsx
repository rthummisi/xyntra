import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function SemanticCache() {
  const cache = useQuery(api.semanticCache, []);

  return (
    <SurfacePage
      title="Semantic Cache Browser"
      description="Live Redis-backed semantic cache entries exposed by the backend."
      kicker="Phase 21 • F-12"
      primary={
        <DataPanel
          title="Cache Entries"
          subtitle="Current semantic cache records."
          loading={cache.status === "loading"}
          error={cache.error}
          data={cache.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: item.key,
                body: item.response ?? "",
                status: item.local_only ? "local-only" : "shared",
              }))}
            />
          )}
        />
      }
    />
  );
}
