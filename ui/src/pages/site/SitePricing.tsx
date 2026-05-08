const plans = [
  {
    name: "Starter",
    price: "$0",
    cadence: "forever",
    summary: "Single-user local control plane for validating the workflow.",
    features: [
      "Local-only routing and Ollama support",
      "CLI chat, exec, and test flows",
      "Basic fallback chains and session memory",
      "Marketing-site and console preview",
    ],
  },
  {
    name: "Pro",
    price: "$39",
    cadence: "per user / month",
    summary: "For power users who want routing control without enterprise overhead.",
    features: [
      "Advanced routing and fallback policies",
      "Prompt templates and model comparison",
      "Execution replay and richer analytics",
      "Priority access to new workflow features",
    ],
    featured: true,
  },
  {
    name: "Team",
    price: "$99",
    cadence: "per active user / month",
    summary: "For engineering teams standardizing coding workflows under one control plane.",
    features: [
      "Shared workspaces and provider catalogs",
      "Approvals, audit trails, and policy scopes",
      "Budget controls and spend analytics",
      "Webhook integrations and admin tooling",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    cadence: "annual contract",
    summary: "For regulated teams that need governance, deployment flexibility, and support.",
    features: [
      "SSO, SCIM, and role-based governance",
      "Self-hosted, VPC, or managed deployment",
      "Compliance exports and retention controls",
      "Onboarding, support, and custom policy packs",
    ],
  },
];

const pricingPrinciples = [
  "Charge for continuity, governance, and vendor independence.",
  "Do not compete on raw model resale alone.",
  "Keep BYOK available for enterprise buyers.",
  "Use managed usage only as an optional expansion path.",
];

const faq = [
  {
    question: "Why not just price Xyntra like a coding assistant seat?",
    answer:
      "Because the strongest value is not autocomplete. It is keeping engineering workflows alive across rate limits, outages, cost swings, and policy constraints.",
  },
  {
    question: "Why include a free tier at all?",
    answer:
      "Adoption starts with developers proving the workflow locally. The commercial expansion comes when teams want shared control, governance, and billing.",
  },
  {
    question: "What should enterprise buyers actually pay for?",
    answer:
      "SSO, policy scopes, self-hosted deployment, audit exports, chargeback visibility, and admin-grade routing control.",
  },
];

export default function SitePricing() {
  return (
    <div className="marketing-page">
      <section className="section-header">
        <p className="marketing-eyebrow">Pricing direction</p>
        <h1>Price the continuity layer, not the worker model.</h1>
        <p className="section-lead">
          Xyntra becomes commercially defensible when teams pay for routing
          policy, state continuity, governance, and vendor independence. Model
          inference is an input. The control plane is the product.
        </p>
      </section>

      <section className="pricing-grid">
        {plans.map((plan) => (
          <article
            className={`pricing-card ${plan.featured ? "featured" : ""}`}
            key={plan.name}
          >
            <div className="pricing-header">
              <p>{plan.name}</p>
              <h2>{plan.price}</h2>
              <span>{plan.cadence}</span>
            </div>
            <p className="pricing-summary">{plan.summary}</p>
            <ul className="marketing-list">
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            <div className="pricing-cta">
              <a
                className={
                  plan.featured
                    ? "marketing-primary-button"
                    : "marketing-secondary-button"
                }
                href="/demo"
              >
                {plan.name === "Enterprise" ? "Talk to us" : "Request access"}
              </a>
            </div>
          </article>
        ))}
      </section>

      <section className="pricing-bottom-grid">
        <article className="marketing-card emphasis">
          <p className="marketing-eyebrow">Monetization logic</p>
          <h3>The buyer is paying to avoid workflow collapse.</h3>
          <p>
            When a model rate-limits mid-task, the alternative is not “use a
            different model later.” The real alternative is stalled work, manual
            context rebuild, and engineering time lost. That is the budget line
            Xyntra should target.
          </p>
        </article>
        <article className="marketing-card">
          <p className="marketing-eyebrow">Packaging principles</p>
          <ul className="marketing-list">
            {pricingPrinciples.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="faq-grid">
        {faq.map((item) => (
          <article className="marketing-card" key={item.question}>
            <h3>{item.question}</h3>
            <p>{item.answer}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
