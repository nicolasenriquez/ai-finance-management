import { Fragment, useEffect, useMemo, useState } from "react";

import type {
  PortfolioHierarchyAssetRow,
  PortfolioHierarchyGroupBy,
  PortfolioHierarchyGroupRow,
  PortfolioHierarchyLotRow,
} from "../../core/api/schemas";
import { formatDateLabel } from "../../core/lib/dates";
import { parseMoneyDecimal } from "../../core/lib/decimal";
import { formatQuantity, formatUsdMoney, resolveMoneyTone } from "../../core/lib/formatters";

type PortfolioHierarchyTableProps = {
  groups: PortfolioHierarchyGroupRow[];
  groupBy: PortfolioHierarchyGroupBy;
  onGroupByChange: (nextGroupBy: PortfolioHierarchyGroupBy) => void;
};

type HierarchySortField = "label" | "current_value" | "profit_loss" | "change_pct";
type HierarchySortDirection = "asc" | "desc";
type HierarchySortState = {
  field: HierarchySortField;
  direction: HierarchySortDirection;
};

const INSTRUMENT_DISPLAY_NAME_BY_SYMBOL: Record<string, string> = {
  AAPL: "Apple Inc.",
  MSFT: "Microsoft Corp.",
  GOOGL: "Alphabet Inc.",
  NVDA: "NVIDIA Corp.",
  AMZN: "Amazon.com Inc.",
  META: "Meta Platforms Inc.",
  TSLA: "Tesla Inc.",
  VOO: "Vanguard S&P 500 ETF",
  QQQ: "Invesco QQQ",
  QQQM: "Invesco NASDAQ 100 ETF",
};

function resolveInstrumentDisplayName(symbol: string): string {
  return INSTRUMENT_DISPLAY_NAME_BY_SYMBOL[symbol] || "Listed instrument";
}

function formatOptionalPercent(value: string | null): string {
  if (value === null) {
    return "—";
  }
  return `${parseMoneyDecimal(value).toFixed(2)}%`;
}

function isPositiveDecimal(value: string | null): boolean {
  if (value === null) {
    return false;
  }
  return parseMoneyDecimal(value).greaterThan(0);
}

function formatSignedMoney(value: string): string {
  const decimalValue = parseMoneyDecimal(value);
  const formatted = formatUsdMoney(value);
  return decimalValue.greaterThan(0) ? `+${formatted}` : formatted;
}

function formatSignedPercent(value: string | null): string {
  if (value === null) {
    return "—";
  }
  const decimalValue = parseMoneyDecimal(value);
  const fixedValue = decimalValue.toFixed(2);
  if (decimalValue.greaterThan(0)) {
    return `+${fixedValue}%`;
  }
  return `${fixedValue}%`;
}

function toSortableNumber(value: string | null): number {
  if (value === null) {
    return 0;
  }
  const parsedValue = Number.parseFloat(value);
  if (!Number.isFinite(parsedValue)) {
    return 0;
  }
  return parsedValue;
}

function compareLabelValues(leftValue: string, rightValue: string): number {
  return leftValue.localeCompare(rightValue, undefined, {
    sensitivity: "base",
    numeric: true,
  });
}

function compareNumericValues(leftValue: number, rightValue: number): number {
  if (leftValue === rightValue) {
    return 0;
  }
  return leftValue > rightValue ? 1 : -1;
}

function resolveSortArrow(
  sortState: HierarchySortState,
  field: HierarchySortField,
): string {
  if (sortState.field !== field) {
    return "↕";
  }
  return sortState.direction === "asc" ? "↑" : "↓";
}

function resolveAriaSort(
  sortState: HierarchySortState,
  field: HierarchySortField,
): "none" | "ascending" | "descending" {
  if (sortState.field !== field) {
    return "none";
  }
  return sortState.direction === "asc" ? "ascending" : "descending";
}

function sortAssetsForGroup(
  assets: PortfolioHierarchyAssetRow[],
  sortState: HierarchySortState,
): PortfolioHierarchyAssetRow[] {
  const sortedAssets = [...assets];
  sortedAssets.sort((leftAsset, rightAsset) => {
    let comparison = 0;
    if (sortState.field === "label") {
      comparison = compareLabelValues(
        leftAsset.instrument_symbol,
        rightAsset.instrument_symbol,
      );
    } else if (sortState.field === "current_value") {
      comparison = compareNumericValues(
        toSortableNumber(leftAsset.market_value_usd),
        toSortableNumber(rightAsset.market_value_usd),
      );
    } else if (sortState.field === "profit_loss") {
      comparison = compareNumericValues(
        toSortableNumber(leftAsset.profit_loss_usd),
        toSortableNumber(rightAsset.profit_loss_usd),
      );
    } else {
      comparison = compareNumericValues(
        toSortableNumber(leftAsset.change_pct),
        toSortableNumber(rightAsset.change_pct),
      );
    }

    if (comparison === 0) {
      return compareLabelValues(
        leftAsset.instrument_symbol,
        rightAsset.instrument_symbol,
      );
    }

    return sortState.direction === "asc" ? comparison : -comparison;
  });
  return sortedAssets;
}

function renderLotRows(lots: PortfolioHierarchyLotRow[]) {
  return lots.map((lot) => {
    const lotProfitTone = resolveMoneyTone(lot.profit_loss_usd);
    const lotCostBasis = parseMoneyDecimal(lot.total_cost_basis_usd);
    const lotProfitValue = parseMoneyDecimal(lot.profit_loss_usd);
    const lotProfitPercent = lotCostBasis.greaterThan(0)
      ? lotProfitValue.dividedBy(lotCostBasis).times(100).toFixed(2)
      : null;

    return (
      <tr className="hierarchy-lot-row" key={`${lot.lot_id}-${lot.opened_on}`}>
        <td>{formatDateLabel(lot.opened_on)}</td>
        <td>
          <span className="hierarchy-type-pill">BUY</span>
        </td>
        <td className="numeric">{formatQuantity(lot.remaining_qty)}</td>
        <td className="numeric">{formatUsdMoney(lot.total_cost_basis_usd)}</td>
        <td className="numeric">{formatUsdMoney(lot.market_value_usd)}</td>
        <td className={`numeric tone-${lotProfitTone}`}>
          <div className="hierarchy-profit-cell">
            <strong>{formatSignedMoney(lot.profit_loss_usd)}</strong>
            <span>{formatSignedPercent(lotProfitPercent)}</span>
          </div>
        </td>
      </tr>
    );
  });
}

export function PortfolioHierarchyTable({
  groups,
  groupBy,
  onGroupByChange,
}: PortfolioHierarchyTableProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [expandedAssets, setExpandedAssets] = useState<Set<string>>(new Set());
  const [sortState, setSortState] = useState<HierarchySortState>({
    field: "label",
    direction: "asc",
  });

  const sortedGroups = useMemo(() => {
    const sortableGroups = [...groups];
    sortableGroups.sort((leftGroup, rightGroup) => {
      let comparison = 0;
      if (sortState.field === "label") {
        comparison = compareLabelValues(leftGroup.group_label, rightGroup.group_label);
      } else if (sortState.field === "current_value") {
        comparison = compareNumericValues(
          toSortableNumber(leftGroup.total_market_value_usd),
          toSortableNumber(rightGroup.total_market_value_usd),
        );
      } else if (sortState.field === "profit_loss") {
        comparison = compareNumericValues(
          toSortableNumber(leftGroup.total_profit_loss_usd),
          toSortableNumber(rightGroup.total_profit_loss_usd),
        );
      } else {
        comparison = compareNumericValues(
          toSortableNumber(leftGroup.total_change_pct),
          toSortableNumber(rightGroup.total_change_pct),
        );
      }

      if (comparison === 0) {
        return compareLabelValues(leftGroup.group_label, rightGroup.group_label);
      }

      return sortState.direction === "asc" ? comparison : -comparison;
    });
    return sortableGroups;
  }, [groups, sortState]);

  const allGroupKeys = useMemo(
    () => sortedGroups.map((group) => group.group_key),
    [sortedGroups],
  );
  const allAssetKeys = useMemo(
    () =>
      sortedGroups.flatMap((group) =>
        group.assets.map((asset) => `${group.group_key}:${asset.instrument_symbol}`),
      ),
    [sortedGroups],
  );

  useEffect(() => {
    setExpandedGroups(new Set());
    setExpandedAssets(new Set());
  }, [allGroupKeys]);

  function toggleGroup(groupKey: string): void {
    setExpandedGroups((previous) => {
      const next = new Set(previous);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  }

  function toggleAsset(assetKey: string): void {
    setExpandedAssets((previous) => {
      const next = new Set(previous);
      if (next.has(assetKey)) {
        next.delete(assetKey);
      } else {
        next.add(assetKey);
      }
      return next;
    });
  }

  function expandAllGroups(): void {
    setExpandedGroups(new Set(allGroupKeys));
  }

  function collapseAllGroups(): void {
    setExpandedGroups(new Set());
  }

  function expandAllAssets(): void {
    setExpandedAssets(new Set(allAssetKeys));
  }

  function collapseAllAssets(): void {
    setExpandedAssets(new Set());
  }

  function handleSortChange(field: HierarchySortField): void {
    setSortState((previousSortState) => {
      if (previousSortState.field === field) {
        return {
          field,
          direction: previousSortState.direction === "asc" ? "desc" : "asc",
        };
      }
      return {
        field,
        direction: field === "label" ? "asc" : "desc",
      };
    });
  }

  function renderAssetRow(groupKey: string, asset: PortfolioHierarchyAssetRow) {
    const assetRowKey = `${groupKey}:${asset.instrument_symbol}`;
    const isAssetExpanded = expandedAssets.has(assetRowKey);
    const lotPanelId = `hierarchy-lots-${groupKey}-${asset.instrument_symbol}`
      .replaceAll(" ", "-")
      .replaceAll(".", "-");
    const profitTone = resolveMoneyTone(asset.profit_loss_usd);
    const changeTone = isPositiveDecimal(asset.change_pct) ? "positive" : "negative";
    const changePrefix = isPositiveDecimal(asset.change_pct) ? "↗" : "↘";

    return (
      <Fragment key={assetRowKey}>
        <tr className="data-table__row hierarchy-row hierarchy-row--asset">
          <td className="hierarchy-cell hierarchy-cell--asset">
            <button
              aria-expanded={isAssetExpanded}
              aria-controls={lotPanelId}
              aria-label={`Toggle asset ${asset.instrument_symbol} lots`}
              className="hierarchy-toggle"
              onClick={(event) => {
                event.stopPropagation();
                toggleAsset(assetRowKey);
              }}
              type="button"
            >
              {isAssetExpanded ? "▾" : "▸"}
            </button>
            <div className="symbol-cell">
              <div className="symbol-cell__primary">
                <span className="hierarchy-symbol-avatar">
                  {asset.instrument_symbol.slice(0, 2)}
                </span>
                <span className="hierarchy-symbol-title">{asset.instrument_symbol}</span>
              </div>
              <span className="metric-hint">{resolveInstrumentDisplayName(asset.instrument_symbol)}</span>
            </div>
          </td>
          <td className="numeric">{formatQuantity(asset.open_quantity)}</td>
          <td className="numeric">{formatUsdMoney(asset.avg_price_usd)}</td>
          <td className="numeric">{formatUsdMoney(asset.current_price_usd)}</td>
          <td className={`numeric tone-${profitTone}`}>
            <div className="hierarchy-profit-cell">
              <strong>{formatSignedMoney(asset.profit_loss_usd)}</strong>
              <span>{formatSignedPercent(asset.change_pct)}</span>
            </div>
          </td>
          <td className="numeric">
            <span className={`hierarchy-change-pill hierarchy-change-pill--${changeTone}`}>
              {`${changePrefix} ${formatOptionalPercent(asset.change_pct)}`}
            </span>
          </td>
        </tr>

        {isAssetExpanded ? (
          <tr className="hierarchy-subrow" id={lotPanelId}>
            <td colSpan={6}>
              <div className="hierarchy-lot-container">
                <div className="lot-dispositions__header">
                  <div>
                    <h3 className="lot-dispositions__title">Individual Entries (Tax Lots)</h3>
                    <p className="definition-copy">
                      Lot-level positions aligned to persisted ledger and snapshot valuation.
                    </p>
                  </div>
                </div>
                <div className="table-shell">
                  <table className="data-table hierarchy-lot-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th className="numeric">Shares</th>
                        <th className="numeric">Cost Basis</th>
                        <th className="numeric">Market Value</th>
                        <th className="numeric">Profit/Loss</th>
                      </tr>
                    </thead>
                    <tbody>{renderLotRows(asset.lots)}</tbody>
                  </table>
                </div>
                <div className="lot-metrics lot-metrics--compact">
                  <article className="metric-card metric-card--hierarchy">
                    <span className="metric-card__label">Open Lots</span>
                    <strong className="metric-card__value">{asset.lot_count}</strong>
                  </article>
                  <article className="metric-card metric-card--hierarchy">
                    <span className="metric-card__label">Sector</span>
                    <strong className="metric-card__value">{asset.sector_label}</strong>
                  </article>
                  <article className="metric-card metric-card--hierarchy">
                    <span className="metric-card__label">Avg Price</span>
                    <strong className="metric-card__value">
                      {formatUsdMoney(asset.avg_price_usd)}
                    </strong>
                  </article>
                  <article className="metric-card metric-card--hierarchy">
                    <span className="metric-card__label">Current</span>
                    <strong className="metric-card__value">
                      {formatUsdMoney(asset.current_price_usd)}
                    </strong>
                  </article>
                </div>
              </div>
            </td>
          </tr>
        ) : null}
      </Fragment>
    );
  }

  return (
    <section className="panel hierarchy-panel">
      <header className="panel__header hierarchy-panel__header">
        <div>
          <h2 className="panel__title">Portfolio Hierarchy</h2>
          <p className="panel__subtitle">
            Pivot view grouped by {groupBy} and asset lots.
          </p>
        </div>
        <div className="hierarchy-toolbar">
          {groupBy === "sector" ? (
            <div className="hierarchy-toolbar__group">
              <span className="hierarchy-toolbar__label">Sectors</span>
              <button
                aria-label="Expand all sector groups"
                className="hierarchy-toolbar__button"
                onClick={expandAllGroups}
                type="button"
              >
                Expand
              </button>
              <button
                aria-label="Collapse all sector groups"
                className="hierarchy-toolbar__button"
                onClick={collapseAllGroups}
                type="button"
              >
                Collapse
              </button>
            </div>
          ) : null}
          <div className="hierarchy-toolbar__group">
            <span className="hierarchy-toolbar__label">Stocks</span>
            <button
              aria-label="Expand all stock rows"
              className="hierarchy-toolbar__button"
              onClick={expandAllAssets}
              type="button"
            >
              Expand
            </button>
            <button
              aria-label="Collapse all stock rows"
              className="hierarchy-toolbar__button"
              onClick={collapseAllAssets}
              type="button"
            >
              Collapse
            </button>
          </div>
          <button
            aria-label={groupBy === "sector"
              ? "Switch to stock pivot view"
              : "Switch to sector pivot view"}
            className="button-secondary hierarchy-pivot-toggle"
            onClick={() =>
              onGroupByChange(groupBy === "sector" ? "symbol" : "sector")
            }
            type="button"
          >
            {groupBy === "sector" ? "Pivot View" : "Flat View"}
          </button>
          <button
            aria-label="More hierarchy actions"
            className="hierarchy-toolbar__icon-button"
            type="button"
          >
            •••
          </button>
        </div>
      </header>
      <div className="panel__body table-shell">
        <table className="data-table hierarchy-table">
          <thead>
            <tr>
              <th aria-sort={resolveAriaSort(sortState, "label")}>
                <button
                  aria-label="Sort hierarchy by asset or group"
                  className={`hierarchy-sort-button ${
                    sortState.field === "label" ? "hierarchy-sort-button--active" : ""
                  }`}
                  onClick={() => handleSortChange("label")}
                  type="button"
                >
                  Asset / Group
                  <span className="hierarchy-sort-button__arrow" aria-hidden="true">
                    {resolveSortArrow(sortState, "label")}
                  </span>
                </button>
              </th>
              <th className="numeric">Shares</th>
              <th className="numeric">Avg Price</th>
              <th aria-sort={resolveAriaSort(sortState, "current_value")} className="numeric">
                <button
                  aria-label="Sort hierarchy by current value"
                  className={`hierarchy-sort-button hierarchy-sort-button--numeric ${
                    sortState.field === "current_value" ? "hierarchy-sort-button--active" : ""
                  }`}
                  onClick={() => handleSortChange("current_value")}
                  type="button"
                >
                  Current
                  <span className="hierarchy-sort-button__arrow" aria-hidden="true">
                    {resolveSortArrow(sortState, "current_value")}
                  </span>
                </button>
              </th>
              <th aria-sort={resolveAriaSort(sortState, "profit_loss")} className="numeric">
                <button
                  aria-label="Sort hierarchy by profit or loss"
                  className={`hierarchy-sort-button hierarchy-sort-button--numeric ${
                    sortState.field === "profit_loss" ? "hierarchy-sort-button--active" : ""
                  }`}
                  onClick={() => handleSortChange("profit_loss")}
                  type="button"
                >
                  Profit/Loss
                  <span className="hierarchy-sort-button__arrow" aria-hidden="true">
                    {resolveSortArrow(sortState, "profit_loss")}
                  </span>
                </button>
              </th>
              <th aria-sort={resolveAriaSort(sortState, "change_pct")} className="numeric">
                <button
                  aria-label="Sort hierarchy by change percent"
                  className={`hierarchy-sort-button hierarchy-sort-button--numeric ${
                    sortState.field === "change_pct" ? "hierarchy-sort-button--active" : ""
                  }`}
                  onClick={() => handleSortChange("change_pct")}
                  type="button"
                >
                  Change
                  <span className="hierarchy-sort-button__arrow" aria-hidden="true">
                    {resolveSortArrow(sortState, "change_pct")}
                  </span>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedGroups.map((group) => {
              const isGroupExpanded = expandedGroups.has(group.group_key);
              const groupProfitTone = resolveMoneyTone(group.total_profit_loss_usd);
              const groupChangeTone = isPositiveDecimal(group.total_change_pct)
                ? "positive"
                : "negative";
              const groupChangePrefix = isPositiveDecimal(group.total_change_pct)
                ? "↗"
                : "↘";

              return (
                <Fragment key={group.group_key}>
                  <tr className="data-table__row hierarchy-row hierarchy-row--group">
                    <td className="hierarchy-cell hierarchy-cell--group">
                      <button
                        aria-expanded={isGroupExpanded}
                        aria-label={`Toggle group ${group.group_label}`}
                        className="hierarchy-toggle"
                        onClick={(event) => {
                          event.stopPropagation();
                          toggleGroup(group.group_key);
                        }}
                        type="button"
                      >
                        {isGroupExpanded ? "▾" : "▸"}
                      </button>
                      <div className="symbol-cell">
                        <div className="symbol-cell__primary">
                          <span className="hierarchy-group-title">{group.group_label}</span>
                        </div>
                        <span className="metric-hint">{group.asset_count} assets</span>
                      </div>
                    </td>
                    <td className="numeric">—</td>
                    <td className="numeric">—</td>
                    <td className="numeric">
                      {formatUsdMoney(group.total_market_value_usd)}
                    </td>
                    <td className={`numeric tone-${groupProfitTone}`}>
                      <div className="hierarchy-profit-cell">
                        <strong>{formatSignedMoney(group.total_profit_loss_usd)}</strong>
                        <span>{formatSignedPercent(group.total_change_pct)}</span>
                      </div>
                    </td>
                    <td className="numeric">
                      <span className={`hierarchy-change-pill hierarchy-change-pill--${groupChangeTone}`}>
                        {`${groupChangePrefix} ${formatOptionalPercent(group.total_change_pct)}`}
                      </span>
                    </td>
                  </tr>
                  {isGroupExpanded
                    ? sortAssetsForGroup(group.assets, sortState).map((asset) =>
                        renderAssetRow(group.group_key, asset),
                      )
                    : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
