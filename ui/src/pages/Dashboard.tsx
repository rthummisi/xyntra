import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { api, useQuery } from "../lib/api";
import { APP_PREFIX } from "../lib/routes";
import { MetricCard, Panel, StatusPill } from "../components/Chrome";

function LiveExecutionGraph({ agents }: { agents: Array<Record<string, unknown>> }) {
  const stateColor: Record<string, string> = {
    running: "#22d3ee",
    spawning: "#e8b84b",
    done: "#22c55e",
    failed: "#f43f5e",
    killed: "#64748b",
    idle: "#334155",
    waiting: "#a78bfa",
  };

  if (agents.length === 0) {
    return (
      <div className="exec-graph-empty">
        <p className="exec-empty-title">NO ACTIVE AGENTS</p>
        <p className="exec-empty-sub">Dispatch a mission from Agent Fleet to see live execution.</p>
        <NavLink className="exec-empty-cta" to={`${APP_PREFIX}/agent-fleet`}>
          → AGENT FLEET
        </NavLink>
      </div>
    );
  }

  return (
    <div className="exec-graph">
      {agents.map((a) => {
        const state = String(a.state ?? "idle");
        const color = stateColor[state] ?? "#64748b";
        const isLive = state === "running" || state === "spawning";
        return (
          <div key={String(a.agent_id)} className="exec-node" style={{ "--node-color": color } as React.CSSProperties}>
            <div className={`exec-node-ring${isLive ? " pulse" : ""}`} style={{ borderColor: color }} />
            <span className="exec-node-role mono">{String(a.role ?? "").slice(0, 3).toUpperCase()}</span>
            <span className="exec-node-name">{String(a.name ?? "").split("-")[0]}</span>
            <StatusPill value={state} />
          </div>
        );
      })}
    </div>
  );
}

function SystemStatusRow() {
  const health = useQuery(api.providerHealth as () => Promise<unknown[]>, []);
  const providers = ((health.data as unknown[]) ?? []) as Array<Record<string, unknown>>;
  const healthy = providers.filter((p) => p.status === "healthy").length;

  return (
    <div className="status-row">
      {providers.slice(0, 8).map((p) => (
        <div key={String(p.provider)} className="provider-status-chip">
          <span className={`chip-dot ${p.status === "healthy" ? "green" : "red"}`} />
          <span className="chip-name mono">{String(p.provider)}</span>
        </div>
      ))}
      <span className="status-row-summary">{healthy}/{providers.length} healthy</span>
    </div>
  );
}

export default function Dashboard() {
  const agents = useQuery(api.agents, []);
  const active = useQuery(api.activeAgents, []);
  const health = useQuery(api.providerHealth as () => Promise<unknown[]>, []);
  const hw = useQuery(api.hwLive, []);
  const spend = useQuery(api.spendDashboard as () => Promise<unknown>, []);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 4000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    void agents.refresh();
    void active.refresh();
    void hw.refresh();
  }, [tick]);

  const allAgents = (agents.data as Array<Record<string, unknown>>) ?? [];
  const activeCount = (active.data?.active_count as number) ?? 0;
  const freeVram = (hw.data?.free_vram_gb as number) ?? 0;
  const hasCuda = Boolean(hw.data?.has_cuda);
  const hasMps = Boolean(hw.data?.has_mps);
  const providers = ((health.data as unknown[]) ?? []) as Array<Record<string, unknown>>;
  const healthyCount = providers.filter((p) => p.status === "healthy").length;
  const spendData = spend.data as Record<string, unknown> | null;
  const spendSummary = (spendData?.summary as Record<string, unknown>) ?? {};
  const spendUsd = Number(spendSummary.cost_usd ?? 0).toFixed(2);

  return (
    <div className="mission-control">
      <div className="mc-header">
        <div className="mc-title-block">
          <p className="mc-eyebrow">XYNTRA AGENTIC OS — MISSION CONTROL</p>
          <h1 className="mc-title">System Status</h1>
        </div>
        <div className="mc-live-badge">
          <span className="live-dot" />
          LIVE
        </div>
      </div>

      <div className="mc-metrics">
        <MetricCard label="ACTIVE AGENTS" value={activeCount} detail="Running now" live={activeCount > 0} />
        <MetricCard label="PROVIDERS" value={`${healthyCount}/${providers.length}`} detail="Healthy" />
        <MetricCard
          label="COMPUTE"
          value={hasCuda ? "CUDA GPU" : hasMps ? "APPLE MPS" : "CPU"}
          detail={hasCuda || hasMps ? `${freeVram.toFixed(1)} GB VRAM free` : "API only mode"}
        />
        <MetricCard label="SPEND" value={`$${spendUsd}`} detail="Total tracked cost" />
      </div>

      <div className="mc-body">
        <div className="mc-main">
          <Panel title="Execution Graph" subtitle="Live agent fleet state.">
            <LiveExecutionGraph agents={allAgents} />
          </Panel>

          <Panel title="Provider Grid" subtitle="All registered worker-bee providers.">
            <SystemStatusRow />
            <div className="provider-grid">
              {providers.map((p) => (
                <div key={String(p.provider)} className={`provider-tile ${p.status === "healthy" ? "ok" : "degraded"}`}>
                  <span className="provider-tile-name mono">{String(p.provider)}</span>
                  <StatusPill value={String(p.status ?? "unknown")} />
                  <span className="provider-tile-failures mono">
                    {(p.details as Record<string, unknown>)?.circuit_failures as number ?? 0} failures
                  </span>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="mc-sidebar">
          <Panel title="Quick Nav" subtitle="OS entry points.">
            <div className="quick-nav">
              <NavLink className="qnav-item" to={`${APP_PREFIX}/agent-fleet`}>
                <span className="qnav-icon">⬡</span>
                <div>
                  <span className="qnav-label">Agent Fleet</span>
                  <p className="qnav-sub">Spawn and monitor agents</p>
                </div>
              </NavLink>
              <NavLink className="qnav-item" to={`${APP_PREFIX}/hardware`}>
                <span className="qnav-icon">⎖</span>
                <div>
                  <span className="qnav-label">Hardware</span>
                  <p className="qnav-sub">GPU telemetry and model fit</p>
                </div>
              </NavLink>
              <NavLink className="qnav-item" to={`${APP_PREFIX}/kernel`}>
                <span className="qnav-icon">◈</span>
                <div>
                  <span className="qnav-label">Kernel</span>
                  <p className="qnav-sub">Classify and route any task</p>
                </div>
              </NavLink>
              <NavLink className="qnav-item" to={`${APP_PREFIX}/chat`}>
                <span className="qnav-icon">▶</span>
                <div>
                  <span className="qnav-label">Dispatch</span>
                  <p className="qnav-sub">Direct inference</p>
                </div>
              </NavLink>
            </div>
          </Panel>

          <Panel title="Agent Activity" subtitle="Recent processes.">
            {allAgents.length === 0 ? (
              <p className="muted-note">No agents spawned yet.</p>
            ) : (
              <div className="activity-list">
                {allAgents.slice(-8).reverse().map((a) => (
                  <div key={String(a.agent_id)} className="activity-row">
                    <span className="activity-role mono">{String(a.role)}</span>
                    <StatusPill value={String(a.state)} />
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
