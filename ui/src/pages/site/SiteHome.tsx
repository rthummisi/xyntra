const proofPoints = [
  {
    label: "Recovery path",
    value: "< 1 routing decision",
    detail:
      "The control plane detects rate limits, retries responsibly, then hands execution to the next allowed model before the workflow stalls.",
  },
  {
    label: "State continuity",
    value: "Repo + session retained",
    detail:
      "Changed files, branch metadata, prior outputs, terminal transcripts, and task history stay attached across model handoffs.",
  },
  {
    label: "Operator control",
    value: "Developer-defined",
    detail:
      "Fallback chains, privacy rules, cost ceilings, and approval gates live in policy instead of being buried inside one model vendor.",
  },
];

const testimonialCards = [
  {
    quote:
      "The value is not just failover. It is that the coding session keeps its memory, cost posture, and audit trail when the worker model changes.",
    person: "Platform engineering lead",
    company: "Design partner profile",
  },
  {
    quote:
      "We do not want one AI vendor to become the operating system for development. Xyntra gives us the control layer back.",
    person: "CTO",
    company: "Security-first SaaS team",
  },
  {
    quote:
      "The model can change. The workflow should not. That is the difference between a toy assistant and infrastructure.",
    person: "Developer productivity manager",
    company: "Enterprise internal tools group",
  },
];

const comparisonRows = [
  {
    category: "Primary job",
    xyntra: "Keep coding workflows moving across providers, limits, and policy boundaries",
    copilots: "Help an individual developer write or edit code",
    gateways: "Route generic LLM requests across providers",
  },
  {
    category: "Model switching",
    xyntra: "Automatic, policy-aware, and stateful for coding sessions",
    copilots: "Limited model choice with product-owned orchestration",
    gateways: "Usually request-level fallback without coding continuity",
  },
  {
    category: "Repo continuity",
    xyntra: "Preserves repo context, changed files, session history, and artifacts",
    copilots: "Context exists, but routing logic is not developer-owned",
    gateways: "Usually outside repo-aware coding workflows",
  },
  {
    category: "Control plane owner",
    xyntra: "Developer or team defines the decision logic",
    copilots: "Vendor product plus admin policies",
    gateways: "Platform operator or infra layer",
  },
];

const featureCards = [
  {
    title: "Route around limits in real time",
    body:
      "When GPT throttles, Claude degrades, or a local model runs out of headroom, Xyntra reroutes the task instead of resetting the session.",
  },
  {
    title: "Keep the decision layer outside the model",
    body:
      "The mind of the system lives in the control plane. Models remain replaceable execution workers, which makes vendor switching operationally safe.",
  },
  {
    title: "Turn AI usage into an inspectable system",
    body:
      "Replay, approvals, spend logs, routing traces, artifacts, and policy reasons stay visible so engineering teams can govern adoption without slowing it down.",
  },
];

export default function SiteHome() {
  return (
    <div className="marketing-page">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="marketing-eyebrow">Developer-owned orchestration</p>
          <h1>Never let one model vendor become the operating system for coding.</h1>
          <p className="hero-lead">
            Xyntra is the control plane that keeps coding work moving when models
            rate-limit, fail, get expensive, or violate policy. It routes
            execution across providers while preserving project continuity, audit
            visibility, and developer authority.
          </p>
          <div className="hero-actions">
            <a className="marketing-primary-button" href="/demo">
              Request Demo
            </a>
            <a className="marketing-secondary-button" href="/pricing">
              View Pricing
            </a>
          </div>
          <div className="hero-subproof">
            <span>Local-first</span>
            <span>Policy-aware</span>
            <span>Repo-aware</span>
            <span>Model-swappable</span>
          </div>
        </div>
        <aside className="hero-console">
          <div className="console-window">
            <div className="console-dots">
              <span />
              <span />
              <span />
            </div>
            <pre>{`xyntra exec "repair failing integration tests"

[route] primary=openai/gpt-5-coder
[event] 429 rate limit detected
[policy] hosted fallback allowed
[fallback] anthropic/claude-sonnet selected
[state] repo context retained
[state] changed files retained
[state] session memory retained
[result] patch generated and tests rerun`}</pre>
          </div>
          <div className="hero-note">
            <strong>What changes:</strong>
            <p>
              The worker model. Not the task, not the state, and not the control
              logic.
            </p>
          </div>
        </aside>
      </section>

      <section className="marketing-metrics">
        {proofPoints.map((point) => (
          <article className="marketing-metric" key={point.label}>
            <span>{point.label}</span>
            <strong>{point.value}</strong>
            <p>{point.detail}</p>
          </article>
        ))}
      </section>

      <section className="story-grid">
        <div className="story-copy">
          <p className="marketing-eyebrow">Why this exists</p>
          <h2>Copilots optimize for interaction. Gateways optimize for requests. Xyntra optimizes for coding continuity.</h2>
          <p>
            Engineering teams do not just need “another model.” They need a way to
            keep delivery moving when providers rate-limit, cost changes spike, or
            privacy rules force a route change mid-stream.
          </p>
          <ul className="marketing-list">
            <li>Route by task type, latency, cost, and privacy rules</li>
            <li>Keep the same repo session alive across model handoffs</li>
            <li>Expose the full routing trail for audit and replay</li>
            <li>Let the team own the orchestration logic instead of one vendor</li>
          </ul>
        </div>
        <div className="marketing-card-stack">
          {featureCards.map((card) => (
            <article className="marketing-card" key={card.title}>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="comparison-section">
        <div className="section-header compact">
          <p className="marketing-eyebrow">Competitive frame</p>
          <h2>Different from copilots. Different from gateways.</h2>
          <p className="section-lead">
            Xyntra sits between coding agents and model providers. It owns
            continuity, policy, and switching decisions so the team does not lose
            control when the backend model changes.
          </p>
        </div>
        <div className="comparison-table-wrap">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Xyntra</th>
                <th>Copilot / Cursor class</th>
                <th>AI gateway class</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row) => (
                <tr key={row.category}>
                  <td>{row.category}</td>
                  <td>{row.xyntra}</td>
                  <td>{row.copilots}</td>
                  <td>{row.gateways}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="testimonials-section">
        <div className="section-header compact">
          <p className="marketing-eyebrow">Proof direction</p>
          <h2>Use these blocks as placeholders for design-partner proof.</h2>
        </div>
        <div className="pricing-grid">
          {testimonialCards.map((card) => (
            <article className="testimonial-card" key={card.quote}>
              <p className="testimonial-quote">“{card.quote}”</p>
              <div className="testimonial-meta">
                <strong>{card.person}</strong>
                <span>{card.company}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="callout-band">
        <div>
          <p className="marketing-eyebrow">Next step</p>
          <h2>Show the control plane, then sell the continuity.</h2>
        </div>
        <div className="callout-actions">
          <p>
            The strongest demo is simple: start a coding task, hit a rate limit,
            switch models automatically, and finish without losing the session.
          </p>
          <div className="hero-actions">
            <a className="marketing-primary-button" href="/demo">
              Book a walkthrough
            </a>
            <a className="marketing-secondary-button" href="/how-it-works">
              See the architecture
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
