import {
  formatDateTimeLabel,
  formatUtcDateTimeLabel,
} from "../../core/lib/dates";

type TimestampBadgeProps = {
  value: string;
};

export function TimestampBadge({ value }: TimestampBadgeProps) {
  return (
    <span className="timestamp-badge" title={`UTC ${formatUtcDateTimeLabel(value)}`}>
      <span className="timestamp-badge__label">Ledger as of</span>
      <strong className="timestamp-badge__value">{formatDateTimeLabel(value)}</strong>
    </span>
  );
}
