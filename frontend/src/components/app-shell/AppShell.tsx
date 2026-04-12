import type { PropsWithChildren, ReactNode } from "react";
import { Link } from "react-router-dom";

import { ThemeToggle } from "../theme-toggle/ThemeToggle";

type AppShellProps = PropsWithChildren<{
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  headerVariant?: "default" | "chat";
}>;

export function AppShell({
  eyebrow,
  title,
  description,
  actions,
  headerVariant = "default",
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
        <header
          className={
            headerVariant === "chat"
              ? "panel route-frame route-frame--chat"
              : "panel route-frame"
          }
        >
          <div className="route-frame__body">
            <div className="route-frame__meta">
              <span className="eyebrow">{eyebrow}</span>
            </div>
            <div className="route-frame__copy">
              <h1 className="route-frame__title">{title}</h1>
              <p className="route-frame__description">{description}</p>
            </div>
          </div>
          {actions ? <div className="route-frame__actions">{actions}</div> : null}
        </header>
        <div className="page-grid">{children}</div>
      </div>
    </main>
  );
}
