export type SimulationStrategy =
  | "balanced"
  | "cost"
  | "latency"
  | "quality"
  | "privacy";

export type SimulationPreset =
  | "rate-limit-recovery"
  | "local-private-repair"
  | "vision-fallback";

export type SimulationInput = {
  objective: string;
  strategy: SimulationStrategy;
  localOnly: boolean;
  containsPii: boolean;
  requiresVision: boolean;
  strictLatency: boolean;
  preferredProvider: string;
  degradedProviders: string[];
};

export type SimulationDecision = {
  presetLabel: string;
  summary: string;
  selected: SimulationCandidate;
  fallbackChain: SimulationCandidate[];
  blockedProviders: string[];
  reasoning: string[];
};

export type SimulationCandidate = {
  provider: string;
  model: string;
  latency: number;
  cost: number;
  quality: number;
  local: boolean;
  vision: boolean;
  privacy: number;
  score?: number;
};

type CandidateDefinition = Omit<SimulationCandidate, "score">;

const candidates: CandidateDefinition[] = [
  {
    provider: "openai",
    model: "gpt-4o-mini",
    latency: 9,
    cost: 6,
    quality: 8,
    local: false,
    vision: true,
    privacy: 4,
  },
  {
    provider: "anthropic",
    model: "claude-sonnet-4-6",
    latency: 7,
    cost: 5,
    quality: 9,
    local: false,
    vision: true,
    privacy: 5,
  },
  {
    provider: "gemini",
    model: "gemini-2.5-pro",
    latency: 6,
    cost: 6,
    quality: 9,
    local: false,
    vision: true,
    privacy: 5,
  },
  {
    provider: "groq",
    model: "llama-3.3-70b-versatile",
    latency: 10,
    cost: 8,
    quality: 7,
    local: false,
    vision: false,
    privacy: 4,
  },
  {
    provider: "ollama",
    model: "qwen2.5-coder:32b",
    latency: 5,
    cost: 10,
    quality: 7,
    local: true,
    vision: false,
    privacy: 10,
  },
  {
    provider: "ollama",
    model: "llama3.2:11b",
    latency: 6,
    cost: 10,
    quality: 6,
    local: true,
    vision: true,
    privacy: 10,
  },
];

const presetLabels: Record<SimulationPreset, string> = {
  "rate-limit-recovery": "Rate-limit recovery",
  "local-private-repair": "Local-only private repair",
  "vision-fallback": "Vision request with provider outage",
};

const strategyWeights: Record<
  SimulationStrategy,
  { latency: number; cost: number; quality: number; privacy: number }
> = {
  balanced: { latency: 0.3, cost: 0.2, quality: 0.3, privacy: 0.2 },
  cost: { latency: 0.15, cost: 0.45, quality: 0.15, privacy: 0.25 },
  latency: { latency: 0.5, cost: 0.15, quality: 0.15, privacy: 0.2 },
  quality: { latency: 0.1, cost: 0.1, quality: 0.55, privacy: 0.25 },
  privacy: { latency: 0.1, cost: 0.1, quality: 0.15, privacy: 0.65 },
};

export function presetInput(preset: SimulationPreset): SimulationInput {
  switch (preset) {
    case "local-private-repair":
      return {
        objective: "Repair a private integration failure using only local execution.",
        strategy: "privacy",
        localOnly: true,
        containsPii: true,
        requiresVision: false,
        strictLatency: false,
        preferredProvider: "openai",
        degradedProviders: [],
      };
    case "vision-fallback":
      return {
        objective: "Analyze a UI screenshot after the preferred vision provider went unhealthy.",
        strategy: "quality",
        localOnly: false,
        containsPii: false,
        requiresVision: true,
        strictLatency: false,
        preferredProvider: "openai",
        degradedProviders: ["openai"],
      };
    case "rate-limit-recovery":
    default:
      return {
        objective: "Continue a coding task after the primary model hits a rate limit.",
        strategy: "balanced",
        localOnly: false,
        containsPii: false,
        requiresVision: false,
        strictLatency: true,
        preferredProvider: "openai",
        degradedProviders: ["openai"],
      };
  }
}

export function simulateRoutingDecision(
  input: SimulationInput,
  preset: SimulationPreset,
): SimulationDecision {
  const reasoning: string[] = [];
  let filtered = [...candidates];

  reasoning.push(
    `Policy check: strategy=${input.strategy}, local_only=${String(input.localOnly)}, pii=${String(input.containsPii)}.`,
  );

  if (input.localOnly || input.containsPii) {
    filtered = filtered.filter((candidate) => candidate.local);
    reasoning.push(
      "Privacy filter removed hosted providers because the request is local-only or contains sensitive data.",
    );
  }

  if (input.requiresVision) {
    filtered = filtered.filter((candidate) => candidate.vision);
    reasoning.push(
      "Capability filter kept only models that can accept visual inputs.",
    );
  }

  if (input.strictLatency) {
    filtered = filtered.filter((candidate) => candidate.latency >= 6);
    reasoning.push(
      "Latency SLA removed slower candidates that would likely miss the interactive threshold.",
    );
  }

  const blockedProviders = Array.from(
    new Set(
      input.degradedProviders.filter((provider) =>
        filtered.some((candidate) => candidate.provider === provider),
      ),
    ),
  );
  if (blockedProviders.length > 0) {
    filtered = filtered.filter(
      (candidate) => !blockedProviders.includes(candidate.provider),
    );
    reasoning.push(
      `Circuit breaker skipped degraded providers: ${blockedProviders.join(", ")}.`,
    );
  }

  const weights = strategyWeights[input.strategy];
  const preferredBoost = input.localOnly ? 0 : 0.8;

  const ranked = filtered
    .map((candidate) => {
      const score =
        candidate.latency * weights.latency +
        candidate.cost * weights.cost +
        candidate.quality * weights.quality +
        candidate.privacy * weights.privacy +
        (candidate.provider === input.preferredProvider ? preferredBoost : 0);
      return { ...candidate, score: Number(score.toFixed(2)) };
    })
    .sort((left, right) => (right.score ?? 0) - (left.score ?? 0));

  const selected =
    ranked[0] ??
    ({
      provider: "none",
      model: "no-eligible-model",
      latency: 0,
      cost: 0,
      quality: 0,
      local: input.localOnly,
      vision: input.requiresVision,
      privacy: 0,
      score: 0,
    } satisfies SimulationCandidate);

  const fallbackChain = ranked.slice(1, 4);
  reasoning.push(
    `Strategy scoring selected ${selected.provider}/${selected.model} with a score of ${selected.score ?? 0}.`,
  );
  if (fallbackChain.length > 0) {
    reasoning.push(
      `Fallback chain prepared: ${fallbackChain.map((candidate) => `${candidate.provider}/${candidate.model}`).join(" -> ")}.`,
    );
  }

  return {
    presetLabel: presetLabels[preset],
    summary: buildSummary(selected, input, blockedProviders),
    selected,
    fallbackChain,
    blockedProviders,
    reasoning,
  };
}

function buildSummary(
  candidate: SimulationCandidate,
  input: SimulationInput,
  blockedProviders: string[],
): string {
  if (candidate.provider === "none") {
    return "No eligible provider satisfied the current policy and capability constraints.";
  }

  const recoveryClause =
    blockedProviders.length > 0
      ? ` after excluding ${blockedProviders.join(", ")}`
      : "";
  const privacyClause = input.localOnly
    ? " while keeping all execution local"
    : "";
  return `${candidate.provider}/${candidate.model} was selected${recoveryClause}${privacyClause} because it best matched the ${input.strategy} strategy for this request.`;
}
