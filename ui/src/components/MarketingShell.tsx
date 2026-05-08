import { Link, NavLink, Outlet } from "react-router-dom";
import { APP_PREFIX } from "../lib/routes";

const marketingLinks = [
  { to: "/", label: "Overview" },
  { to: "/try-xyntra", label: "Try Xyntra" },
  { to: "/pricing", label: "Pricing" },
  { to: "/how-it-works", label: "How It Works" },
  { to: "/demo", label: "Request Demo" },
];

export function MarketingShell() {
  return (
    <div className="marketing-shell">
      <header className="marketing-header">
        <Link className="marketing-brand" to="/">
          <span className="marketing-mark">X</span>
          <div className="marketing-brand-copy">
            <strong>Xyntra</strong>
            <small>Xyntra Control Plane for anything AI</small>
          </div>
        </Link>
        <nav className="marketing-nav">
          {marketingLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                isActive ? "marketing-nav-link active" : "marketing-nav-link"
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="marketing-actions">
          <a className="marketing-link-button" href={APP_PREFIX}>
            Open Console
          </a>
          <a className="marketing-primary-button" href="/demo">
            Request Demo
          </a>
        </div>
      </header>
      <main className="marketing-main">
        <Outlet />
      </main>
      <footer className="marketing-footer">
        <div className="marketing-footer-inner">
          <Link className="marketing-footer-home" to="/">
            Back to home
          </Link>
          <div className="marketing-footer-links">
            {marketingLinks.map((link) => (
              <Link key={link.to} to={link.to}>
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
