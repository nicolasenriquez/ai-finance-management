import {
  describe,
  expect,
  it,
} from "vitest";

import {
  extractYFinanceQualityAdapterRows,
  extractYFinanceTechnicalAdapterRows,
  extractYFinanceValuationAdapterRows,
} from "./yfinance-extraction-adapters";

describe("yfinance extraction adapter contract", () => {
  it("4.9 extracts first-surface valuation metrics from direct screener fields", () => {
    const valuationRows = extractYFinanceValuationAdapterRows({
      "peratio.lasttwelvemonths": 22.4,
      pegratio_5y: 1.8,
      "pricebookratio.quarterly": 8.6,
    });

    expect(valuationRows).toHaveLength(3);
    expect(valuationRows.map((row) => row.metricId)).toEqual([
      "pe_ratio",
      "peg_ratio",
      "price_to_book",
    ]);
    expect(valuationRows.every((row) => row.availability === "direct")).toBe(true);
  });

  it("4.9 marks quality metrics unavailable when direct fields are missing", () => {
    const qualityRows = extractYFinanceQualityAdapterRows({
      "returnonequity.lasttwelvemonths": 0.24,
      "returnonassets.lasttwelvemonths": null,
      "totaldebtequity.lasttwelvemonths": undefined,
      "currentratio.lasttwelvemonths": 1.7,
    });

    expect(qualityRows).toHaveLength(4);

    const roaMetric = qualityRows.find((row) => row.metricId === "return_on_assets");
    const debtToEquityMetric = qualityRows.find((row) => row.metricId === "debt_to_equity");

    expect(roaMetric?.availability).toBe("unavailable");
    expect(debtToEquityMetric?.availability).toBe("unavailable");
    expect(roaMetric?.reason).toContain("field missing");
    expect(debtToEquityMetric?.reason).toContain("field missing");
  });

  it("4.9 extracts direct and derived technical inputs from OHLCV/actions/options payloads", () => {
    const technicalRows = extractYFinanceTechnicalAdapterRows({
      bars: [
        { open: 181, high: 183, low: 179, close: 182, volume: 12_200_000 },
        { open: 182, high: 184, low: 181, close: 183, volume: 11_900_000 },
        { open: 183, high: 186, low: 182, close: 185, volume: 13_100_000 },
        { open: 185, high: 187, low: 184, close: 186, volume: 12_700_000 },
        { open: 186, high: 189, low: 185, close: 188, volume: 14_400_000 },
        { open: 188, high: 190, low: 187, close: 189, volume: 12_900_000 },
        { open: 189, high: 191, low: 188, close: 190, volume: 11_500_000 },
        { open: 190, high: 192, low: 189, close: 191, volume: 10_900_000 },
        { open: 191, high: 193, low: 190, close: 192, volume: 10_300_000 },
        { open: 192, high: 194, low: 191, close: 193, volume: 10_500_000 },
        { open: 193, high: 195, low: 192, close: 194, volume: 9_900_000 },
        { open: 194, high: 196, low: 193, close: 195, volume: 9_600_000 },
        { open: 195, high: 197, low: 194, close: 196, volume: 9_800_000 },
        { open: 196, high: 198, low: 195, close: 197, volume: 9_300_000 },
        { open: 197, high: 199, low: 196, close: 198, volume: 9_100_000 },
      ],
      actions: [
        {
          type: "dividend",
          value: 0.26,
        },
      ],
      optionContracts: [
        {
          impliedVolatility: 0.37,
        },
      ],
    });

    const latestClose = technicalRows.find((row) => row.metricId === "latest_close");
    const impliedVolatility = technicalRows.find(
      (row) => row.metricId === "option_implied_volatility",
    );
    const atrMetric = technicalRows.find((row) => row.metricId === "atr_14");

    expect(latestClose?.availability).toBe("direct");
    expect(impliedVolatility?.availability).toBe("direct");
    expect(atrMetric?.availability).toBe("derived");
    expect(atrMetric?.value).not.toBeNull();
  });
});
