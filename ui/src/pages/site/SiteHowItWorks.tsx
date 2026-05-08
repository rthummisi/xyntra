const steps = [
  {
    title: "1. Define the control contract",
    body:
      "The team sets routing preferences, privacy rules, fallback chains, approval gates, and budget ceilings at the control-plane layer before a task starts.",
  },
  {
    title: "2. Start the coding task with real context",
    body:
      "Repo root, changed files, project memory, prior session outputs, and terminal execution history are assembled so the task begins with usable state, not a blank prompt.",
  },
  {
    title: "3. Watch for failures and policy boundaries",
    body:
      "If the selected model hits a 429, times out, breaches latency, or violates a routing rule, Xyntra catches the event before the coding workflow breaks.",
  },
  {
    title: "4. Hand work to the next allowed worker",
    body:
      "The control plane switches the backend model while preserving task history, context, and metadata so the next worker continues the same job rather than starting over.",
  },
  {
    title: "5. Record the entire decision trail",
    body:
      "Routing choice, fallback reason, provider call, cost record, artifact, and replay state remain visible for debugging, audit, and operator trust.",
  },
];

const principles = [
  "The control plane should stay authoritative even when the model changes.",
  "A provider outage is a routing event, not a workflow-ending event.",
  "The developer or team owns the rules of execution.",
  "State continuity matters more than one-off model performance.",
];

export default function SiteHowItWorks() {
  return (
    <div className="marketing-page">
      <section className="section-header">
        <p className="marketing-eyebrow">How it works</p>
        <h1>Keep the mind in the control plane and the models as workers.</h1>
        <p className="section-lead">
          Xyntra separates orchestration from execution. That means a model can
          change in the middle of a coding workflow without changing the system’s
          governing logic, visibility, or policy posture.
        </p>
      </section>

      <section className="timeline-grid">
        <div className="timeline-column">
          {steps.map((step) => (
            <article className="timeline-step" key={step.title}>
              <h2>{step.title}</h2>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
        <aside className="principles-column">
          <div className="marketing-card emphasis">
            <p className="marketing-eyebrow">Operating doctrine</p>
            <h3>The control plane should not lose authority when the backend worker changes.</h3>
            <ul className="marketing-list">
              {principles.map((principle) => (
                <li key={principle}>{principle}</li>
              ))}
            </ul>
          </div>
          <div className="marketing-card">
            <p className="marketing-eyebrow">Example model handoff</p>
            <pre className="marketing-code-block">{`task: "repair failing integration suite"
preferred: gpt-5-coder
event: provider returned 429
policy: hosted fallback allowed
fallback: claude-sonnet selected
continuity: repo + session + artifacts retained
outcome: patch completed, tests rerun, replay stored`}</pre>
          </div>
        </aside>
      </section>
    </div>
  );
}
