import {
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

type MetricExplainabilityPopoverProps = {
  label: string;
  shortDefinition: string;
  whyItMatters: string;
  interpretation: string;
  formulaOrBasis: string;
  comparisonContext?: string;
  caveats?: string;
  currentContextNote?: string;
  className?: string;
};

export function MetricExplainabilityPopover({
  label,
  shortDefinition,
  whyItMatters,
  interpretation,
  formulaOrBasis,
  comparisonContext,
  caveats,
  currentContextNote,
  className,
}: MetricExplainabilityPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverId = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerClassName = className
    ? `metric-explainability__trigger ${className}`
    : "metric-explainability__trigger";

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleDocumentMouseDown(event: MouseEvent): void {
      if (!rootRef.current) {
        return;
      }

      if (!rootRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleDocumentKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleDocumentMouseDown);
    document.addEventListener("keydown", handleDocumentKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleDocumentMouseDown);
      document.removeEventListener("keydown", handleDocumentKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="metric-explainability" ref={rootRef}>
      <button
        aria-controls={popoverId}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label={`Explain ${label}`}
        className={triggerClassName}
        onClick={() => setIsOpen((previous) => !previous)}
        title={`Explain ${label}`}
        type="button"
      >
        <span aria-hidden="true" className="metric-explainability__icon">
          i
        </span>
        <span className="sr-only">Explain {label}</span>
      </button>
      {isOpen ? (
        <div
          className="metric-explainability__popover"
          id={popoverId}
          role="dialog"
          aria-label={`${label} explanation`}
        >
          <h4 className="metric-explainability__title">{label}</h4>
          <dl className="metric-explainability__list">
            <div>
              <dt>Definition</dt>
              <dd>{shortDefinition}</dd>
            </div>
            <div>
              <dt>Why it matters</dt>
              <dd>{whyItMatters}</dd>
            </div>
            <div>
              <dt>How to interpret</dt>
              <dd>{interpretation}</dd>
            </div>
            <div>
              <dt>Formula / basis</dt>
              <dd>{formulaOrBasis}</dd>
            </div>
            {comparisonContext ? (
              <div>
                <dt>Comparison context</dt>
                <dd>{comparisonContext}</dd>
              </div>
            ) : null}
            {currentContextNote ? (
              <div>
                <dt>Current context</dt>
                <dd>{currentContextNote}</dd>
              </div>
            ) : null}
            {caveats ? (
              <div>
                <dt>Caveat</dt>
                <dd>{caveats}</dd>
              </div>
            ) : null}
          </dl>
          <button
            className="metric-explainability__close"
            onClick={() => setIsOpen(false)}
            type="button"
          >
            Close explanation
          </button>
        </div>
      ) : null}
    </div>
  );
}
