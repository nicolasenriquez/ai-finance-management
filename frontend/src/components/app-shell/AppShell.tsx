import type { PropsWithChildren, ReactNode } from "react";
import { Link } from "react-router-dom";

import { ThemeToggle } from "../theme-toggle/ThemeToggle";

type AppShellProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}>;

export function AppShell({
  eyebrow,
  title,
  description,
  actions,
  children,
}: AppShellProps) {
  return (
    <main className="app-shell">
      <div className="app-shell__backdrop" aria-hidden="true" />
      <div className="app-shell__frame">
        <header className="app-shell__masthead">
          <Link
            aria-label="Open portfolio summary"
            className="brand-mark"
            to="/portfolio"
          >
            <span className="brand-mark__eyebrow">AI Finance Management</span>
            <strong className="brand-mark__title">Portfolio ledger workspace</strong>
          </Link>
          <ThemeToggle />
        </header>
        <header className="app-shell__hero panel panel--hero">
          <div className="hero-copy-block">
            <span className="eyebrow">{eyebrow}</span>
            <h1 className="hero-title">{title}</h1>
            <p className="hero-copy">{description}</p>
          </div>
          <div className="hero-meta">
            <div className="hero-meta__card">
              <span className="hero-meta__label">Source posture</span>
              <strong className="hero-meta__value">Ledger-backed and read only</strong>
              <p className="hero-meta__copy">
                Every visible metric comes from persisted accounting state. Unsupported
                market-value and FX-sensitive analytics remain out of scope.
              </p>
            </div>
            <div className="hero-meta__card hero-meta__card--subtle">
              <span className="hero-meta__label">UX baseline</span>
              <strong className="hero-meta__value">Accessible by default</strong>
              <p className="hero-meta__copy">
                Focus visibility, reduced motion, responsive tables, and explicit error
                states are treated as release requirements.
              </p>
            </div>
            {actions ? <div className="hero-actions">{actions}</div> : null}
          </div>
        </header>
        <div className="page-grid">{children}</div>
      </div>
    </main>
  );
}
