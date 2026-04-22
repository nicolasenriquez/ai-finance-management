import {
  Fragment,
  useEffect,
  useState,
} from "react";

export type HierarchyPivotRow = {
  id: string;
  label: string;
  weight: string;
  unrealized: string;
  action: string;
};

export type HierarchyPivotGroup = {
  id: string;
  label: string;
  rows: HierarchyPivotRow[];
};

type HierarchyPivotTableProps = {
  groups: HierarchyPivotGroup[];
  tableLabel: string;
};

function buildDefaultExpansionState(groups: HierarchyPivotGroup[]): Record<string, boolean> {
  return Object.fromEntries(groups.map((group) => [group.id, false]));
}

export function HierarchyPivotTable({
  groups,
  tableLabel,
}: HierarchyPivotTableProps) {
  const [expandedGroupState, setExpandedGroupState] = useState<Record<string, boolean>>(
    () => buildDefaultExpansionState(groups),
  );

  useEffect(() => {
    setExpandedGroupState(buildDefaultExpansionState(groups));
  }, [groups]);

  function toggleGroup(groupId: string): void {
    setExpandedGroupState((previousState) => ({
      ...previousState,
      [groupId]: !previousState[groupId],
    }));
  }

  return (
    <table className="route-metric-table hierarchy-pivot-table" aria-label={tableLabel}>
      <thead>
        <tr>
          <th scope="col">Position</th>
          <th scope="col">Weight</th>
          <th scope="col">Unrealized</th>
          <th scope="col">Action</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((group) => {
          const isExpanded = expandedGroupState[group.id];
          return (
            <Fragment key={group.id}>
              <tr className="hierarchy-pivot-group-row" key={`${group.id}-group`}>
                <th colSpan={4} scope="rowgroup">
                  <button
                    aria-expanded={isExpanded}
                    className="hierarchy-pivot-toggle"
                    onClick={() => toggleGroup(group.id)}
                    type="button"
                  >
                    {isExpanded ? "Hide" : "Show"} {group.label} ({group.rows.length} positions)
                  </button>
                </th>
              </tr>
              {isExpanded
                ? group.rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.label}</td>
                    <td className="numeric-value">{row.weight}</td>
                    <td className="numeric-value">{row.unrealized}</td>
                    <td>{row.action}</td>
                  </tr>
                ))
                : null}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
