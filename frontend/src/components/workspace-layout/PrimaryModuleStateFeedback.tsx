import {
  resolveRoutePrimaryModuleFeedback,
  type RoutePrimaryModuleState,
} from "../../features/portfolio-workspace/route-module-state";

type PrimaryModuleStateFeedbackProps = {
  moduleState: RoutePrimaryModuleState;
  onRetryModuleLoad?: () => void;
};

export function PrimaryModuleStateFeedback({
  moduleState,
  onRetryModuleLoad,
}: PrimaryModuleStateFeedbackProps) {
  const moduleFeedback = resolveRoutePrimaryModuleFeedback(moduleState);
  if (moduleFeedback === null) {
    return null;
  }

  return (
    <section
      className={`primary-module-state-feedback primary-module-state-feedback--${moduleFeedback.tone}`}
      data-module-state={moduleState}
      role="status"
      aria-live="polite"
    >
      <p className="primary-module-state-feedback__message">{moduleFeedback.message}</p>
      <p className="primary-module-state-feedback__state">Module state: {moduleState}</p>
      {moduleFeedback.isRetryable && onRetryModuleLoad ? (
        <button
          className="primary-module-state-feedback__retry"
          onClick={onRetryModuleLoad}
          type="button"
        >
          Retry module load
        </button>
      ) : null}
    </section>
  );
}
