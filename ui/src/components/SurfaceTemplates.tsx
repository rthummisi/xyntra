import type { ReactNode } from "react";
import { ContractNote, DataState, EmptyState, JsonBlock, MetricCard, PageHeader, Panel, StatusPill } from "./Chrome";

export function Grid(props: { children: ReactNode }) {
  return <div className="grid-layout">{props.children}</div>;
}

export function MetricsRow(props: {
  items: Array<{ label: string; value: string | number; detail?: string }>;
}) {
  return (
    <div className="metrics-row">
      {props.items.map((item) => (
        <MetricCard key={item.label} {...item} />
      ))}
    </div>
  );
}

export function SimpleTable(props: {
  columns: string[];
  rows: Array<Array<ReactNode>>;
}) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {props.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {props.rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td key={`${index}-${cellIndex}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SurfacePage(props: {
  title: string;
  description: string;
  kicker?: string;
  metrics?: Array<{ label: string; value: string | number; detail?: string }>;
  primary?: ReactNode;
  secondary?: ReactNode;
}) {
  return (
    <div className="page-stack">
      <PageHeader
        title={props.title}
        description={props.description}
        kicker={props.kicker}
      />
      {props.metrics?.length ? <MetricsRow items={props.metrics} /> : null}
      <Grid>
        {props.primary}
        {props.secondary}
      </Grid>
    </div>
  );
}

export function ContractDrivenPage(props: {
  title: string;
  description: string;
  noteTitle: string;
  noteBody: string;
  snapshot: Record<string, unknown>;
}) {
  return (
    <SurfacePage
      title={props.title}
      description={props.description}
      primary={
        <Panel title="Operational Status" subtitle="This surface is wired to the backend contract status.">
          <ContractNote title={props.noteTitle} body={props.noteBody} />
        </Panel>
      }
      secondary={
        <Panel title="Current Snapshot" subtitle="Visible contract shape for this capability.">
          <JsonBlock value={props.snapshot} />
        </Panel>
      }
    />
  );
}

export function DataPanel<T>(props: {
  title: string;
  subtitle?: string;
  loading: boolean;
  error: string | null;
  data: T[] | null;
  render: (data: T[]) => ReactNode;
  emptyTitle?: string;
  emptyBody?: string;
}) {
  const entries = props.data ?? [];
  return (
    <Panel title={props.title} subtitle={props.subtitle}>
      <DataState
        loading={props.loading}
        error={props.error}
        empty={entries.length === 0}
        emptyTitle={props.emptyTitle}
        emptyBody={props.emptyBody}
      >
        {props.render(entries)}
      </DataState>
    </Panel>
  );
}

export function FeedList(props: {
  items: Array<{
    title: string;
    body?: string;
    status?: string;
    meta?: string;
  }>;
}) {
  if (props.items.length === 0) {
    return <EmptyState title="No items" body="The feed is currently empty." />;
  }
  return (
    <div className="feed-list">
      {props.items.map((item) => (
        <article className="feed-item" key={`${item.title}-${item.meta}`}>
          <div className="feed-row">
            <h4>{item.title}</h4>
            {item.status ? <StatusPill value={item.status} /> : null}
          </div>
          {item.body ? <p>{item.body}</p> : null}
          {item.meta ? <small>{item.meta}</small> : null}
        </article>
      ))}
    </div>
  );
}
