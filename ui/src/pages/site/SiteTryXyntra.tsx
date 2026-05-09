const trySteps = [
  {
    title: "1. Launch the public site",
    body: "Run `xyntra web` to open the marketing site, then jump into the console from the header when you want to move from messaging to product.",
  },
  {
    title: "2. Open the control plane",
    body: "Use the `Open Console` button or go directly to `/app` to access the operational surfaces, live routing views, and task controls.",
  },
  {
    title: "3. Exercise the CLI",
    body: "Try `xyntra`, `xyntra run`, `xyntra exec`, and `xyntra test` so you can see how repo-aware context and session continuity behave outside the browser.",
  },
  {
    title: "4. Simulate the moat",
    body: "Demonstrate the real wedge: start a coding task, force a limit or policy change, and watch Xyntra hand work to a different model without losing state.",
  },
];

const commands = [
  "xyntra web",
  "xyntra web pricing",
  "xyntra validate-contract ./SPEC.md --major-version 1 --kimi-model <kimi-model>",
  "xyntra",
  "xyntra run \"Summarize this repo\"",
  "xyntra exec pwd",
  "xyntra test",
];

export default function SiteTryXyntra() {
  return (
    <div className="marketing-page">
      <section className="section-header">
        <p className="marketing-eyebrow">Try Xyntra</p>
        <h1>See the control plane before you believe the pitch.</h1>
        <p className="section-lead">
          This page turns the local build into a guided trial. It is designed for
          founders, prospects, and design partners who want to move from message
          to product in under five minutes.
        </p>
      </section>

      <section className="pricing-bottom-grid">
        <div className="timeline-column try-column">
          {trySteps.map((step) => (
            <article className="timeline-step" key={step.title}>
              <h2>{step.title}</h2>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
        <div className="principles-column">
          <article className="marketing-card emphasis">
            <p className="marketing-eyebrow">Recommended path</p>
            <h3>Lead the trial with switching under pressure.</h3>
            <p>
              The fastest way to make Xyntra legible is to show a task continue
              after a provider limit or policy boundary would normally interrupt
              it.
            </p>
          </article>
          <article className="marketing-card">
            <p className="marketing-eyebrow">Starter commands</p>
            <pre className="marketing-code-block">{commands.join("\n")}</pre>
          </article>
        </div>
      </section>
    </div>
  );
}
