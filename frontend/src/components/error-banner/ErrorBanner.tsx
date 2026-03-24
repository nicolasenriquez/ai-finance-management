import {
  useId,
  type ReactNode,
} from "react";

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
  const titleId = useId();
  const semanticRole = variant === "error" ? "alert" : "status";
  const liveMode = variant === "error" ? "assertive" : "polite";

  return (
    <section
      aria-labelledby={titleId}
      aria-live={liveMode}
      className={`status-banner status-banner--${variant}`}
      role={semanticRole}
    >
      <h2 className="status-banner__title" id={titleId}>
        {title}
      </h2>
      <p className="status-banner__copy">{message}</p>
      {actions ? <div className="status-banner__actions">{actions}</div> : null}
    </section>
  );
}
