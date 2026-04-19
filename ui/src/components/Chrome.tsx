import { NavLink } from "react-router-dom";
import { routeGroups } from "../lib/routes";

export function Chrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Local AI Control Plane</p>
          <h1>Xyntra</h1>
          <p className="muted">
            One machine. Multi-provider orchestration. Project-aware execution.
          </p>
        </div>
        <nav className="nav-groups">
          {Object.entries(routeGroups).map(([section, items]) => (
            <div className="nav-group" key={section}>
              <p className="nav-section">{section}</p>
              {items.map((item) => (
                <NavLink
                  className={({ isActive }) =>
                    isActive ? "nav-link active" : "nav-link"
                  }
                  key={item.path}
                  to={item.path}
                >
                  <span>{item.label}</span>
                  <small>{item.summary}</small>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      <main className="main-stage">{children}</main>
    </div>
  );
}

export function PageHeader(props: {
  title: string;
  description: string;
  kicker?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{props.kicker ?? "Frontend Phase"}</p>
        <h2>{props.title}</h2>
        <p className="page-description">{props.description}</p>
      </div>
      {props.actions ? <div className="header-actions">{props.actions}</div> : null}
    </header>
  );
}

export function Panel(props: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  tone?: "default" | "accent";
}) {
  return (
    <section className={`panel ${props.tone === "accent" ? "panel-accent" : ""}`}>
      <div className="panel-header">
        <div>
          <h3>{props.title}</h3>
          {props.subtitle ? <p className="muted">{props.subtitle}</p> : null}
        </div>
      </div>
      {props.children}
    </section>
  );
}

export function MetricCard(props: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <article className="metric-card">
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      {props.detail ? <small>{props.detail}</small> : null}
    </article>
  );
}

export function EmptyState(props: {
  title: string;
  body: string;
}) {
  return (
    <div className="empty-state">
      <h4>{props.title}</h4>
      <p>{props.body}</p>
    </div>
  );
}

export function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  return <span className={`status-pill ${normalized}`}>{value}</span>;
}

export function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

export function DataState(props: {
  loading: boolean;
  error: string | null;
  empty: boolean;
  emptyTitle?: string;
  emptyBody?: string;
  children: React.ReactNode;
}) {
  if (props.loading) {
    return <div className="empty-state">Loading live data…</div>;
  }
  if (props.error) {
    return <div className="error-state">{props.error}</div>;
  }
  if (props.empty) {
    return (
      <EmptyState
        title={props.emptyTitle ?? "No data yet"}
        body={props.emptyBody ?? "The backend returned no records for this surface."}
      />
    );
  }
  return <>{props.children}</>;
}

export function ContractNote(props: {
  title: string;
  body: string;
}) {
  return (
    <div className="contract-note">
      <strong>{props.title}</strong>
      <p>{props.body}</p>
    </div>
  );
}
