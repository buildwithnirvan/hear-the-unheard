// Backend location. Override via .env.local (see .env.local.example) when
// the backend isn't running on localhost:8000 — e.g. a deployed instance.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const WS_RECOGNIZE_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/recognize";
