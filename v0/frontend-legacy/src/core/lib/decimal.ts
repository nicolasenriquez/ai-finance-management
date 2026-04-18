import Decimal from "decimal.js";

export function parseMoneyDecimal(value: string): Decimal {
  return new Decimal(value);
}

export function parseQuantityDecimal(value: string): Decimal {
  return new Decimal(value);
}

export function compareDecimal(left: Decimal, right: Decimal): number {
  return left.comparedTo(right);
}
