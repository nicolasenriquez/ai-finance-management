type LoadingTableSkeletonProps = {
  rows?: number;
};

export function LoadingTableSkeleton({
  rows = 5,
}: LoadingTableSkeletonProps) {
  return (
    <div className="skeleton-table" aria-hidden="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="skeleton-row" />
      ))}
    </div>
  );
}
