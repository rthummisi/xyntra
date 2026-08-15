import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { api, useQuery } from "../lib/api";
import { routeGroups } from "../lib/routes";

function SystemBar() {
  const hw = useQuery(api.hwLive, []);
  const agents = useQuery(api.activeAgents, []);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 5000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    void hw.refresh();
    void agents.refresh();
  }, [tick]);

  const gpus = (hw.data?.gpus as Array<Record<string, unknown>>) ?? [];
  const activeCount = (agents.data?.active_count as number) ?? 0;
  const freeVram = (hw.data?.free_vram_gb as number) ?? 0;
  const hasCuda = Boolean(hw.data?.has_cuda);
  const hasMps = Boolean(hw.data?.has_mps);

  return (
    <div className="sysbar">
      <div className="sysbar-brand">
        <span className="sysbar-logo">⬡</span>
        <span className="sysbar-name">XYNTRA</span>
        <span className="sysbar-sub">AGENTIC OS</span>
      </div>
      <div className="sysbar-metrics">
        {hasCuda || hasMps ? (
          <>
            {gpus.slice(0, 2).map((g, i) => {
              const util = (g.utilization_pct as number) ?? 0;
              const pressure = g.vram_pressure as string ?? "low";
              return (
                <div key={i} className="sysbar-gpu">
                  <div className="sysbar-ring-wrap">
                    <svg className="sysbar-ring" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="15.9" fill="none" strokeWidth="3" className="ring-track" />
                      <circle
                        cx="18" cy="18" r="15.9" fill="none" strokeWidth="3"
                        strokeDasharray={`${util} ${100 - util}`}
                        strokeDashoffset="25"
                        className={`ring-fill ring-${pressure}`}
                      />
                    </svg>
                    <span className="ring-label">{Math.round(util)}%</span>
                  </div>
                  <span className="sysbar-gpu-name">GPU{i}</span>
                </div>
              );
            })}
            <div className="sysbar-stat">
              <span className="sysbar-stat-val">{freeVram.toFixed(1)}</span>
              <span className="sysbar-stat-key">VRAM FREE GB</span>
            </div>
          </>
        ) : (
          <div className="sysbar-stat">
            <span className="sysbar-stat-val">CPU</span>
            <span className="sysbar-stat-key">{hasMps ? "APPLE MPS" : "NO GPU"}</span>
          </div>
        )}
        <div className="sysbar-divider" />
        <div className="sysbar-stat">
          <span className={`sysbar-stat-val ${activeCount > 0 ? "live" : ""}`}>{activeCount}</span>
          <span className="sysbar-stat-key">AGENTS LIVE</span>
        </div>
        <div className="sysbar-stat">
          <span className="sysbar-stat-val status-dot-green">●</span>
          <span className="sysbar-stat-key">KERNEL ONLINE</span>
        </div>
      </div>
    </div>
  );
}

export function Chrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="os-shell">
      <SystemBar />
      <div className="os-body">
        <nav className="os-nav">
          <div className="os-nav-inner">
            {Object.entries(routeGroups).map(([section, items]) => (
              <div className="nav-group" key={section}>
                <p className="nav-section-label">{section}</p>
                {items.map((item) => (
                  <NavLink
                    className={({ isActive }) =>
                      "nav-item" + (isActive ? " active" : "")
                    }
                    key={item.path}
                    to={item.path}
                    end={item.path.split("/").length <= 2}
                  >
                    <span className="nav-item-label">{item.label}</span>
                    <span className="nav-item-summary">{item.summary}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </div>
        </nav>
        <main className="os-main">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader(props: {
  title: string;
  description: string;
  kicker?: string;
  badge?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="page-header">
      <div className="page-header-left">
        {props.kicker && <p className="page-kicker">{props.kicker}</p>}
        <h1 className="page-title">{props.title}</h1>
        {props.badge && <span className="page-badge">{props.badge}</span>}
        <p className="page-desc">{props.description}</p>
      </div>
      {props.actions && <div className="page-actions">{props.actions}</div>}
    </header>
  );
}

export function Panel(props: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  tone?: "default" | "accent" | "alert";
  mono?: boolean;
}) {
  return (
    <section className={`panel${props.tone === "accent" ? " panel-accent" : ""}${props.tone === "alert" ? " panel-alert" : ""}`}>
      <div className="panel-header">
        <h3 className="panel-title">{props.title}</h3>
        {props.subtitle && <p className="panel-sub">{props.subtitle}</p>}
      </div>
      <div className={props.mono ? "panel-body mono" : "panel-body"}>{props.children}</div>
    </section>
  );
}

export function MetricCard(props: {
  label: string;
  value: string | number;
  detail?: string;
  live?: boolean;
  alert?: boolean;
}) {
  return (
    <article className={`metric-card${props.alert ? " alert" : ""}`}>
      <span className="metric-label">{props.label}</span>
      <strong className={`metric-value${props.live ? " live" : ""}`}>{props.value}</strong>
      {props.detail && <small className="metric-detail">{props.detail}</small>}
    </article>
  );
}

export function StatusPill({ value }: { value: string }) {
  const cls = value.toLowerCase().replace(/[^a-z]/g, "-");
  return <span className={`status-pill ${cls}`}>{value}</span>;
}

export function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

export function EmptyState(props: { title: string; body: string }) {
  return (
    <div className="empty-state">
      <h4>{props.title}</h4>
      <p>{props.body}</p>
    </div>
  );
}

export function DataState(props: {
  loading: boolean;
  error: string | null;
  empty: boolean;
  emptyTitle?: string;
  emptyBody?: string;
  children: React.ReactNode;
}) {
  if (props.loading) return <div className="empty-state loading">Acquiring data…</div>;
  if (props.error) return <div className="error-state">{props.error}</div>;
  if (props.empty)
    return (
      <EmptyState
        title={props.emptyTitle ?? "No records"}
        body={props.emptyBody ?? "Nothing to display yet."}
      />
    );
  return <>{props.children}</>;
}

export function ContractNote(props: { title: string; body: string }) {
  return (
    <div className="contract-note">
      <strong>{props.title}</strong>
      <p>{props.body}</p>
    </div>
  );
}

// ---- Legacy surface template shims (other pages use these) ----
export function SurfacePage(props: {
  title: string;
  description: string;
  kicker?: string;
  metrics?: Array<{ label: string; value: string | number; detail?: string }>;
  primary: React.ReactNode;
  secondary?: React.ReactNode;
}) {
  return (
    <div className="surface-page">
      <PageHeader title={props.title} description={props.description} kicker={props.kicker} />
      {props.metrics && (
        <div className="metrics-row">
          {props.metrics.map((m) => (
            <MetricCard key={m.label} label={m.label} value={m.value} detail={m.detail} />
          ))}
        </div>
      )}
      <div className={`surface-grid${props.secondary ? " two-col" : ""}`}>
        <div className="surface-primary">{props.primary}</div>
        {props.secondary && <div className="surface-secondary">{props.secondary}</div>}
      </div>
    </div>
  );
}
