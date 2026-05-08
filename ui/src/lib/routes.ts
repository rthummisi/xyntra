import type { RouteItem } from "./types";

export const APP_PREFIX = "/app";

export const routes: RouteItem[] = [
  {
    path: `${APP_PREFIX}`,
    label: "Dashboard",
    section: "Core",
    summary: "System overview and live status.",
  },
  {
    path: `${APP_PREFIX}/chat`,
    label: "Chat",
    section: "Core",
    summary: "Inference, streaming, and branching.",
  },
  {
    path: `${APP_PREFIX}/projects`,
    label: "Projects",
    section: "Core",
    summary: "Projects, state, and decisions.",
  },
  {
    path: `${APP_PREFIX}/sessions`,
    label: "Sessions",
    section: "Core",
    summary: "Session trees and messages.",
  },
  {
    path: `${APP_PREFIX}/tasks`,
    label: "Tasks",
    section: "Core",
    summary: "Task lifecycle and DLQ inspection.",
  },
  {
    path: `${APP_PREFIX}/leaderboard`,
    label: "Leaderboard",
    section: "Models",
    summary: "Capability, quality, and price matrix.",
  },
  {
    path: `${APP_PREFIX}/compare`,
    label: "Compare",
    section: "Models",
    summary: "Parallel output comparison.",
  },
  {
    path: `${APP_PREFIX}/provider-health`,
    label: "Provider Health",
    section: "Models",
    summary: "Circuit and health telemetry.",
  },
  {
    path: `${APP_PREFIX}/routing-decision`,
    label: "Routing Decision",
    section: "Models",
    summary: "Classifier and fallback chain viewer.",
  },
  {
    path: `${APP_PREFIX}/memory`,
    label: "Memory",
    section: "Memory",
    summary: "Session, project, and preference memory.",
  },
  {
    path: `${APP_PREFIX}/context-inspector`,
    label: "Context Inspector",
    section: "Memory",
    summary: "Assembled context and token budget.",
  },
  {
    path: `${APP_PREFIX}/semantic-cache`,
    label: "Semantic Cache",
    section: "Memory",
    summary: "Cache hit, miss, and similarity records.",
  },
  {
    path: `${APP_PREFIX}/artifacts`,
    label: "Artifacts",
    section: "Assets",
    summary: "Versioned artifacts and exports.",
  },
  {
    path: `${APP_PREFIX}/prompt-templates`,
    label: "Prompt Templates",
    section: "Assets",
    summary: "Registry, diff, and rollback.",
  },
  {
    path: `${APP_PREFIX}/spend-analytics`,
    label: "Spend Analytics",
    section: "Observability",
    summary: "Cost, quota, and usage trends.",
  },
  {
    path: `${APP_PREFIX}/replay`,
    label: "Replay",
    section: "Observability",
    summary: "Replay past task runs.",
  },
  {
    path: `${APP_PREFIX}/event-log`,
    label: "Event Log",
    section: "Observability",
    summary: "Webhook event stream and delivery state.",
  },
  {
    path: `${APP_PREFIX}/policies`,
    label: "Policies",
    section: "Security",
    summary: "PII, privacy, approval, and budget policy posture.",
  },
  {
    path: `${APP_PREFIX}/approvals`,
    label: "Approvals",
    section: "Security",
    summary: "Pending approvals and audit posture.",
  },
  {
    path: `${APP_PREFIX}/api-keys`,
    label: "API Keys",
    section: "Security",
    summary: "Key rotation and expiry posture.",
  },
  {
    path: `${APP_PREFIX}/webhooks`,
    label: "Webhooks",
    section: "Admin",
    summary: "Webhook subscriptions and delivery.",
  },
  {
    path: `${APP_PREFIX}/evals`,
    label: "Evals",
    section: "Admin",
    summary: "Prompt and model evaluation harness.",
  },
  {
    path: `${APP_PREFIX}/settings`,
    label: "Settings",
    section: "Admin",
    summary: "Provider and local runtime defaults.",
  },
];

export const routeGroups = routes.reduce<Record<string, RouteItem[]>>((acc, route) => {
  acc[route.section] ??= [];
  acc[route.section].push(route);
  return acc;
}, {});
