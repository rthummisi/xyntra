export type ApiStatus = "idle" | "loading" | "ready" | "error";

export interface RouteItem {
  path: string;
  label: string;
  section: string;
  summary: string;
}

export interface QueryState<T> {
  data: T | null;
  error: string | null;
  status: ApiStatus;
  refresh: () => Promise<void>;
}

export interface ProviderSummary {
  provider: string;
  models: string[];
  local_only: boolean;
}

export interface ProviderHealth {
  provider: string;
  status: string;
  details: Record<string, unknown>;
}

export interface ProviderCapability {
  provider: string;
  model: string;
  quality_tier: string;
  cost_tier: string;
  latency_tier: string;
  context_window: number;
  supports_images: boolean;
  supports_pdf: boolean;
  supports_tools?: boolean;
  supports_streaming?: boolean;
  local_only: boolean;
}

export interface SpendDashboard {
  summary: Record<string, number>;
  by_project: Array<Record<string, string | number>>;
  by_model: Array<Record<string, string | number>>;
  by_date: Array<Record<string, string | number>>;
}

export interface EventRecord {
  id: string;
  subscription_id: string | null;
  event_type: string;
  payload: Record<string, unknown>;
  delivery_status: string;
  attempt_count: number;
  error_message: string | null;
}

export interface ProjectRecord {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  local_only: boolean;
  token_quota: number | null;
}

export interface ProjectStateRecord {
  id: string;
  project_id: string;
  state: Record<string, unknown>;
}

export interface SessionRecord {
  id: string;
  project_id: string;
  user_id: string;
  parent_session_id: string | null;
  title: string;
  status: string;
}

export interface TaskRecord {
  id: string;
  project_id: string;
  session_id: string | null;
  name: string;
  task_type: string;
  status: string;
  input_payload: Record<string, unknown>;
  description: string | null;
}

export interface DeadLetterRecord {
  id: string;
  task_name: string;
  payload: Record<string, unknown>;
  error_history: Array<Record<string, unknown>>;
  retry_count: number;
  status: string;
  last_error: string | null;
}

export interface PromptTemplateRecord {
  id: string;
  project_id: string | null;
  user_id: string | null;
  name: string;
  version: number;
  content: string;
  tags: string[];
}

export interface ArtifactRecord {
  id: string;
  project_id: string;
  task_id: string | null;
  name: string;
  kind: string;
  version: number;
  file_path: string;
  metadata_json: Record<string, unknown>;
}

export interface WebhookRecord {
  id: string;
  project_id: string | null;
  target_url: string;
  secret: string;
  event_types: string[];
  is_active: boolean;
}

export interface CompareResult {
  provider: string;
  model: string;
  response: {
    provider: string;
    model: string;
    content: string;
    finish_reason: string | null;
    usage: Record<string, unknown>;
  };
}

export interface RoutingDecisionRecord {
  selected_provider: string;
  selected_model: string;
  classification: Record<string, unknown>;
  fallback_chain: string[];
  metadata: Record<string, unknown>;
}

export interface RoutingResponse {
  decision: RoutingDecisionRecord;
  response: {
    provider: string;
    model: string;
    content: string;
    finish_reason: string | null;
    usage: Record<string, unknown>;
  };
}

export interface ReplayRecord {
  payload: Record<string, unknown>;
}

export interface MemorySnapshotRecord {
  session_messages: Array<Record<string, unknown>>;
  session_summaries: Array<Record<string, unknown>>;
  project_state: Record<string, unknown> | null;
  project_decisions: Array<Record<string, unknown>>;
  user_preferences: Array<Record<string, unknown>>;
}

export interface ContextInspectionRecord {
  assembled: {
    chunks: Array<{ content: string; source: string; score: number }>;
    budget: {
      total: number;
      reserved_for_output: number;
      available_for_context: number;
    };
  };
  source_project_id: string;
  model_name: string | null;
  total_window: number;
}

export interface PolicyRuleRecord {
  id: string;
  project_id: string | null;
  rule_type: string;
  name: string;
  enabled: boolean;
  config: Record<string, unknown>;
}

export interface ApprovalRecord {
  id: string;
  project_id: string | null;
  task_id: string | null;
  status: string;
  reason: string | null;
  approver_identifier: string | null;
}

export interface SemanticCacheRecord {
  key: string;
  response: string | null;
  local_only: boolean;
}

export interface ApiKeyRecord {
  id: string;
  key_id: string;
  name: string;
  token_preview: string;
  issued_at: string;
  expires_at: string;
  revoked_at: string | null;
  last_used_at: string | null;
  expired: boolean;
}
