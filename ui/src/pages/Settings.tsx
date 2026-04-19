import { Panel } from "../components/Chrome";
import { SurfacePage } from "../components/SurfaceTemplates";
import { API_BASE } from "../lib/api";

export default function Settings() {
  return (
    <SurfacePage
      title="Settings"
      description="Frontend runtime defaults and local environment targets."
      kicker="Phase 24 • F-23"
      primary={
        <Panel title="UI Runtime" subtitle="Frontend-to-backend connectivity defaults.">
          <ul className="plain-list">
            <li>API base URL: {API_BASE}</li>
            <li>Expected local API port: 18000</li>
            <li>Expected local UI port: 4173</li>
            <li>Ollama host port: 21434</li>
          </ul>
        </Panel>
      }
      secondary={
        <Panel title="Provider & Ollama Controls" subtitle="Dedicated settings APIs are not exposed yet.">
          <p className="muted">
            Provider key management and Ollama model provisioning are implemented operationally in the backend and container runtime. This page currently exposes the environment assumptions the UI uses.
          </p>
        </Panel>
      }
    />
  );
}
