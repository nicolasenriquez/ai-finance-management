type SnapshotSemanticFlags = {
  autoAdjust: boolean;
  repair: boolean;
};

export type PricingSnapshotProvenance = {
  providerCode: string;
  datasetCode: string;
  interval: string;
  period: string;
  semanticFlags: SnapshotSemanticFlags;
  snapshotDate: string;
  symbolCount: number;
  fingerprint: string;
};

function parseSemanticFlags(rawFlags: string): SnapshotSemanticFlags {
  const normalizedFlags = rawFlags.toLowerCase();
  const autoAdjust = normalizedFlags.includes("aa1");
  const repair = normalizedFlags.includes("rp1");
  return { autoAdjust, repair };
}

function normalizeProviderCode(rawProviderCode: string): string {
  const normalizedCode = rawProviderCode.trim().toLowerCase();
  if (normalizedCode === "yf") {
    return "YFinance";
  }
  return rawProviderCode.toUpperCase();
}

export function parsePricingSnapshotProvenance(
  snapshotKey: string,
): PricingSnapshotProvenance | null {
  const tokens = snapshotKey.split("|");
  if (tokens.length !== 8) {
    return null;
  }

  const [
    providerCode,
    datasetCode,
    interval,
    period,
    semanticFlags,
    snapshotDate,
    symbolToken,
    fingerprint,
  ] = tokens;

  if (!symbolToken.startsWith("s")) {
    return null;
  }

  const symbolCount = Number(symbolToken.slice(1));
  if (!Number.isFinite(symbolCount) || symbolCount <= 0) {
    return null;
  }

  return {
    providerCode: normalizeProviderCode(providerCode),
    datasetCode: datasetCode.toUpperCase(),
    interval: interval.toUpperCase(),
    period: period.toUpperCase(),
    semanticFlags: parseSemanticFlags(semanticFlags),
    snapshotDate,
    symbolCount,
    fingerprint: fingerprint.slice(0, 12),
  };
}

export function formatPricingSnapshotProvenanceLabel(snapshotKey: string): string {
  const parsed = parsePricingSnapshotProvenance(snapshotKey);
  if (parsed === null) {
    return snapshotKey;
  }

  const adjustmentLabel = parsed.semanticFlags.autoAdjust ? "AA:on" : "AA:off";
  const repairLabel = parsed.semanticFlags.repair ? "Repair:on" : "Repair:off";
  return [
    parsed.providerCode,
    parsed.interval,
    parsed.period,
    `${parsed.symbolCount} symbols`,
    parsed.snapshotDate,
    adjustmentLabel,
    repairLabel,
    `#${parsed.fingerprint}`,
  ].join(" · ");
}
