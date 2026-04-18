import type {
  PropsWithChildren,
  ReactNode,
} from "react";
import { useId } from "react";

type WorkspaceChartPanelProps = PropsWithChildren<{
  title: string;
  subtitle: string;
  shortDescription: string;
  longDescription: string;
  actions?: ReactNode;
  className?: string;
  widgetId?: string;
  questionKey?: string;
  priority?: "primary" | "advanced";
  hierarchy?: "hero" | "standard" | "utility";
  viewportRole?: "dominant-job" | "hero-insight" | "supporting-module";
}>;

export function WorkspaceChartPanel({
  title,
  subtitle,
  shortDescription,
  longDescription,
  actions,
  className,
  widgetId,
  questionKey,
  priority = "primary",
  hierarchy,
  viewportRole = "supporting-module",
  children,
}: WorkspaceChartPanelProps) {
  const headingId = useId();
  const summaryId = useId();
  const resolvedHierarchy = hierarchy ?? (priority === "advanced" ? "utility" : "standard");
  const panelClassName = className
    ? `panel workspace-panel workspace-panel--${resolvedHierarchy} workspace-chart-panel ${className}`
    : `panel workspace-panel workspace-panel--${resolvedHierarchy} workspace-chart-panel`;

  return (
    <section
      aria-labelledby={headingId}
      aria-describedby={summaryId}
      className={panelClassName}
      data-module-priority={priority}
      data-panel-hierarchy={resolvedHierarchy}
      data-first-viewport-role={viewportRole}
      data-question-key={questionKey}
      data-widget-id={widgetId}
    >
      <header className="panel__header workspace-chart-panel__header">
        <div>
          <h2 className="panel__title" id={headingId}>
            {title}
          </h2>
          <p className="panel__subtitle">{subtitle}</p>
        </div>
        {actions ? <div className="workspace-chart-panel__actions">{actions}</div> : null}
      </header>
      <div className="panel__body workspace-chart-panel__body">
        <p className="workspace-chart-panel__summary" id={summaryId}>
          {shortDescription}
        </p>
        <details className="workspace-chart-panel__details">
          <summary>Read chart interpretation details</summary>
          <p>{longDescription}</p>
        </details>
        <div className="workspace-chart-panel__content">{children}</div>
      </div>
    </section>
  );
}
