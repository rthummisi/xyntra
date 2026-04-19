import type { RouteItem } from "./types";

export const routes: RouteItem[] = [
  { path: "/", label: "Dashboard", section: "Core", summary: "System overview and live status." },
  { path: "/chat", label: "Chat", section: "Core", summary: "Inference, streaming, and branching." },
  { path: "/projects", label: "Projects", section: "Core", summary: "Projects, state, and decisions." },
  { path: "/sessions", label: "Sessions", section: "Core", summary: "Session trees and messages." },
  { path: "/tasks", label: "Tasks", section: "Core", summary: "Task lifecycle and DLQ inspection." },
  { path: "/leaderboard", label: "Leaderboard", section: "Models", summary: "Capability, quality, and price matrix." },
  { path: "/compare", label: "Compare", section: "Models", summary: "Parallel output comparison." },
  { path: "/provider-health", label: "Provider Health", section: "Models", summary: "Circuit and health telemetry." },
  { path: "/routing-decision", label: "Routing Decision", section: "Models", summary: "Classifier and fallback chain viewer." },
  { path: "/memory", label: "Memory", section: "Memory", summary: "Session, project, and preference memory." },
  { path: "/context-inspector", label: "Context Inspector", section: "Memory", summary: "Assembled context and token budget." },
  { path: "/semantic-cache", label: "Semantic Cache", section: "Memory", summary: "Cache hit, miss, and similarity records." },
  { path: "/artifacts", label: "Artifacts", section: "Assets", summary: "Versioned artifacts and exports." },
  { path: "/prompt-templates", label: "Prompt Templates", section: "Assets", summary: "Registry, diff, and rollback." },
  { path: "/spend-analytics", label: "Spend Analytics", section: "Observability", summary: "Cost, quota, and usage trends." },
  { path: "/replay", label: "Replay", section: "Observability", summary: "Replay past task runs." },
  { path: "/event-log", label: "Event Log", section: "Observability", summary: "Webhook event stream and delivery state." },
  { path: "/policies", label: "Policies", section: "Security", summary: "PII, privacy, approval, and budget policy posture." },
  { path: "/approvals", label: "Approvals", section: "Security", summary: "Pending approvals and audit posture." },
  { path: "/api-keys", label: "API Keys", section: "Security", summary: "Key rotation and expiry posture." },
  { path: "/webhooks", label: "Webhooks", section: "Admin", summary: "Webhook subscriptions and delivery." },
  { path: "/evals", label: "Evals", section: "Admin", summary: "Prompt and model evaluation harness." },
  { path: "/settings", label: "Settings", section: "Admin", summary: "Provider and local runtime defaults." },
];

export const routeGroups = routes.reduce<Record<string, RouteItem[]>>((acc, route) => {
  acc[route.section] ??= [];
  acc[route.section].push(route);
  return acc;
}, {});
