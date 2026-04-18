import { PORTFOLIO_API_FIXTURE } from "./test-api-fixtures";

const globalFixture = globalThis as typeof globalThis & {
  __PORTFOLIO_API_FIXTURE__?: Record<string, unknown>;
};

globalFixture.__PORTFOLIO_API_FIXTURE__ = PORTFOLIO_API_FIXTURE;
