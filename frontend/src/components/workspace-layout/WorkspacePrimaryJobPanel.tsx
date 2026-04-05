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
};

export function WorkspacePrimaryJobPanel({
  routeLabel,
  jobTitle,
  jobDescription,
  decisionTags,
  coreTenMetrics,
  supplementary,
}: WorkspacePrimaryJobPanelProps) {
  return (
    <section className="panel workspace-primary-job">
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
              <strong>{metric.label}</strong>
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
