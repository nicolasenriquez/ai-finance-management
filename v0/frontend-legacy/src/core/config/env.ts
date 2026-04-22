const DEFAULT_API_PREFIX = "/api";

export type FrontendEnv = {
  apiPrefix: string;
};

export function getFrontendEnv(): FrontendEnv {
  const apiPrefix = import.meta.env.VITE_API_PREFIX || DEFAULT_API_PREFIX;

  return {
    apiPrefix,
  };
}
