type StoryContractBlockProps = {
  what: string;
  why: string;
  action: string;
  evidence: string;
};

type StoryContractStage = {
  key: "what" | "why" | "action" | "evidence";
  label: "What" | "Why" | "Action" | "Evidence";
  value: string;
};

export function StoryContractBlock({
  what,
  why,
  action,
  evidence,
}: StoryContractBlockProps) {
  const stages: StoryContractStage[] = [
    { key: "what", label: "What", value: what },
    { key: "why", label: "Why", value: why },
    { key: "action", label: "Action", value: action },
    { key: "evidence", label: "Evidence", value: evidence },
  ];

  return (
    <dl
      className="story-contract-block"
      data-story-contract="what-why-action-evidence"
      data-testid="story-contract-block"
    >
      {stages.map((stage) => (
        <div
          className={`story-contract-block__row story-contract-block__row--${stage.key}`}
          key={stage.key}
        >
          <dt>{stage.label}</dt>
          <dd>{stage.value}</dd>
        </div>
      ))}
    </dl>
  );
}
