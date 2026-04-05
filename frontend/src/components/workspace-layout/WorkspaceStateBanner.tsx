import {
  resolveWorkspaceLifecycleCopy,
  type WorkspaceLifecycleState,
} from "../../features/portfolio-workspace/state-copy";

type WorkspaceStateBannerProps = {
  state: WorkspaceLifecycleState;
  message?: string;
};

export function WorkspaceStateBanner({ state, message }: WorkspaceStateBannerProps) {
  const lifecycleCopy = resolveWorkspaceLifecycleCopy(state, message);
  return (
    <section
      className={`panel workspace-state-banner workspace-state-banner--${lifecycleCopy.tone}`}
      role="status"
      aria-live="polite"
    >
      <strong>{lifecycleCopy.title}</strong>
      <p>{lifecycleCopy.message}</p>
    </section>
  );
}
