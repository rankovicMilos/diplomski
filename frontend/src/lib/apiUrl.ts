// Backend API. Locally the orchestrator runs on :8001 and the upload service on :8002
// (see scripts/dev.sh); a deployed build points NEXT_PUBLIC_API_URL at its API Gateway stage.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
export const UPLOAD_API_URL = process.env.NEXT_PUBLIC_UPLOAD_API_URL ?? "http://localhost:8002";

// In `next dev` requests go through the dev server proxy (see next.config.ts),
// so the browser only talks to its own origin.
export const API_PROXY_PATH = "/api-proxy";
