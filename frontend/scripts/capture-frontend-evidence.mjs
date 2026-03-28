import http from "node:http";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(projectRoot, "..");
const distRoot = path.join(projectRoot, "dist");
const reportRoot = path.join(repoRoot, "docs", "evidence", "frontend");
const indexHtmlPath = path.join(distRoot, "index.html");

const SERVER_HOST = "127.0.0.1";
const DEFAULT_LISTEN_PORT = 0;
const THEME_STORAGE_KEY = "ai-finance-management-theme";

const summaryPayload = {
  as_of_ledger_at: "2026-03-24T01:00:00Z",
  pricing_snapshot_key: "yf|d1|1d|3mo|aa1rp1|2026-03-24|s2|a1b2c3d4e5f6",
  pricing_snapshot_captured_at: "2026-03-24T00:55:00Z",
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
      latest_close_price_usd: "240.00",
      market_value_usd: "960.00",
      unrealized_gain_usd: "60.00",
      unrealized_gain_pct: "6.67",
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
      latest_close_price_usd: "530.00",
      market_value_usd: "1060.00",
      unrealized_gain_usd: "60.00",
      unrealized_gain_pct: "6.00",
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
      "Missing frontend build artifacts at frontend/dist/index.html. Run `npm run build` before `npm run frontend:evidence`.",
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
    throw new Error("Unable to resolve frontend evidence server address.");
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

    if (symbol === "ERR500") {
      response.writeHead(500, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({
          detail: "The portfolio lot-detail API is temporarily unavailable.",
        }),
      );
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
    filePath = indexHtmlPath;
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

function toPosixRelativeRepoPath(absolutePath) {
  const relativePath = path.relative(repoRoot, absolutePath);
  return relativePath.split(path.sep).join("/");
}

async function captureScreenshot({
  browser,
  baseUrl,
  routePath,
  screenshotPath,
  viewport,
  waitForSelector,
  theme,
  fullPage,
}) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();

  if (theme) {
    await page.addInitScript(
      ({ storageKey, storageTheme }) => {
        window.localStorage.setItem(storageKey, storageTheme);
        document.documentElement.dataset.theme = storageTheme;
      },
      {
        storageKey: THEME_STORAGE_KEY,
        storageTheme: theme,
      },
    );
  }

  await page.goto(`${baseUrl}${routePath}`, { waitUntil: "networkidle" });
  if (waitForSelector) {
    await page.waitForSelector(waitForSelector, { state: "visible" });
  }
  await page.waitForTimeout(250);
  await page.screenshot({
    path: screenshotPath,
    fullPage,
  });

  await context.close();
}

async function collectRouteAccessibilityAudit(page, routeLabel) {
  const domChecks = await page.evaluate(() => {
    const normalize = (value) => value.replace(/\s+/g, " ").trim();

    const getAriaLabelledByText = (element) => {
      const labelledBy = element.getAttribute("aria-labelledby");
      if (!labelledBy) {
        return "";
      }

      return labelledBy
        .split(/\s+/)
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((node) => normalize(node.textContent || ""))
        .filter(Boolean)
        .join(" ");
    };

    const resolveAccessibleName = (element) => {
      const ariaLabel = normalize(element.getAttribute("aria-label") || "");
      if (ariaLabel) {
        return ariaLabel;
      }

      const labelledByText = getAriaLabelledByText(element);
      if (labelledByText) {
        return labelledByText;
      }

      return normalize(element.textContent || "");
    };

    const isFocusable = (element) => {
      if (!(element instanceof HTMLElement)) {
        return false;
      }

      if (element.tabIndex >= 0) {
        return true;
      }

      const tagName = element.tagName.toLowerCase();
      if (tagName === "a") {
        return element.hasAttribute("href");
      }

      if (
        tagName === "button" ||
        tagName === "input" ||
        tagName === "select" ||
        tagName === "textarea"
      ) {
        return !element.hasAttribute("disabled");
      }

      return false;
    };

    const describeElement = (element) => {
      if (!(element instanceof HTMLElement)) {
        return "(unknown)";
      }

      const tagName = element.tagName.toLowerCase();
      const id = element.id ? `#${element.id}` : "";
      const className = element.className
        ? `.${String(element.className).trim().replace(/\s+/g, ".")}`
        : "";
      return `${tagName}${id}${className}`;
    };

    const unnamedButtons = Array.from(document.querySelectorAll("button"))
      .filter((element) => resolveAccessibleName(element).length === 0)
      .map((element) => describeElement(element));

    const unnamedLinks = Array.from(document.querySelectorAll("a"))
      .filter((element) => resolveAccessibleName(element).length === 0)
      .map((element) => describeElement(element));

    const ariaHiddenFocusable = Array.from(document.querySelectorAll("[aria-hidden='true']"))
      .filter((element) => isFocusable(element))
      .map((element) => describeElement(element));

    const interactiveRows = Array.from(
      document.querySelectorAll("tr.data-table__row--interactive"),
    ).map((row) => ({
      label: row.getAttribute("aria-label"),
      role: row.getAttribute("role"),
      tabIndex: row.getAttribute("tabindex"),
      keyShortcuts: row.getAttribute("aria-keyshortcuts"),
    }));

    const statusBanners = Array.from(document.querySelectorAll("section.status-banner")).map(
      (banner) => ({
        role: banner.getAttribute("role"),
        title: normalize(
          banner.querySelector(".status-banner__title")?.textContent || "",
        ),
      }),
    );

    const implicitRoleByTag = {
      a: "link",
      button: "button",
      h1: "heading",
      h2: "heading",
      h3: "heading",
      h4: "heading",
      h5: "heading",
      h6: "heading",
      main: "main",
      table: "table",
      td: "cell",
      th: "columnheader",
      tr: "row",
    };

    const roleCounts = {};
    for (const element of document.querySelectorAll("*")) {
      if (!(element instanceof HTMLElement)) {
        continue;
      }

      const explicitRole = element.getAttribute("role");
      const implicitRole = implicitRoleByTag[element.tagName.toLowerCase()];
      const resolvedRole = explicitRole || implicitRole;
      if (!resolvedRole) {
        continue;
      }

      roleCounts[resolvedRole] = (roleCounts[resolvedRole] || 0) + 1;
    }

    return {
      h1Count: document.querySelectorAll("h1").length,
      mainCount: document.querySelectorAll("main").length,
      unnamedButtons,
      unnamedLinks,
      ariaHiddenFocusable,
      interactiveRows,
      statusBanners,
      roleCounts,
    };
  });

  const findings = [];
  if (domChecks.mainCount !== 1) {
    findings.push(`Expected exactly one main landmark, found ${domChecks.mainCount}.`);
  }
  if (domChecks.h1Count !== 1) {
    findings.push(`Expected exactly one h1, found ${domChecks.h1Count}.`);
  }
  if (domChecks.unnamedButtons.length > 0) {
    findings.push(`Unnamed buttons found: ${domChecks.unnamedButtons.join(", ")}.`);
  }
  if (domChecks.unnamedLinks.length > 0) {
    findings.push(`Unnamed links found: ${domChecks.unnamedLinks.join(", ")}.`);
  }
  if (domChecks.ariaHiddenFocusable.length > 0) {
    findings.push(
      `Focusable aria-hidden elements found: ${domChecks.ariaHiddenFocusable.join(", ")}.`,
    );
  }

  if (routeLabel === "/portfolio" && domChecks.interactiveRows.length === 0) {
    findings.push("Expected at least one keyboard-focusable summary row.");
  }

  if (routeLabel === "/portfolio/UNKNOWN") {
    const hasStatus = domChecks.statusBanners.some((banner) => banner.role === "status");
    if (!hasStatus) {
      findings.push("Expected 404 route to expose a status role banner.");
    }
  }

  if (routeLabel === "/portfolio/ERR500") {
    const hasAlert = domChecks.statusBanners.some((banner) => banner.role === "alert");
    if (!hasAlert) {
      findings.push("Expected 500 route to expose an alert role banner.");
    }
  }

  return {
    route: routeLabel,
    passed: findings.length === 0,
    findings,
    domChecks,
    roleCounts: domChecks.roleCounts,
  };
}

async function describeActiveElement(page) {
  return page.evaluate(() => {
    const element = document.activeElement;
    if (!element || !(element instanceof HTMLElement)) {
      return {
        selector: "(none)",
        role: null,
        label: null,
      };
    }

    const normalize = (value) => value.replace(/\s+/g, " ").trim();
    const ariaLabel = normalize(element.getAttribute("aria-label") || "");
    const textLabel = normalize(element.textContent || "");
    const label = ariaLabel || textLabel || null;
    const tagName = element.tagName.toLowerCase();
    const className = String(element.className || "").trim().replace(/\s+/g, ".");
    const selector = className ? `${tagName}.${className}` : tagName;

    return {
      selector,
      role: element.getAttribute("role"),
      label,
      className: String(element.className || ""),
    };
  });
}

async function tabUntil(page, predicate, maxTabs = 32) {
  const sequence = [];

  for (let index = 0; index < maxTabs; index += 1) {
    await page.keyboard.press("Tab");
    const activeElement = await describeActiveElement(page);
    sequence.push(activeElement);
    if (predicate(activeElement)) {
      return {
        found: true,
        sequence,
      };
    }
  }

  return {
    found: false,
    sequence,
  };
}

async function runKeyboardWalkthrough(browser, baseUrl) {
  const context = await browser.newContext({
    viewport: {
      width: 1440,
      height: 900,
    },
  });
  const page = await context.newPage();

  const report = {
    summaryToRowTabSequence: [],
    firstInteractiveRowFound: false,
    enterOnRowNavigatesToLotDetail: false,
    lotDetailBackLinkFound: false,
    backLinkReturnsToSummary: false,
    notFoundRetryFound: false,
    notFoundBackLinkFound: false,
    serverErrorRetryFound: false,
    serverErrorBackLinkFound: false,
  };

  await page.goto(`${baseUrl}/portfolio`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Portfolio summary");

  const rowSequence = await tabUntil(
    page,
    (activeElement) =>
      typeof activeElement.className === "string" &&
      activeElement.className.includes("data-table__row--interactive"),
  );
  report.summaryToRowTabSequence = rowSequence.sequence;
  report.firstInteractiveRowFound = rowSequence.found;

  if (rowSequence.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio/VOO$`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.enterOnRowNavigatesToLotDetail = true;
  }

  const lotBackLink = await tabUntil(
    page,
    (activeElement) =>
      typeof activeElement.label === "string" &&
      activeElement.label.includes("Back to summary"),
  );
  report.lotDetailBackLinkFound = lotBackLink.found;

  if (lotBackLink.found) {
    await Promise.all([
      page.waitForURL(new RegExp(`${baseUrl}/portfolio$`), { timeout: 4000 }),
      page.keyboard.press("Enter"),
    ]);
    report.backLinkReturnsToSummary = true;
  }

  await page.goto(`${baseUrl}/portfolio/UNKNOWN`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Instrument not found");
  const notFoundRetry = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Retry request",
  );
  report.notFoundRetryFound = notFoundRetry.found;
  const notFoundBackLink = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Back to summary",
  );
  report.notFoundBackLinkFound = notFoundBackLink.found;

  await page.goto(`${baseUrl}/portfolio/ERR500`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=Lot detail unavailable");
  const serverErrorRetry = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Retry request",
  );
  report.serverErrorRetryFound = serverErrorRetry.found;
  const serverErrorBackLink = await tabUntil(
    page,
    (activeElement) => activeElement.label === "Back to summary",
  );
  report.serverErrorBackLinkFound = serverErrorBackLink.found;

  await context.close();
  return report;
}

function toPassFail(value) {
  return value ? "PASS" : "FAIL";
}

async function writeAccessibilityMarkdown({
  dateLabel,
  markdownPath,
  accessibilityAudits,
}) {
  const routeRows = accessibilityAudits
    .map(
      (audit) =>
        `| \`${audit.route}\` | \`${toPassFail(audit.passed)}\` | ${
          audit.findings.length > 0 ? audit.findings.join(" ") : "No blocking findings."
        } |`,
    )
    .join("\n");

  const content = `# Frontend Accessibility Scan - ${dateLabel}

## Method

- Tooling: Playwright Chromium + DOM semantic checks + explicit role inventory.
- Scope: \`/portfolio\`, \`/portfolio/VOO\`, \`/portfolio/UNKNOWN\`, \`/portfolio/ERR500\`.
- Focus: landmark/heading structure, interactive naming, keyboard-row semantics, and error-banner role mapping.

## Route Results

| Route | Verdict | Findings |
| --- | --- | --- |
${routeRows}

## WCAG Mapping Notes

- \`1.3.1 Info and Relationships\`: verified main landmark and heading structure per route.
- \`2.4.7 Focus Visible\`: paired with keyboard walkthrough evidence in \`docs/evidence/frontend/keyboard-walkthrough-${dateLabel}.md\`.
- \`3.3.1 Error Identification\`: verified dedicated \`status\` (\`404\`) and \`alert\` (\`500\`) banners.
- \`4.1.2 Name, Role, Value\`: verified button/link naming and interactive summary row semantics.

## Raw Evidence

- JSON report: \`docs/evidence/frontend/accessibility-scan-${dateLabel}.json\`
`;

  await writeFile(markdownPath, content);
}

async function writeKeyboardMarkdown({
  dateLabel,
  markdownPath,
  keyboardReport,
}) {
  const firstSteps = keyboardReport.summaryToRowTabSequence
    .slice(0, 8)
    .map((step, index) => `${index + 1}. ${step.selector} | role=${step.role || "n/a"} | label=${step.label || "n/a"}`)
    .join("\n");

  const content = `# Frontend Keyboard Walkthrough - ${dateLabel}

## Scope

- Routes: \`/portfolio\`, \`/portfolio/VOO\`, \`/portfolio/UNKNOWN\`, \`/portfolio/ERR500\`
- Viewport: desktop \`1440x900\`
- Source: automated tab-sequence and keyboard activation checks via Playwright

## Results

- First interactive summary row found by keyboard tabbing: \`${toPassFail(keyboardReport.firstInteractiveRowFound)}\`
- Enter on focused summary row navigates to lot detail: \`${toPassFail(keyboardReport.enterOnRowNavigatesToLotDetail)}\`
- Lot-detail back link is keyboard-reachable: \`${toPassFail(keyboardReport.lotDetailBackLinkFound)}\`
- Keyboard activation on back link returns to summary: \`${toPassFail(keyboardReport.backLinkReturnsToSummary)}\`
- 404 screen retry button is keyboard-reachable: \`${toPassFail(keyboardReport.notFoundRetryFound)}\`
- 404 screen back link is keyboard-reachable: \`${toPassFail(keyboardReport.notFoundBackLinkFound)}\`
- 500 screen retry button is keyboard-reachable: \`${toPassFail(keyboardReport.serverErrorRetryFound)}\`
- 500 screen back link is keyboard-reachable: \`${toPassFail(keyboardReport.serverErrorBackLinkFound)}\`

## Summary Tab Sequence (first 8 focus stops)

${firstSteps}

## Raw Evidence

- JSON report: \`docs/evidence/frontend/keyboard-walkthrough-${dateLabel}.json\`
`;

  await writeFile(markdownPath, content);
}

async function main() {
  await mkdir(reportRoot, { recursive: true });
  await assertBuildArtifactsExist();

  const now = new Date();
  const measuredAt = now.toISOString();
  const dateLabel = now.toISOString().slice(0, 10);
  const captureLabel = formatIsoDateForFile(measuredAt);
  const screenshotRoot = path.join(reportRoot, `screenshots-${dateLabel}`);
  await mkdir(screenshotRoot, { recursive: true });

  const requestedPort = resolveListenPort();
  const server = http.createServer((request, response) => {
    void serveRequest(request, response).catch((error) => {
      response.writeHead(500, {
        "Content-Type": mimeByExtension[".json"],
        "Cache-Control": "no-store",
      });
      response.end(
        JSON.stringify({
          detail: "Frontend evidence fixture server failed to serve request.",
        }),
      );
      console.error(error);
    });
  });

  const baseUrl = await listenServer(server, requestedPort);
  let browser;
  try {
    browser = await chromium.launch({ headless: true });

    const screenshotSpecs = [
      {
        fileName: "desktop-summary-ledger-timestamp.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Ledger as of",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "desktop-summary-first-viewport.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Ledger as of",
        theme: "dark",
        fullPage: false,
      },
      {
        fileName: "desktop-summary-dark-theme.png",
        routePath: "/portfolio",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Ledger as of",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "mobile-summary-responsive.png",
        routePath: "/portfolio",
        viewport: { width: 390, height: 844 },
        waitForSelector: "text=Ledger as of",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-disposition-history.png",
        routePath: "/portfolio/VOO",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Disposition history",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-not-found-404.png",
        routePath: "/portfolio/UNKNOWN",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Instrument not found",
        theme: "dark",
        fullPage: true,
      },
      {
        fileName: "lot-detail-server-error-500.png",
        routePath: "/portfolio/ERR500",
        viewport: { width: 1440, height: 900 },
        waitForSelector: "text=Lot detail unavailable",
        theme: "dark",
        fullPage: true,
      },
    ];

    for (const screenshotSpec of screenshotSpecs) {
      await captureScreenshot({
        browser,
        baseUrl,
        routePath: screenshotSpec.routePath,
        screenshotPath: path.join(screenshotRoot, screenshotSpec.fileName),
        viewport: screenshotSpec.viewport,
        waitForSelector: screenshotSpec.waitForSelector,
        theme: screenshotSpec.theme,
        fullPage: screenshotSpec.fullPage,
      });
    }

    const accessibilityAudits = [];
    const accessibilityRoutes = [
      "/portfolio",
      "/portfolio/VOO",
      "/portfolio/UNKNOWN",
      "/portfolio/ERR500",
    ];
    for (const routePath of accessibilityRoutes) {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      const page = await context.newPage();
      await page.goto(`${baseUrl}${routePath}`, { waitUntil: "networkidle" });
      if (routePath === "/portfolio") {
        await page.waitForSelector("text=Portfolio summary");
      }
      if (routePath === "/portfolio/VOO") {
        await page.waitForSelector("text=Disposition history");
      }
      if (routePath === "/portfolio/UNKNOWN") {
        await page.waitForSelector("text=Instrument not found");
      }
      if (routePath === "/portfolio/ERR500") {
        await page.waitForSelector("text=Lot detail unavailable");
      }
      accessibilityAudits.push(
        await collectRouteAccessibilityAudit(page, routePath),
      );
      await context.close();
    }

    const keyboardReport = await runKeyboardWalkthrough(browser, baseUrl);

    const accessibilityJsonPath = path.join(
      reportRoot,
      `accessibility-scan-${dateLabel}.json`,
    );
    const keyboardJsonPath = path.join(
      reportRoot,
      `keyboard-walkthrough-${dateLabel}.json`,
    );
    const accessibilityMarkdownPath = path.join(
      reportRoot,
      `accessibility-scan-${dateLabel}.md`,
    );
    const keyboardMarkdownPath = path.join(
      reportRoot,
      `keyboard-walkthrough-${dateLabel}.md`,
    );

    await writeFile(
      accessibilityJsonPath,
      `${JSON.stringify(
        {
          measuredAt,
          baseUrl,
          audits: accessibilityAudits,
        },
        null,
        2,
      )}\n`,
    );
    await writeFile(
      keyboardJsonPath,
      `${JSON.stringify(
        {
          measuredAt,
          baseUrl,
          keyboardReport,
        },
        null,
        2,
      )}\n`,
    );

    await writeAccessibilityMarkdown({
      dateLabel,
      markdownPath: accessibilityMarkdownPath,
      accessibilityAudits,
    });
    await writeKeyboardMarkdown({
      dateLabel,
      markdownPath: keyboardMarkdownPath,
      keyboardReport,
    });

    const screenshotEntries = [
      "desktop-summary-ledger-timestamp.png",
      "desktop-summary-first-viewport.png",
      "desktop-summary-dark-theme.png",
      "mobile-summary-responsive.png",
      "lot-detail-disposition-history.png",
      "lot-detail-not-found-404.png",
      "lot-detail-server-error-500.png",
    ].map((fileName) =>
      toPosixRelativeRepoPath(path.join(screenshotRoot, fileName)),
    );

    console.log(
      JSON.stringify(
        {
          measuredAt,
          captureId: captureLabel,
          baseUrl,
          screenshots: screenshotEntries,
          accessibilityReport: toPosixRelativeRepoPath(accessibilityMarkdownPath),
          keyboardReport: toPosixRelativeRepoPath(keyboardMarkdownPath),
        },
        null,
        2,
      ),
    );
  } finally {
    if (browser) {
      await browser.close();
    }
    await closeServer(server);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
