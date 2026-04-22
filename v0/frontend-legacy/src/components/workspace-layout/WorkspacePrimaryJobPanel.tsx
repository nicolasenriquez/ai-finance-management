import type { ReactNode } from "react";

import type {
  CoreTenMetricCatalogEntry,
  PersonalFinanceDecisionTag,
} from "../../features/portfolio-workspace/core-ten-catalog";

type WorkspacePrimaryJobPanelProps = {
  routeLabel: string;
  jobTitle: string;
  jobDescription: string;
  decisionTags: PersonalFinanceDecisionTag[];
  coreTenMetrics: CoreTenMetricCatalogEntry[];
  supplementary?: ReactNode;
  metricValuesById?: Record<string, string>;
  questionKey?: string;
  widgetId?: string;
  hierarchy?: "hero" | "standard" | "utility";
  viewportRole?: "dominant-job" | "hero-insight" | "supporting-module";
};

export function WorkspacePrimaryJobPanel({
  routeLabel,
  jobTitle,
  jobDescription,
  decisionTags,
  coreTenMetrics,
  supplementary,
  metricValuesById,
  questionKey,
  widgetId,
  hierarchy = "hero",
  viewportRole = "dominant-job",
}: WorkspacePrimaryJobPanelProps) {
  return (
    <section
      className={`panel workspace-panel workspace-panel--${hierarchy} workspace-primary-job`}
      data-module-priority="primary"
      data-panel-hierarchy={hierarchy}
      data-first-viewport-role={viewportRole}
      data-question-key={questionKey}
      data-widget-id={widgetId}
    >
      <header className="panel__header workspace-primary-job__header">
        <div>
          <h2 className="panel__title">{jobTitle}</h2>
          <p className="panel__subtitle">
            {routeLabel} first-viewport analytical job with Core 10 interpretation
            priority.
          </p>
        </div>
      </header>

      <div className="panel__body workspace-primary-job__body">
        <p className="workspace-primary-job__description">{jobDescription}</p>

        <div className="workspace-primary-job__tokens">
          {decisionTags.map((decisionTag) => (
            <span className="workspace-primary-job__token" key={decisionTag}>
              {decisionTag}
            </span>
          ))}
        </div>

        <ul className="workspace-primary-job__core-list">
          {coreTenMetrics.map((metric) => (
            <li key={metric.metricId}>
              <div className="workspace-primary-job__metric-row">
                <strong>{metric.label}</strong>
                {metricValuesById?.[metric.metricId] ? (
                  <span className="workspace-primary-job__metric-value">
                    {metricValuesById[metric.metricId]}
                  </span>
                ) : null}
              </div>
              <p>{metric.interpretation}</p>
            </li>
          ))}
        </ul>

        {supplementary ? (
          <div className="workspace-primary-job__supplementary">
            {supplementary}
          </div>
        ) : null}
      </div>
    </section>
  );
}
