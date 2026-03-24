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
  let summaryRouteRuns;
  let lotDetailRouteRuns;
  try {
    browser = await chromium.launch({ headless: true });

    measuredAt = new Date().toISOString();
    summaryRouteRuns = await collectRouteRuns(browser, baseUrl, "/portfolio");
    lotDetailRouteRuns = await collectRouteRuns(browser, baseUrl, "/portfolio/VOO");
  } finally {
    if (browser) {
      await browser.close();
    }
    await closeServer(server);
  }

  const summaryRoute = summarizeRuns(summaryRouteRuns);
  const lotDetailRoute = summarizeRuns(lotDetailRouteRuns);
  const overallPass =
    summaryRoute.verdict.clsPass &&
    summaryRoute.verdict.inpPass &&
    summaryRoute.verdict.lcpPass &&
    lotDetailRoute.verdict.clsPass &&
    lotDetailRoute.verdict.inpPass &&
    lotDetailRoute.verdict.lcpPass;

  const report = {
    measuredAt,
    routeResults: {
      "/portfolio": {
        ...summaryRoute,
        runs: summaryRouteRuns,
      },
      "/portfolio/VOO": {
        ...lotDetailRoute,
        runs: lotDetailRouteRuns,
      },
    },
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
        routeP75: {
          "/portfolio": summaryRoute.p75,
          "/portfolio/VOO": lotDetailRoute.p75,
        },
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
