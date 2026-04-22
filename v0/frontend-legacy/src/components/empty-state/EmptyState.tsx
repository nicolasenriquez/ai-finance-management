import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  message: string;
  actions?: ReactNode;
};

export function EmptyState({ title, message, actions }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <h2 className="empty-state__title">{title}</h2>
      <p className="empty-state__copy">{message}</p>
      {actions ? <div className="empty-state__actions">{actions}</div> : null}
    </section>
  );
}
