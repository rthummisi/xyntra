import { useEffect, useState } from "react";
import { api, useQuery } from "../lib/api";
import { DataState, MetricCard, Panel, PageHeader, StatusPill } from "../components/Chrome";

const ROLE_COLORS: Record<string, string> = {
  coordinator: "#e8b84b",
  reasoning: "#7c9ef8",
  research: "#5ec4aa",
  coding: "#a78bfa",
  synthesis: "#f97316",
  validation: "#22d3ee",
  critic: "#f43f5e",
  summarizer: "#94a3b8",
};

function AgentCard({ agent }: { agent: Record<string, unknown> }) {
  const role = String(agent.role ?? "");
  const state = String(agent.state ?? "");
  const color = ROLE_COLORS[role] ?? "#64748b";
  const isLive = state === "running" || state === "spawning";

  return (
    <article className="agent-card" style={{ "--agent-color": color } as React.CSSProperties}>
      <div className="agent-card-header">
        <div className="agent-role-dot" style={{ background: color }} />
        <span className="agent-name">{String(agent.name ?? "")}</span>
        <StatusPill value={state} />
      </div>
      <div className="agent-card-meta">
        <span className="agent-meta-item">
          <span className="meta-label">ROLE</span>
          <span className="meta-val" style={{ color }}>{role.toUpperCase()}</span>
        </span>
        <span className="agent-meta-item">
          <span className="meta-label">PROVIDER</span>
          <span className="meta-val">{String(agent.assigned_provider ?? "–")}</span>
        </span>
        <span className="agent-meta-item">
          <span className="meta-label">MODEL</span>
          <span className="meta-val mono">{String(agent.assigned_model ?? "–")}</span>
        </span>
      </div>
      {isLive && <div className="agent-pulse-bar" style={{ background: color }} />}
      {agent.result_summary ? (
        <p className="agent-result">{String(agent.result_summary).slice(0, 120)}…</p>
      ) : null}
    </article>
  );
}

function MissionLauncher({ onMission }: { onMission: (res: unknown) => void }) {
  const [objective, setObjective] = useState("");
  const [roles, setRoles] = useState<string[]>(["coordinator", "reasoning", "synthesis", "validation"]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const allRoles = ["coordinator", "reasoning", "research", "coding", "synthesis", "validation", "critic", "summarizer"];

  function toggleRole(r: string) {
    setRoles((prev) => prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]);
  }

  async function launch() {
    if (!objective.trim()) return;
    setRunning(true);
    setError(null);
    try {
      const res = await api.runMission({ objective, roles });
      onMission(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Mission failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <Panel title="Mission Dispatch" subtitle="Define objective and agent roster, then launch.">
      <div className="mission-form">
        <label className="field-label">MISSION OBJECTIVE</label>
        <textarea
          className="mission-input"
          placeholder="Describe what you need the fleet to accomplish…"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          rows={4}
        />
        <label className="field-label">AGENT ROSTER</label>
        <div className="role-picker">
          {allRoles.map((r) => (
            <button
              key={r}
              className={`role-chip${roles.includes(r) ? " selected" : ""}`}
              style={{ "--chip-color": ROLE_COLORS[r] ?? "#64748b" } as React.CSSProperties}
              onClick={() => toggleRole(r)}
            >
              {r}
            </button>
          ))}
        </div>
        {error && <p className="error-inline">{error}</p>}
        <button
          className="launch-btn"
          onClick={launch}
          disabled={running || !objective.trim()}
        >
          {running ? "EXECUTING…" : "LAUNCH MISSION"}
        </button>
      </div>
    </Panel>
  );
}

export default function AgentFleet() {
  const all = useQuery(api.agents, []);
  const active = useQuery(api.activeAgents, []);
  const roles = useQuery(api.agentRoles, []);
  const [lastMission, setLastMission] = useState<unknown>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 3000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    void all.refresh();
    void active.refresh();
  }, [tick]);

  const agents = (all.data as Array<Record<string, unknown>>) ?? [];
  const activeCount = (active.data?.active_count as number) ?? 0;
  const rolesCatalog = (roles.data as Array<Record<string, unknown>>) ?? [];

  return (
    <div className="surface-page">
      <PageHeader
        title="Agent Fleet"
        kicker="OS KERNEL · AGENTS"
        badge={activeCount > 0 ? `${activeCount} LIVE` : undefined}
        description="Spawn agents, form mission teams, and monitor execution in real-time."
      />

      <div className="metrics-row">
        <MetricCard label="TOTAL AGENTS" value={agents.length} detail="All time" />
        <MetricCard label="ACTIVE" value={activeCount} detail="Running + spawning" live={activeCount > 0} />
        <MetricCard label="ROLES DEFINED" value={rolesCatalog.length} detail="Agent archetypes" />
      </div>

      <div className="fleet-layout">
        <div className="fleet-left">
          <MissionLauncher onMission={setLastMission} />
          {lastMission ? (
            <Panel title="Last Mission Result" mono>
              <pre className="json-block">{JSON.stringify(lastMission, null, 2)}</pre>
            </Panel>
          ) : null}
          <Panel title="Agent Archetypes" subtitle="Built-in role definitions.">
            <DataState loading={roles.status === "loading"} error={roles.error} empty={rolesCatalog.length === 0}>
              <div className="archetype-list">
                {rolesCatalog.map((r) => (
                  <div key={String(r.role)} className="archetype-row">
                    <div className="archetype-dot" style={{ background: (ROLE_COLORS[String(r.role)] ?? "#64748b") as string }} />
                    <div>
                      <span className="archetype-role">{String(r.role)}</span>
                      <p className="archetype-desc">{String(r.description)}</p>
                      <span className="archetype-meta mono">{String(r.preferred_provider)} / {String(r.preferred_model)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </DataState>
          </Panel>
        </div>

        <div className="fleet-right">
          <Panel title="Live Fleet" subtitle="All agent processes this session.">
            <DataState
              loading={all.status === "loading"}
              error={all.error}
              empty={agents.length === 0}
              emptyTitle="Fleet empty"
              emptyBody="Launch a mission to spawn agents."
            >
              <div className="agent-grid">
                {agents.map((a) => (
                  <AgentCard key={String(a.agent_id)} agent={a} />
                ))}
              </div>
            </DataState>
          </Panel>
        </div>
      </div>
    </div>
  );
}
