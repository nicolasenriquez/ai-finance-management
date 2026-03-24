import type { ReactNode } from "react";

type ErrorBannerProps = {
  title: string;
  message: string;
  actions?: ReactNode;
  variant?: "error" | "warning";
};

export function ErrorBanner({
  title,
  message,
  actions,
  variant = "error",
}: ErrorBannerProps) {
  return (
    <section className={`status-banner status-banner--${variant}`} aria-live="polite">
      <h2 className="status-banner__title">{title}</h2>
      <p className="status-banner__copy">{message}</p>
      {actions ? <div className="status-banner__actions">{actions}</div> : null}
    </section>
  );
}
