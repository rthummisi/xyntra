import { useEffect } from "react";
import { api, useQuery } from "../lib/api";
import { DataState, MetricCard, Panel, PageHeader } from "../components/Chrome";

function VramGauge({ used, total, label }: { used: number; total: number; label: string }) {
  const pct = total > 0 ? (used / total) * 100 : 0;
  const pressure = pct < 50 ? "low" : pct < 80 ? "med" : "high";
  const colors = { low: "#22d3ee", med: "#e8b84b", high: "#f43f5e" };
  const color = colors[pressure];
  const r = 54;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;

  return (
    <div className="vram-gauge">
      <svg viewBox="0 0 120 120" className="gauge-svg">
        <circle cx="60" cy="60" r={r} fill="none" stroke="var(--track)" strokeWidth="8" />
        <circle
          cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{ transition: "stroke-dasharray 0.5s ease" }}
        />
        <text x="60" y="54" textAnchor="middle" className="gauge-pct" fill={color}>
          {Math.round(pct)}%
        </text>
        <text x="60" y="72" textAnchor="middle" className="gauge-sub" fill="var(--muted)">
          VRAM
        </text>
      </svg>
      <p className="gauge-label">{label}</p>
      <p className="gauge-detail">{(used / 1024).toFixed(1)} / {(total / 1024).toFixed(1)} GB</p>
    </div>
  );
}

function UtilBar({ value, label }: { value: number; label: string }) {
  const color = value < 50 ? "#22d3ee" : value < 80 ? "#e8b84b" : "#f43f5e";
  return (
    <div className="util-bar-row">
      <span className="util-label mono">{label}</span>
      <div className="util-track">
        <div className="util-fill" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="util-val mono" style={{ color }}>{Math.round(value)}%</span>
    </div>
  );
}

export default function HardwareCockpit() {
  const hw = useQuery(api.hwSnapshot, []);
  const fitting = useQuery(() => api.hwModelsFitting(0), []);

  useEffect(() => {
    const t = setInterval(() => { void hw.refresh(); }, 5000);
    return () => clearInterval(t);
  }, []);

  const snap = hw.data as Record<string, unknown> | null;
  const gpus = (snap?.gpus as Array<Record<string, unknown>>) ?? [];
  const fittingModels = (fitting.data as Array<Record<string, unknown>>) ?? [];

  return (
    <div className="surface-page">
      <PageHeader
        title="Hardware Cockpit"
        kicker="OS KERNEL · HARDWARE"
        description="GPU telemetry, VRAM pressure, and local model fit matrix."
      />

      <DataState
        loading={hw.status === "loading"}
        error={hw.error}
        empty={!snap}
        emptyTitle="No hardware detected"
        emptyBody="nvidia-smi not found. API-only providers are available."
      >
        <>
          <div className="metrics-row">
            <MetricCard
              label="GPU COUNT"
              value={gpus.length}
              detail={Boolean(snap?.has_cuda) ? "CUDA enabled" : Boolean(snap?.has_mps) ? "Apple MPS" : "None"}
            />
            <MetricCard label="VRAM FREE" value={`${(snap?.free_vram_gb as number ?? 0).toFixed(1)} GB`} detail="Across all GPUs" live />
            <MetricCard label="VRAM TOTAL" value={`${(snap?.total_vram_gb as number ?? 0).toFixed(1)} GB`} />
            <MetricCard label="RAM FREE" value={`${(snap?.ram_available_gb as number ?? 0).toFixed(1)} GB`} detail="System RAM" />
            <MetricCard label="CPU CORES" value={snap?.cpu_cores as number ?? 0} />
          </div>

          <div className="hw-grid">
            {gpus.map((g, i) => (
              <Panel key={i} title={`GPU ${g.index} — ${g.name}`}>
                <div className="gpu-panel-body">
                  <VramGauge
                    used={g.vram_used_mb as number}
                    total={g.vram_total_mb as number}
                    label={`GPU ${g.index}`}
                  />
                  <div className="gpu-stats">
                    <UtilBar value={g.utilization_pct as number} label="UTIL" />
                    <div className="gpu-stat-row">
                      <span className="gpu-stat-key">TEMP</span>
                      <span className={`gpu-stat-val ${(g.temperature_c as number) > 80 ? "hot" : ""}`}>
                        {g.temperature_c as number}°C
                      </span>
                    </div>
                    <div className="gpu-stat-row">
                      <span className="gpu-stat-key">POWER</span>
                      <span className="gpu-stat-val">{(g.power_draw_w as number).toFixed(0)} W</span>
                    </div>
                    <div className="gpu-stat-row">
                      <span className="gpu-stat-key">PRESSURE</span>
                      <span className={`gpu-stat-val pressure-${g.vram_pressure}`}>{String(g.vram_pressure).toUpperCase()}</span>
                    </div>
                    <div className="gpu-stat-row">
                      <span className="gpu-stat-key">VRAM FREE</span>
                      <span className="gpu-stat-val">{(g.vram_free_gb as number).toFixed(1)} GB</span>
                    </div>
                  </div>
                </div>
              </Panel>
            ))}
          </div>
        </>
      </DataState>

      <Panel title="Local Models — Fit Matrix" subtitle="Models that fit in current free VRAM, sorted by size.">
        <DataState
          loading={fitting.status === "loading"}
          error={fitting.error}
          empty={fittingModels.length === 0}
          emptyTitle="No local models fit"
          emptyBody="Insufficient free VRAM. API providers will be used."
        >
          <div className="fit-table-wrap">
            <table className="fit-table">
              <thead>
                <tr>
                  <th>PROVIDER</th>
                  <th>MODEL</th>
                  <th>FULL FP16</th>
                  <th>8-BIT</th>
                  <th>4-BIT</th>
                  <th>MIN RAM</th>
                </tr>
              </thead>
              <tbody>
                {fittingModels.map((m, i) => (
                  <tr key={i}>
                    <td className="mono">{String(m.provider)}</td>
                    <td className="mono">{String(m.model)}</td>
                    <td className="mono num">{m.vram_full_gb as number} GB</td>
                    <td className="mono num">{m.vram_8bit_gb as number} GB</td>
                    <td className="mono num">{m.vram_4bit_gb as number} GB</td>
                    <td className="mono num">{m.min_ram_gb as number} GB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </DataState>
      </Panel>
    </div>
  );
}
