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
  provenanceTooltip?: string;
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
  { label: "Quant/Reports", path: "/portfolio/reports" },
  { label: "Copilot (Read-only)", path: "/portfolio/copilot" },
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
  provenanceTooltip,
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
        <div className="workspace-trust__row workspace-trust__row--primary">
          {freshnessTimestamp ? (
            <TimestampBadge value={freshnessTimestamp} />
          ) : (
            <span className="workspace-trust__token workspace-trust__token--neutral">
              Freshness: awaiting response
            </span>
          )}

          {periodLabel ? (
            <span className="workspace-trust__token">
              <span className="workspace-trust__key">Period</span>
              <span className="workspace-trust__value">{periodLabel}</span>
            </span>
          ) : null}
          {frequencyLabel ? (
            <span className="workspace-trust__token">
              <span className="workspace-trust__key">Frequency</span>
              <span className="workspace-trust__value">{frequencyLabel}</span>
            </span>
          ) : null}
          {timezoneLabel ? (
            <span className="workspace-trust__token">
              <span className="workspace-trust__key">Timezone</span>
              <span className="workspace-trust__value">{timezoneLabel}</span>
            </span>
          ) : null}
        </div>

        <div className="workspace-trust__row workspace-trust__row--secondary">
          <span className="workspace-trust__token workspace-trust__token--scope">
            <span className="workspace-trust__key">Scope</span>
            <span className="workspace-trust__value">{scopeLabel}</span>
          </span>

          <span
            aria-label="Data provenance"
            className="workspace-trust__token workspace-trust__token--provenance"
          >
            <span className="workspace-trust__key">Provenance</span>
            <span
              className="workspace-trust__value workspace-trust__value--truncate"
              title={provenanceTooltip || provenanceLabel}
            >
              {provenanceLabel}
            </span>
          </span>
        </div>
      </section>

      {children}
    </AppShell>
  );
}
