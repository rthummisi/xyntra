import { DataPanel, FeedList, SurfacePage } from "../components/SurfaceTemplates";
import { api, useQuery } from "../lib/api";

export default function PromptTemplates() {
  const prompts = useQuery(api.prompts, []);

  return (
    <SurfacePage
      title="Prompt Template Registry"
      description="Template versions, tags, and registry state from the prompt API."
      kicker="Phase 22 • F-14"
      primary={
        <DataPanel
          title="Templates"
          subtitle="Latest prompt template records."
          loading={prompts.status === "loading"}
          error={prompts.error}
          data={prompts.data}
          render={(items) => (
            <FeedList
              items={items.map((item) => ({
                title: `${item.name} v${item.version}`,
                body: item.content,
                meta: item.tags.join(", ") || "untagged",
              }))}
            />
          )}
        />
      }
    />
  );
}
