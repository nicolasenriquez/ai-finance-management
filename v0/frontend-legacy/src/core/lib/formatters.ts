import Decimal from "decimal.js";

import {
  compareDecimal,
  parseMoneyDecimal,
  parseQuantityDecimal,
} from "./decimal";

export type ValueTone = "positive" | "negative" | "neutral";

const ZERO_DECIMAL = new Decimal(0);

const moneyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatUsdMoney(value: string): string {
  return moneyFormatter.format(parseMoneyDecimal(value).toNumber());
}

export function formatQuantity(value: string): string {
  const decimal = parseQuantityDecimal(value);
  const fixed = decimal.toFixed(9);
  return fixed.replace(/(\.\d*?[1-9])0+$/u, "$1").replace(/\.0+$/u, "");
}

function resolveDecimalTone(value: Decimal): ValueTone {
  const comparison = compareDecimal(value, ZERO_DECIMAL);

  if (comparison > 0) {
    return "positive";
  }

  if (comparison < 0) {
    return "negative";
  }

  return "neutral";
}

export function resolveMoneyTone(value: string): ValueTone {
  return resolveDecimalTone(parseMoneyDecimal(value));
}

export function resolveQuantityTone(value: string): ValueTone {
  return resolveDecimalTone(parseQuantityDecimal(value));
}
