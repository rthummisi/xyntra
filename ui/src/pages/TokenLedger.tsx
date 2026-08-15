import { useEffect, useState } from "react";
import { api } from "../lib/api";

interface TokenRow {
  date: string;
  time: string;
  task: string;
  provider: string;
  model: string;
  task_type: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cache_hit: boolean;
  efficiency: "productive" | "useless";
  efficiency_reason: string;
}

interface LedgerData {
  totals: {
    total_entries: number;
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    productive: number;
    useless: number;
  };
  rows: TokenRow[];
}

export default function TokenLedger() {
  const [data, setData] = useState<LedgerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  const load = () => {
    setLoading(true);
    api
      .tokenLedger(200)
      .then((d) => setData(d as unknown as LedgerData))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, []);

  const clear = async () => {
    if (!confirm("Clear the token ledger? This cannot be undone.")) return;
    setClearing(true);
    await api.clearTokenLedger().catch(() => null);
    setClearing(false);
    load();
  };

  if (loading && !data) {
    return (
      <div className="panel">
        <p style={{ color: "var(--os-muted)" }}>Loading token ledger…</p>
      </div>
    );
  }

  const totals = data?.totals;
  const rows = data?.rows ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h2 style={{ color: "var(--os-accent)", margin: 0, fontSize: "1.1rem", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Token Ledger
          </h2>
          <p style={{ color: "var(--os-muted)", margin: "0.25rem 0 0", fontSize: "0.8rem" }}>
            Per-task token burn. Auto-refreshes every 10 s.
          </p>
        </div>
        <button
          onClick={clear}
          disabled={clearing}
          style={{
            background: "transparent",
            border: "1px solid #f43f5e",
            color: "#f43f5e",
            padding: "0.35rem 0.9rem",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "0.75rem",
            fontFamily: "inherit",
          }}
        >
          {clearing ? "Clearing…" : "Clear Ledger"}
        </button>
      </div>

      {/* Totals row */}
      {totals && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: "0.75rem" }}>
          {[
            { label: "Total Calls", value: totals.total_entries },
            { label: "Total Tokens", value: totals.total_tokens.toLocaleString() },
            { label: "Prompt", value: totals.prompt_tokens.toLocaleString() },
            { label: "Completion", value: totals.completion_tokens.toLocaleString() },
            { label: "Productive", value: totals.productive, accent: "#22d3ee" },
            { label: "Useless", value: totals.useless, accent: "#f43f5e" },
          ].map(({ label, value, accent }) => (
            <div key={label} className="metric-card">
              <div
                className="metric-value"
                style={accent ? { color: accent } : undefined}
              >
                {value}
              </div>
              <div className="metric-label">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="panel" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.78rem" }}>
            <thead>
              <tr style={{ background: "rgba(34,211,238,0.06)", borderBottom: "1px solid rgba(34,211,238,0.15)" }}>
                {[
                  "Date", "Time", "Task", "Provider", "Model",
                  "Type", "Prompt", "Completion", "Total", "Cache",
                  "Efficiency", "Reason",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "0.55rem 0.75rem",
                      textAlign: "left",
                      color: "var(--os-accent)",
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      letterSpacing: "0.04em",
                      fontSize: "0.7rem",
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={12}
                    style={{ padding: "2rem", textAlign: "center", color: "var(--os-muted)" }}
                  >
                    No token entries yet. Send a message to start recording.
                  </td>
                </tr>
              ) : (
                rows.map((row, i) => {
                  const isUseless = row.efficiency === "useless";
                  return (
                    <tr
                      key={i}
                      style={{
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                        background: isUseless ? "rgba(244,63,94,0.04)" : undefined,
                      }}
                    >
                      <td style={tdStyle}>{row.date}</td>
                      <td style={{ ...tdStyle, color: "var(--os-muted)" }}>{row.time}</td>
                      <td
                        style={{ ...tdStyle, maxWidth: "220px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                        title={row.task}
                      >
                        {row.task || "—"}
                      </td>
                      <td style={{ ...tdStyle, color: "#a78bfa" }}>{row.provider}</td>
                      <td style={{ ...tdStyle, color: "#5ec4aa", whiteSpace: "nowrap" }}>{row.model}</td>
                      <td style={{ ...tdStyle, color: "var(--os-muted)" }}>{row.task_type}</td>
                      <td style={{ ...tdStyle, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                        {row.prompt_tokens.toLocaleString()}
                      </td>
                      <td style={{ ...tdStyle, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
                        {row.completion_tokens.toLocaleString()}
                      </td>
                      <td style={{ ...tdStyle, textAlign: "right", fontVariantNumeric: "tabular-nums", fontWeight: 600, color: "var(--os-accent)" }}>
                        {row.total_tokens.toLocaleString()}
                      </td>
                      <td style={{ ...tdStyle, textAlign: "center" }}>
                        {row.cache_hit ? (
                          <span style={{ color: "#22d3ee", fontSize: "0.7rem" }}>HIT</span>
                        ) : (
                          <span style={{ color: "var(--os-muted)", fontSize: "0.7rem" }}>—</span>
                        )}
                      </td>
                      <td style={{ ...tdStyle, whiteSpace: "nowrap" }}>
                        <span
                          style={{
                            padding: "0.2rem 0.5rem",
                            borderRadius: "3px",
                            fontSize: "0.68rem",
                            fontWeight: 700,
                            textTransform: "uppercase",
                            letterSpacing: "0.06em",
                            background: isUseless ? "rgba(244,63,94,0.15)" : "rgba(34,211,238,0.1)",
                            color: isUseless ? "#f43f5e" : "#22d3ee",
                          }}
                        >
                          {row.efficiency}
                        </span>
                      </td>
                      <td
                        style={{ ...tdStyle, color: "var(--os-muted)", maxWidth: "260px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                        title={row.efficiency_reason}
                      >
                        {row.efficiency_reason}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const tdStyle: React.CSSProperties = {
  padding: "0.5rem 0.75rem",
  color: "var(--os-text)",
};
