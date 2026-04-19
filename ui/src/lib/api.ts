import { useEffect, useMemo, useState } from "react";
import type {
  ArtifactRecord,
  ApprovalRecord,
  ApiKeyRecord,
  CompareResult,
  ContextInspectionRecord,
  EventRecord,
  MemorySnapshotRecord,
  PolicyRuleRecord,
  ProjectRecord,
  ProjectStateRecord,
  PromptTemplateRecord,
  ProviderCapability,
  ProviderHealth,
  ProviderSummary,
  QueryState,
  ReplayRecord,
  RoutingResponse,
  SemanticCacheRecord,
  SessionRecord,
  SpendDashboard,
  TaskRecord,
  DeadLetterRecord,
  WebhookRecord,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:18000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  if (response.status === 204) {
    return null as T;
  }
  return (await response.json()) as T;
}

export function useQuery<T>(loader: () => Promise<T>, deps: unknown[] = []): QueryState<T> {
  const memoLoader = useMemo(() => loader, deps);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");

  async function refresh(): Promise<void> {
    setStatus("loading");
    setError(null);
    try {
      const next = await memoLoader();
      setData(next);
      setStatus("ready");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Unknown error";
      setError(message);
      setStatus("error");
    }
  }

  useEffect(() => {
    void refresh();
  }, [memoLoader]);

  return { data, error, status, refresh };
}

export const api = {
  providers: () => request<ProviderSummary[]>("/providers"),
  providerHealth: () => request<ProviderHealth[]>("/providers/health"),
  capabilities: () => request<ProviderCapability[]>("/providers/capabilities"),
  leaderboard: () => request<ProviderCapability[]>("/providers/leaderboard"),
  spendDashboard: () => request<SpendDashboard>("/analytics/dashboard"),
  events: (query = "") => request<EventRecord[]>(`/events${query}`),
  projects: () => request<ProjectRecord[]>("/projects"),
  projectState: (projectId: string) => request<ProjectStateRecord>(`/projects/${projectId}/state`),
  sessions: (projectId: string) => request<SessionRecord[]>(`/projects/${projectId}/sessions`),
  tasks: (projectId: string) => request<TaskRecord[]>(`/tasks?project_id=${projectId}`),
  dlq: () => request<DeadLetterRecord[]>("/tasks/dlq"),
  prompts: () => request<PromptTemplateRecord[]>("/prompts"),
  artifacts: (projectId: string) => request<ArtifactRecord[]>(`/artifacts?project_id=${projectId}`),
  webhooks: () => request<WebhookRecord[]>("/webhooks"),
  memorySnapshot: (sessionId: string, projectId: string, userId: string) =>
    request<MemorySnapshotRecord>(
      `/memory/snapshot?session_id=${sessionId}&project_id=${projectId}&user_id=${userId}`,
    ),
  contextInspection: (projectId: string, modelName?: string) =>
    request<ContextInspectionRecord>(
      `/context/inspect?project_id=${projectId}${modelName ? `&model_name=${encodeURIComponent(modelName)}` : ""}`,
    ),
  policyRules: () => request<PolicyRuleRecord[]>("/policies/rules"),
  approvals: () => request<ApprovalRecord[]>("/approvals"),
  semanticCache: () => request<SemanticCacheRecord[]>("/cache/semantic"),
  apiKeys: () => request<ApiKeyRecord[]>("/security/api-keys"),
  compare: (payload: Record<string, unknown>) =>
    request<{ results: CompareResult[] }>("/compare", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  route: (payload: Record<string, unknown>) =>
    request<RoutingResponse>("/router", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  chat: (payload: Record<string, unknown>) =>
    request<RoutingResponse>("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  replay: (taskRunId: string) => request<ReplayRecord>(`/replay/${taskRunId}`),
  evals: (payload: Record<string, unknown>) =>
    request<{ results: Array<Record<string, unknown>> }>("/evals", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export { API_BASE };
