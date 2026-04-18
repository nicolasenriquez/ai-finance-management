import {
  resolveWorkspaceLifecycleCopy,
  type WorkspaceLifecycleState,
} from "../../features/portfolio-workspace/state-copy";

type WorkspaceStateBannerProps = {
  state: WorkspaceLifecycleState;
  message?: string;
  hierarchy?: "hero" | "standard" | "utility";
};

export function WorkspaceStateBanner({
  state,
  message,
  hierarchy = "utility",
}: WorkspaceStateBannerProps) {
  const lifecycleCopy = resolveWorkspaceLifecycleCopy(state, message);
  return (
    <section
      className={`panel workspace-panel workspace-panel--${hierarchy} workspace-state-banner workspace-state-banner--${lifecycleCopy.tone}`}
      data-lifecycle-state={state}
      data-panel-hierarchy={hierarchy}
      role="status"
      aria-live="polite"
    >
      <strong>{lifecycleCopy.title}</strong>
      <p>{lifecycleCopy.message}</p>
    </section>
  );
}
