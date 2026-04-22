import http from "node:http";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const distRoot = path.join(projectRoot, "dist");
const reportRoot = path.resolve(projectRoot, "..", "docs", "evidence", "frontend");
const indexHtmlPath = path.join(distRoot, "index.html");

const SERVER_HOST = "127.0.0.1";
const DEFAULT_LISTEN_PORT = 0;
const RUNS_PER_ROUTE = 5;

const thresholds = {
  lcpMs: 2500,
  inpMs: 200,
  cls: 0.1,
};

const summaryPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  rows: [
    {
      instrument_symbol: "VOO",
      open_quantity: "4.000000000",
      open_cost_basis_usd: "900.00",
      open_lot_count: 1,
      realized_proceeds_usd: "500.00",
      realized_cost_basis_usd: "450.00",
      realized_gain_usd: "50.00",
      dividend_gross_usd: "10.00",
      dividend_taxes_usd: "2.00",
      dividend_net_usd: "8.00",
    },
    {
      instrument_symbol: "AAPL",
      open_quantity: "2.000000000",
      open_cost_basis_usd: "1000.00",
      open_lot_count: 2,
      realized_proceeds_usd: "400.00",
      realized_cost_basis_usd: "320.00",
      realized_gain_usd: "80.00",
      dividend_gross_usd: "18.00",
      dividend_taxes_usd: "3.00",
      dividend_net_usd: "15.00",
    },
  ],
};

const lotDetailPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  instrument_symbol: "VOO",
  lots: [
    {
      lot_id: 15,
      opened_on: "2025-12-01",
      original_qty: "4.000000000",
      remaining_qty: "2.000000000",
      total_cost_basis_usd: "900.00",
      unit_cost_basis_usd: "225.00",
      dispositions: [
        {
          sell_transaction_id: 88,
          disposition_date: "2026-01-10",
          matched_qty: "2.000000000",
          matched_cost_basis_usd: "450.00",
          sell_gross_amount_usd: "500.00",
        },
      ],
    },
  ],
};

const transactionsPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  events: [
    {
      id: "trade:101",
      posted_at: "2026-03-24T00:00:00Z",
      instrument_symbol: "AAPL",
      event_type: "buy",
      quantity: "1.000000000",
      cash_amount_usd: "250.00",
    },
    {
      id: "dividend:51",
      posted_at: "2026-03-22T00:00:00Z",
      instrument_symbol: "VOO",
      event_type: "dividend",
      quantity: "0.000000000",
      cash_amount_usd: "6.00",
    },
    {
      id: "trade:99",
      posted_at: "2026-03-20T00:00:00Z",
      instrument_symbol: "VOO",
      event_type: "sell",
      quantity: "0.500000000",
      cash_amount_usd: "180.00",
    },
  ],
};

const supportedChartPeriods = ["30D", "90D", "252D", "MAX"];
const supportedHierarchyGroups = ["sector", "symbol"];
const supportedRiskWindows = [30, 90, 252];

const hierarchyPayloadByGroup = {
  sector: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    group_by: "sector",
    pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
    pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
    groups: [
      {
        group_key: "Technology",
        group_label: "Technology",
        asset_count: 2,
        total_market_value_usd: "1475.00",
        total_profit_loss_usd: "255.00",
        total_change_pct: "20.90",
        assets: [
          {
            instrument_symbol: "AAPL",
            sector_label: "Technology",
            open_quantity: "2.000000000",
            open_cost_basis_usd: "1000.00",
            avg_price_usd: "500.00",
            current_price_usd: "530.00",
            market_value_usd: "1060.00",
            profit_loss_usd: "60.00",
            change_pct: "6.00",
            lot_count: 2,
            lots: [
              {
                lot_id: 21,
                opened_on: "2025-12-20",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "480.00",
                total_cost_basis_usd: "480.00",
                market_value_usd: "530.00",
                profit_loss_usd: "50.00",
              },
              {
                lot_id: 22,
                opened_on: "2026-01-05",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "520.00",
                total_cost_basis_usd: "520.00",
                market_value_usd: "530.00",
                profit_loss_usd: "10.00",
              },
            ],
          },
          {
            instrument_symbol: "MSFT",
            sector_label: "Technology",
            open_quantity: "1.000000000",
            open_cost_basis_usd: "220.00",
            avg_price_usd: "220.00",
            current_price_usd: "415.00",
            market_value_usd: "415.00",
            profit_loss_usd: "195.00",
            change_pct: "88.64",
            lot_count: 1,
            lots: [
              {
                lot_id: 31,
                opened_on: "2025-11-01",
                original_qty: "1.000000000",
                remaining_qty: "1.000000000",
                unit_cost_basis_usd: "220.00",
                total_cost_basis_usd: "220.00",
                market_value_usd: "415.00",
                profit_loss_usd: "195.00",
              },
            ],
          },
        ],
      },
      {
        group_key: "Index",
        group_label: "Index",
        asset_count: 1,
        total_market_value_usd: "960.00",
        total_profit_loss_usd: "60.00",
        total_change_pct: "6.67",
        assets: [
          {
            instrument_symbol: "VOO",
            sector_label: "Index",
            open_quantity: "4.000000000",
            open_cost_basis_usd: "900.00",
            avg_price_usd: "225.00",
            current_price_usd: "240.00",
            market_value_usd: "960.00",
            profit_loss_usd: "60.00",
            change_pct: "6.67",
            lot_count: 1,
            lots: [
              {
                lot_id: 15,
                opened_on: "2025-12-01",
                original_qty: "4.000000000",
                remaining_qty: "4.000000000",
                unit_cost_basis_usd: "225.00",
                total_cost_basis_usd: "900.00",
                market_value_usd: "960.00",
                profit_loss_usd: "60.00",
              },
            ],
          },
        ],
      },
    ],
  },
  symbol: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    group_by: "symbol",
    pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
    pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
    groups: [],
  },
};

const timeSeriesPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "30D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2026-03-19T00:00:00Z", portfolio_value_usd: "1830.00", pnl_usd: "0.00" },
      { captured_at: "2026-03-20T00:00:00Z", portfolio_value_usd: "1850.00", pnl_usd: "20.00" },
      { captured_at: "2026-03-21T00:00:00Z", portfolio_value_usd: "1872.00", pnl_usd: "42.00" },
      { captured_at: "2026-03-22T00:00:00Z", portfolio_value_usd: "1905.00", pnl_usd: "75.00" },
      { captured_at: "2026-03-23T00:00:00Z", portfolio_value_usd: "1975.00", pnl_usd: "145.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "190.00" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "90D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2026-02-24T00:00:00Z", portfolio_value_usd: "1685.00", pnl_usd: "-45.00" },
      { captured_at: "2026-03-03T00:00:00Z", portfolio_value_usd: "1730.00", pnl_usd: "0.00" },
      { captured_at: "2026-03-10T00:00:00Z", portfolio_value_usd: "1782.00", pnl_usd: "52.00" },
      { captured_at: "2026-03-17T00:00:00Z", portfolio_value_usd: "1895.00", pnl_usd: "165.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "290.00" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "252D",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2025-09-24T00:00:00Z", portfolio_value_usd: "1320.00", pnl_usd: "-120.00" },
      { captured_at: "2025-12-24T00:00:00Z", portfolio_value_usd: "1505.00", pnl_usd: "65.00" },
      { captured_at: "2026-01-24T00:00:00Z", portfolio_value_usd: "1620.00", pnl_usd: "180.00" },
      { captured_at: "2026-02-24T00:00:00Z", portfolio_value_usd: "1760.00", pnl_usd: "320.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "580.00" },
    ],
  },
  MAX: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "MAX",
    frequency: "1D",
    timezone: "UTC",
    points: [
      { captured_at: "2024-03-24T00:00:00Z", portfolio_value_usd: "940.00", pnl_usd: "-90.00" },
      { captured_at: "2024-09-24T00:00:00Z", portfolio_value_usd: "1110.00", pnl_usd: "80.00" },
      { captured_at: "2025-03-24T00:00:00Z", portfolio_value_usd: "1385.00", pnl_usd: "355.00" },
      { captured_at: "2025-09-24T00:00:00Z", portfolio_value_usd: "1575.00", pnl_usd: "545.00" },
      { captured_at: "2026-03-24T00:00:00Z", portfolio_value_usd: "2020.00", pnl_usd: "990.00" },
    ],
  },
};

const contributionPayloadByPeriod = {
  "30D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "30D",
    rows: [
      { instrument_symbol: "AAPL", contribution_pnl_usd: "110.00", contribution_pct: "5.44" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "60.00", contribution_pct: "2.97" },
      { instrument_symbol: "MSFT", contribution_pnl_usd: "20.00", contribution_pct: "0.99" },
    ],
  },
  "90D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "90D",
    rows: [
      { instrument_symbol: "AAPL", contribution_pnl_usd: "150.00", contribution_pct: "7.43" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "105.00", contribution_pct: "5.20" },
      { instrument_symbol: "MSFT", contribution_pnl_usd: "35.00", contribution_pct: "1.73" },
    ],
  },
  "252D": {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "252D",
    rows: [
      { instrument_symbol: "AAPL", contribution_pnl_usd: "320.00", contribution_pct: "15.84" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "190.00", contribution_pct: "9.41" },
      { instrument_symbol: "MSFT", contribution_pnl_usd: "70.00", contribution_pct: "3.47" },
    ],
  },
  MAX: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    period: "MAX",
    rows: [
      { instrument_symbol: "AAPL", contribution_pnl_usd: "540.00", contribution_pct: "26.73" },
      { instrument_symbol: "VOO", contribution_pnl_usd: "330.00", contribution_pct: "16.34" },
      { instrument_symbol: "MSFT", contribution_pnl_usd: "120.00", contribution_pct: "5.94" },
    ],
  },
};

const riskPayloadByWindowDays = {
  30: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 30,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1625",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.0810",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "beta",
        value: "1.0420",
        window_days: 30,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
    ],
  },
  90: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 90,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1740",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.1245",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "beta",
        value: "1.0180",
        window_days: 90,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
    ],
  },
  252: {
    as_of_ledger_at: "2026-03-24T01:00:00Z",
    window_days: 252,
    metrics: [
      {
        estimator_id: "annualized_volatility",
        value: "0.1890",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "max_drawdown",
        value: "-0.2015",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
      {
        estimator_id: "beta",
        value: "0.9950",
        window_days: 252,
        return_basis: "simple",
        annualization_basis: { kind: "trading_days", value: 252 },
        as_of_timestamp: "2026-03-24T00:00:00Z",
      },
    ],
  },
};

const mimeByExtension = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function toP75(values) {
  if (values.length === 0) {
    return null;
  }

  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil(sorted.length * 0.75) - 1;
  return sorted[Math.max(index, 0)];
}

function formatIsoDateForFile(value) {
  return value.replaceAll(":", "-");
}

function resolveListenPort() {
  const rawPort = process.env.CWV_PORT;
  if (!rawPort) {
    return DEFAULT_LISTEN_PORT;
  }

  const port = Number.parseInt(rawPort, 10);
  if (Number.isNaN(port) || port < 0 || port > 65535) {
    throw new Error(
      `Invalid CWV_PORT value "${rawPort}". Use an integer between 0 and 65535.`,
    );
  }

  return port;
}

async function assertBuildArtifactsExist() {
  try {
    await readFile(indexHtmlPath);
  } catch (error) {
    throw new Error(
      "Missing frontend build artifacts at frontend/dist/index.html. Run `npm run build` before `npm run cwv:measure`.",
      { cause: error },
    );
  }
}

async function closeServer(server) {
  if (!server.listening) {
    return;
  }

  await new Promise((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve(undefined);
    });
  });
}

async function listenServer(server, port) {
  await new Promise((resolve, reject) => {
    const onError = (error) => {
      server.off("listening", onListening);
      reject(error);
    };
    const onListening = () => {
      server.off("error", onError);
      resolve(undefined);
    };

    server.once("error", onError);
    server.once("listening", onListening);
    server.listen(port, SERVER_HOST);
  });

  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Unable to resolve CWV server address.");
  }

  return `http://${SERVER_HOST}:${address.port}`;
}

async function serveRequest(request, response) {
  const requestUrl = new URL(request.url || "/", "http://127.0.0.1");
  const pathname = requestUrl.pathname;

  if (pathname === "/api/portfolio/summary") {
    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(summaryPayload));
    return;
  }

  if (pathname === "/api/portfolio/time-series") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "30D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    const selectedPayload = timeSeriesPayloadByPeriod[requestedPeriod];
    response.end(
      JSON.stringify({
        ...selectedPayload,
        points: selectedPayload.points.map((point) => ({
          benchmark_nasdaq100_value_usd: point.benchmark_nasdaq100_value_usd ?? null,
          benchmark_sp500_value_usd: point.benchmark_sp500_value_usd ?? null,
          ...point,
        })),
      }),
    );
    return;
  }

  if (pathname === "/api/portfolio/contribution") {
    const requestedPeriod = (requestUrl.searchParams.get("period") || "30D").toUpperCase();
    if (!supportedChartPeriods.includes(requestedPeriod)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported chart period '${requestedPeriod}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(contributionPayloadByPeriod[requestedPeriod]));
    return;
  }

  if (pathname === "/api/portfolio/risk-estimators") {
    const requestedWindow = Number.parseInt(
      requestUrl.searchParams.get("window_days") || "252",
      10,
    );
    if (!supportedRiskWindows.includes(requestedWindow)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({ detail: `Unsupported risk estimator window '${requestedWindow}'.` }),
      );
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(riskPayloadByWindowDays[requestedWindow]));
    return;
  }

  if (pathname === "/api/portfolio/hierarchy") {
    const requestedGroup = (requestUrl.searchParams.get("group_by") || "sector").toLowerCase();
    if (!supportedHierarchyGroups.includes(requestedGroup)) {
      response.writeHead(422, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify({ detail: `Unsupported hierarchy group '${requestedGroup}'.` }));
      return;
    }

    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    const payload =
      requestedGroup === "symbol"
        ? {
            ...hierarchyPayloadByGroup.symbol,
            groups: hierarchyPayloadByGroup.sector.groups.flatMap((group) =>
              group.assets.map((asset) => ({
                group_key: asset.instrument_symbol,
                group_label: asset.instrument_symbol,
                asset_count: 1,
                total_market_value_usd: asset.market_value_usd,
                total_profit_loss_usd: asset.profit_loss_usd,
                total_change_pct: asset.change_pct,
                assets: [asset],
              })),
            ),
          }
        : hierarchyPayloadByGroup.sector;
    response.end(JSON.stringify(payload));
    return;
  }

  if (pathname.startsWith("/api/portfolio/lots/")) {
    const symbol = decodeURIComponent(pathname.slice("/api/portfolio/lots/".length))
      .trim()
      .toUpperCase();
    if (symbol === "VOO") {
      response.writeHead(200, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(JSON.stringify(lotDetailPayload));
      return;
    }

    response.writeHead(404, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(
      JSON.stringify({
        detail: `Instrument ${symbol} was not found in the portfolio ledger.`,
      }),
    );
    return;
  }

  if (pathname === "/api/portfolio/transactions") {
    response.writeHead(200, {
      "Content-Type": mimeByExtension[".json"],
      "Cache-Control": "no-store",
    });
    response.end(JSON.stringify(transactionsPayload));
    return;
  }

  let filePath = path.join(distRoot, pathname);
  if (pathname === "/" || pathname === "") {
    filePath = path.join(distRoot, "index.html");
  }

  try {
    const fileBuffer = await readFile(filePath);
    const extension = path.extname(filePath);
    response.writeHead(200, {
      "Content-Type": mimeByExtension[extension] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    response.end(fileBuffer);
    return;
  } catch {
    // Continue to SPA fallback.
  }

  const spaIndex = await readFile(indexHtmlPath);
  response.writeHead(200, {
    "Content-Type": mimeByExtension[".html"],
    "Cache-Control": "no-store",
  });
  response.end(spaIndex);
}

async function collectRouteRuns(browser, baseUrl, routePath) {
  const runs = [];

  for (let runIndex = 0; runIndex < RUNS_PER_ROUTE; runIndex += 1) {
    const context = await browser.newContext({
      viewport: {
        width: 1440,
        height: 900,
      },
    });
    const page = await context.newPage();

    await page.addInitScript(() => {
      window.__cwvMetrics = {
        cls: 0,
        inp: null,
        lcp: null,
      };

      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const latest = entries[entries.length - 1];
        if (latest) {
          window.__cwvMetrics.lcp = latest.startTime;
        }
      });
      lcpObserver.observe({
        buffered: true,
        type: "largest-contentful-paint",
      });

      const clsObserver = new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
          if (!entry.hadRecentInput) {
            window.__cwvMetrics.cls += entry.value;
          }
        }
      });
      clsObserver.observe({
        buffered: true,
        type: "layout-shift",
      });

      const inpObserver = new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
          if (
            window.__cwvMetrics.inp === null ||
            entry.duration > window.__cwvMetrics.inp
          ) {
            window.__cwvMetrics.inp = entry.duration;
          }
        }
      });
      inpObserver.observe({
        buffered: true,
        durationThreshold: 16,
        type: "event",
      });
    });

    await page.goto(`${baseUrl}${routePath}`, { waitUntil: "networkidle" });
    const themeToggle = page.locator("button.theme-toggle");
    if ((await themeToggle.count()) > 0) {
      await themeToggle.click();
    }
    await page.waitForTimeout(350);

    const metrics = await page.evaluate(() => {
      const cwv = window.__cwvMetrics;
      return {
        cls: typeof cwv.cls === "number" ? cwv.cls : null,
        inp: typeof cwv.inp === "number" ? cwv.inp : null,
        lcp: typeof cwv.lcp === "number" ? cwv.lcp : null,
      };
    });
    runs.push(metrics);

    await context.close();
  }

  return runs;
}

function summarizeRuns(runs) {
  const lcpValues = runs
    .map((run) => run.lcp)
    .filter((value) => typeof value === "number");
  const inpValues = runs
    .map((run) => run.inp)
    .filter((value) => typeof value === "number");
  const clsValues = runs
    .map((run) => run.cls)
    .filter((value) => typeof value === "number");

  const p75 = {
    cls: toP75(clsValues),
    inpMs: toP75(inpValues),
    lcpMs: toP75(lcpValues),
  };

  return {
    p75,
    thresholds,
    verdict: {
      clsPass: p75.cls !== null && p75.cls <= thresholds.cls,
      inpPass: p75.inpMs !== null && p75.inpMs <= thresholds.inpMs,
      lcpPass: p75.lcpMs !== null && p75.lcpMs <= thresholds.lcpMs,
    },
    values: {
      cls: clsValues,
      inpMs: inpValues,
      lcpMs: lcpValues,
    },
  };
}

async function main() {
  await mkdir(reportRoot, { recursive: true });
  await assertBuildArtifactsExist();

  const requestedPort = resolveListenPort();

  const server = http.createServer((request, response) => {
    void serveRequest(request, response).catch((error) => {
      response.writeHead(500, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({
          detail: "CWV local fixture server failed to serve request.",
        }),
      );
      console.error(error);
    });
  });

  const baseUrl = await listenServer(server, requestedPort);
  let browser;

  let measuredAt;
  const measuredRoutes = [
    "/portfolio",
    "/portfolio/VOO",
    "/portfolio/home?period=30D",
    "/portfolio/analytics?period=90D",
    "/portfolio/risk?period=252D",
    "/portfolio/transactions",
  ];
  const routeRunsByPath = {};
  try {
    browser = await chromium.launch({ headless: true });

    measuredAt = new Date().toISOString();
    for (const routePath of measuredRoutes) {
      routeRunsByPath[routePath] = await collectRouteRuns(browser, baseUrl, routePath);
    }
  } finally {
    if (browser) {
      await browser.close();
    }
    await closeServer(server);
  }

  const routeResults = {};
  for (const routePath of measuredRoutes) {
    const runs = routeRunsByPath[routePath];
    routeResults[routePath] = {
      ...summarizeRuns(runs),
      runs,
    };
  }

  const overallPass = Object.values(routeResults).every(
    (routeResult) =>
      routeResult.verdict.clsPass &&
      routeResult.verdict.inpPass &&
      routeResult.verdict.lcpPass,
  );

  const report = {
    measuredAt,
    routeResults,
    runsPerRoute: RUNS_PER_ROUTE,
    thresholds,
    tool: "playwright-performance-observer",
    overallPass,
  };

  await writeFile(
    path.join(
        reportRoot,
        `cwv-report-${formatIsoDateForFile(measuredAt)}.json`,
      ),
    `${JSON.stringify(report, null, 2)}\n`,
  );

  console.log(
    JSON.stringify(
      {
        reportPath: path.join(
          "docs",
          "evidence",
          "frontend",
          `cwv-report-${formatIsoDateForFile(measuredAt)}.json`,
        ),
        routeP75: Object.fromEntries(
          measuredRoutes.map((routePath) => [routePath, routeResults[routePath].p75]),
        ),
        thresholds,
        baseUrl,
        overallPass,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
