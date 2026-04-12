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
  children,
}: WorkspaceChartPanelProps) {
  const headingId = useId();
  const summaryId = useId();
  const panelClassName = className
    ? `panel workspace-chart-panel ${className}`
    : "panel workspace-chart-panel";

  return (
    <section
      aria-labelledby={headingId}
      aria-describedby={summaryId}
      className={panelClassName}
      data-module-priority={priority}
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
