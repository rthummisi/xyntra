import { FormEvent, useEffect, useState } from "react";
import {
  presetInput,
  simulateRoutingDecision,
  type SimulationPreset,
} from "../../lib/routingSimulator";

const STORAGE_KEY = "xyntra-demo-leads";

type Lead = {
  name: string;
  email: string;
  company: string;
  teamSize: string;
  notes: string;
};

const demoScripts: Record<
  SimulationPreset,
  { title: string; steps: string[]; close: string }
> = {
  "rate-limit-recovery": {
    title: "Demo flow: recover from a provider limit without losing the task",
    steps: [
      "Start with OpenAI as the preferred worker for a live coding request.",
      "Inject a rate-limit event and show the circuit breaker exclude the provider.",
      "Show Xyntra preserve session, repo, and changed-file continuity during handoff.",
      "Land on the selected fallback model and finish the same task with replay evidence.",
    ],
    close:
      "This proves the workflow survives a provider incident without a session reset.",
  },
  "local-private-repair": {
    title: "Demo flow: keep a sensitive repair entirely on the local machine",
    steps: [
      "Flag the request as local_only and containing sensitive project data.",
      "Show hosted providers disappear at policy check time before execution begins.",
      "Demonstrate that only Ollama-backed candidates remain eligible.",
      "Close on the privacy guarantee: no hosted route is even considered.",
    ],
    close:
      "This proves privacy is enforced as a control-plane guarantee, not a best-effort hint.",
  },
  "vision-fallback": {
    title: "Demo flow: rescue a multimodal request during a provider outage",
    steps: [
      "Use a screenshot or PDF-style request that requires vision capability.",
      "Mark the preferred provider as degraded to simulate a real outage.",
      "Show capability filtering and circuit-breaker logic narrow the pool.",
      "Finish on the next eligible vision model and review the decision trail.",
    ],
    close:
      "This proves routing remains capability-aware even under failure pressure.",
  },
};

export default function SiteDemo() {
  const [preset, setPreset] = useState<SimulationPreset>("rate-limit-recovery");
  const [lead, setLead] = useState<Lead>({
    name: "",
    email: "",
    company: "",
    teamSize: "",
    notes: "",
  });
  const [submitted, setSubmitted] = useState(false);
  const [savedCount, setSavedCount] = useState(0);

  const decision = simulateRoutingDecision(presetInput(preset), preset);
  const script = demoScripts[preset];

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      setSavedCount(0);
      return;
    }
    try {
      const parsed = JSON.parse(stored) as Lead[];
      setSavedCount(parsed.length);
    } catch {
      setSavedCount(0);
    }
  }, [submitted]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const stored = localStorage.getItem(STORAGE_KEY);
    const existing = stored ? ((JSON.parse(stored) as Lead[]) ?? []) : [];
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...existing, lead], null, 2));
    setSubmitted(true);
    setLead({
      name: "",
      email: "",
      company: "",
      teamSize: "",
      notes: "",
    });
  }

  return (
    <div className="marketing-page">
      <section className="section-header">
        <p className="marketing-eyebrow">Interactive demo</p>
        <h1>Show the control plane before you ask for the meeting.</h1>
        <p className="section-lead">
          This page now doubles as a lightweight proof environment. Pick a
          failure or policy scenario, inspect the simulated route, then use the
          talk track to run a live product walkthrough.
        </p>
      </section>

      <section className="pricing-grid">
        {(
          [
            ["rate-limit-recovery", "Rate-limit recovery"],
            ["local-private-repair", "Local-only repair"],
            ["vision-fallback", "Vision fallback"],
          ] as Array<[SimulationPreset, string]>
        ).map(([value, label]) => (
          <button
            key={value}
            className={
              value === preset
                ? "marketing-primary-button"
                : "marketing-secondary-button"
            }
            onClick={() => setPreset(value)}
            type="button"
            style={{ textAlign: "left" }}
          >
            {label}
          </button>
        ))}
      </section>

      <section className="pricing-bottom-grid">
        <div className="principles-column">
          <article className="marketing-card emphasis">
            <p className="marketing-eyebrow">Selected route</p>
            <h3>
              {decision.selected.provider}/{decision.selected.model}
            </h3>
            <p>{decision.summary}</p>
            <ul className="marketing-list">
              <li>Strategy: {presetInput(preset).strategy}</li>
              <li>Blocked providers: {decision.blockedProviders.join(", ") || "none"}</li>
              <li>
                Fallback chain:{" "}
                {decision.fallbackChain
                  .map((candidate) => `${candidate.provider}/${candidate.model}`)
                  .join(" -> ") || "none"}
              </li>
            </ul>
          </article>

          <article className="marketing-card">
            <p className="marketing-eyebrow">Decision trail</p>
            <ul className="marketing-list">
              {decision.reasoning.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        </div>

        <div className="principles-column">
          <article className="marketing-card">
            <p className="marketing-eyebrow">Demo talk track</p>
            <h3>{script.title}</h3>
            <ul className="marketing-list">
              {script.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
            <p>{script.close}</p>
          </article>

          <article className="marketing-card">
            <p className="marketing-eyebrow">What to open during the live demo</p>
            <ul className="marketing-list">
              <li>`/app/routing-decision` for simulation and live route output</li>
              <li>`/app/replay` to prove the execution trail survives failures</li>
              <li>`/app/spend-analytics` to show policy and cost consequences</li>
              <li>`/app/policies` to anchor privacy and approval guarantees</li>
            </ul>
          </article>
        </div>
      </section>

      <section className="pricing-bottom-grid">
        <form className="marketing-form-card" onSubmit={handleSubmit}>
          <p className="marketing-eyebrow">Request demo</p>
          <h3 style={{ margin: 0 }}>Capture interest after the simulator lands.</h3>
          <label>
            Name
            <input
              value={lead.name}
              onChange={(event) =>
                setLead((current) => ({ ...current, name: event.target.value }))
              }
              placeholder="Your name"
              required
            />
          </label>
          <label>
            Work email
            <input
              type="email"
              value={lead.email}
              onChange={(event) =>
                setLead((current) => ({ ...current, email: event.target.value }))
              }
              placeholder="you@company.com"
              required
            />
          </label>
          <label>
            Company
            <input
              value={lead.company}
              onChange={(event) =>
                setLead((current) => ({ ...current, company: event.target.value }))
              }
              placeholder="Company name"
              required
            />
          </label>
          <label>
            Team size
            <select
              value={lead.teamSize}
              onChange={(event) =>
                setLead((current) => ({ ...current, teamSize: event.target.value }))
              }
              required
            >
              <option value="">Select team size</option>
              <option value="1-5">1-5</option>
              <option value="6-20">6-20</option>
              <option value="21-100">21-100</option>
              <option value="100+">100+</option>
            </select>
          </label>
          <label>
            What scenario matters most?
            <textarea
              rows={5}
              value={lead.notes}
              onChange={(event) =>
                setLead((current) => ({ ...current, notes: event.target.value }))
              }
              placeholder="Rate limits, local-only privacy, vision fallback, budget enforcement..."
              required
            />
          </label>
          <button className="marketing-primary-button" type="submit">
            Save local demo request
          </button>
          {submitted ? (
            <p className="form-success">
              Saved locally. This preview now has {savedCount + 1} captured
              request{savedCount === 0 ? "" : "s"} in your browser.
            </p>
          ) : null}
        </form>

        <div className="principles-column">
          <article className="marketing-card emphasis">
            <p className="marketing-eyebrow">Why this update matters</p>
            <h3>The site can now explain Xyntra before the operator touches the console.</h3>
            <p>
              The old page only captured contact intent. This version sells the
              product with a visible route decision, a failure scenario, and a
              concrete demo script.
            </p>
          </article>
          <article className="marketing-card">
            <p className="marketing-eyebrow">Production next step</p>
            <p>
              Replace the local-storage form with a backend POST target and wire
              the scenario picker to saved playbooks or real telemetry snapshots.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
