// GAIA — Shared runtime configuration
// Single source of truth for constants shared across modules.
// Import from here instead of from app.ts to avoid circular dependencies.

const metaEnv = ((import.meta as unknown as { env?: Record<string, string> }).env) ?? {};

/** Base URL of the Python sidecar REST API. */
export const API_BASE: string = metaEnv.VITE_API_BASE ?? 'http://localhost:8008';
