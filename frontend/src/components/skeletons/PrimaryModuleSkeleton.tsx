type PrimaryModuleSkeletonProps = {
  label: string;
  rowCount?: number;
};

export function PrimaryModuleSkeleton({
  label,
  rowCount = 4,
}: PrimaryModuleSkeletonProps) {
  const rows = Array.from({ length: rowCount }, (_, index) => `${label}-row-${index + 1}`);

  return (
    <article
      aria-label={`${label} loading skeleton`}
      className="primary-module-skeleton"
      data-loading-contract="primary-module"
      data-skeleton-height-token="module-height-compact"
      data-testid="primary-module-skeleton"
    >
      <div className="primary-module-skeleton__title" />
      <div className="primary-module-skeleton__kicker" />
      <div className="primary-module-skeleton__rows" aria-hidden="true">
        {rows.map((rowKey) => (
          <div key={rowKey} className="primary-module-skeleton__row" />
        ))}
      </div>
    </article>
  );
}
