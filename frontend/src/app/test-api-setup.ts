import { PORTFOLIO_API_FIXTURE } from "./test-api-fixtures";

const globalFixture = globalThis as typeof globalThis & {
  __PORTFOLIO_API_FIXTURE__?: Record<string, unknown>;
};

const TEST_VIEWPORT_WIDTH = 960;
const TEST_VIEWPORT_HEIGHT = 240;

globalFixture.__PORTFOLIO_API_FIXTURE__ = PORTFOLIO_API_FIXTURE;

if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
  window.matchMedia = (query: string): MediaQueryList => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  });
}

if (typeof window !== "undefined" && typeof window.ResizeObserver !== "function") {
  class ResizeObserverMock implements ResizeObserver {
    private readonly callback: ResizeObserverCallback;

    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }

    observe(target: Element): void {
      const entry = {
        target,
        contentRect: {
          x: 0,
          y: 0,
          width: 960,
          height: 240,
          top: 0,
          right: 960,
          bottom: 240,
          left: 0,
          toJSON: () => ({}),
        },
      } as ResizeObserverEntry;
      this.callback([entry], this);
    }

    unobserve(): void {
      // no-op in test shim
    }

    disconnect(): void {
      // no-op in test shim
    }
  }

  window.ResizeObserver = ResizeObserverMock;
}

if (typeof window !== "undefined") {
  window.requestAnimationFrame = () => 0;
  window.cancelAnimationFrame = () => undefined;
}

if (typeof HTMLElement !== "undefined") {
  Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
    configurable: true,
    get: () => TEST_VIEWPORT_WIDTH,
  });

  Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
    configurable: true,
    get: () => TEST_VIEWPORT_HEIGHT,
  });

  Object.defineProperty(HTMLElement.prototype, "clientWidth", {
    configurable: true,
    get: () => TEST_VIEWPORT_WIDTH,
  });

  Object.defineProperty(HTMLElement.prototype, "clientHeight", {
    configurable: true,
    get: () => TEST_VIEWPORT_HEIGHT,
  });

  HTMLElement.prototype.getBoundingClientRect = () =>
    ({
      x: 0,
      y: 0,
      width: TEST_VIEWPORT_WIDTH,
      height: TEST_VIEWPORT_HEIGHT,
      top: 0,
      right: TEST_VIEWPORT_WIDTH,
      bottom: TEST_VIEWPORT_HEIGHT,
      left: 0,
      toJSON: () => ({}),
    }) as DOMRect;
}
