import type { PropsWithChildren, ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { AppShell } from "../app-shell/AppShell";
import { TimestampBadge } from "../timestamp-badge/TimestampBadge";

type PortfolioWorkspaceLayoutProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  freshnessTimestamp?: string;
  scopeLabel: string;
  provenanceLabel: string;
  periodLabel?: string;
  frequencyLabel?: string;
  timezoneLabel?: string;
}>;

type WorkspaceRoute = {
  label: string;
  path: string;
};

const WORKSPACE_ROUTES: WorkspaceRoute[] = [
  { label: "Home", path: "/portfolio/home" },
  { label: "Analytics (Preview)", path: "/portfolio/analytics" },
  { label: "Risk (Interpretation)", path: "/portfolio/risk" },
  { label: "Transactions", path: "/portfolio/transactions" },
];

export function PortfolioWorkspaceLayout({
  eyebrow,
  title,
  description,
  actions,
  freshnessTimestamp,
  scopeLabel,
  provenanceLabel,
  periodLabel,
  frequencyLabel,
  timezoneLabel,
  children,
}: PortfolioWorkspaceLayoutProps) {
  return (
    <AppShell
      eyebrow={eyebrow}
      title={title}
      description={description}
      actions={actions}
    >
      <nav
        className="panel workspace-nav"
        aria-label="Portfolio analytics workspace navigation"
      >
        <ul className="workspace-nav__list">
          {WORKSPACE_ROUTES.map((route) => (
            <li key={route.path}>
              <NavLink
                to={route.path}
                className={({ isActive }) =>
                  isActive
                    ? "workspace-nav__link workspace-nav__link--active"
                    : "workspace-nav__link"
                }
              >
                {route.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <section className="panel workspace-trust" aria-label="Data trust context">
        <div className="workspace-trust__items">
          {freshnessTimestamp ? (
            <TimestampBadge value={freshnessTimestamp} />
          ) : (
            <span className="status-pill status-pill--neutral">
              Freshness: awaiting response
            </span>
          )}
          <span className="status-pill status-pill--neutral">Scope: {scopeLabel}</span>
          <span className="status-pill status-pill--neutral">
            Provenance: {provenanceLabel}
          </span>
          {periodLabel ? (
            <span className="status-pill status-pill--neutral">Period: {periodLabel}</span>
          ) : null}
          {frequencyLabel ? (
            <span className="status-pill status-pill--neutral">
              Frequency: {frequencyLabel}
            </span>
          ) : null}
          {timezoneLabel ? (
            <span className="status-pill status-pill--neutral">Timezone: {timezoneLabel}</span>
          ) : null}
        </div>
      </section>

      {children}
    </AppShell>
  );
}
