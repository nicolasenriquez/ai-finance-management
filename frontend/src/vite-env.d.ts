/// <reference types="vite/client" />

declare global {
  // Populated only in Vitest via src/app/test-api-setup.ts.
  // Production builds never define this fixture.
  // eslint-disable-next-line no-var
  var __PORTFOLIO_API_FIXTURE__: Record<string, unknown> | undefined;
}

export {};
