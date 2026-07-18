import type { DemoPayload, NegotiationMessage, Option, RankedOptions } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export type StreamHandlers = {
  onRanked: (ranked: RankedOptions, spec: Record<string, unknown>) => void;
  onSessionStart: (info: {
    session_id: string;
    option_id: string;
    status: string;
    current_price?: number | null;
  }) => void;
  onMessage: (payload: {
    session_id: string;
    option_id: string;
    message: NegotiationMessage;
    current_price?: number | null;
  }) => void;
  onSessionEnd: (info: {
    session_id: string;
    option_id: string;
    status: string;
    current_price?: number | null;
  }) => void;
  onRecommendation: (recommendation: DemoPayload["recommendation"]) => void;
  onDone: () => void;
  onError: (err: Error) => void;
};

/** Fetch the full demo payload in one shot (fallback if SSE fails). */
export async function fetchDemo(): Promise<DemoPayload> {
  const res = await fetch(`${API_BASE}/demo`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /demo failed: ${res.status}`);
  return res.json();
}

/** Live SSE stream: ranked → messages → recommendation. */
export function streamDemo(handlers: StreamHandlers): () => void {
  const es = new EventSource(`${API_BASE}/demo/stream`);

  es.addEventListener("ranked", (ev) => {
    const data = JSON.parse((ev as MessageEvent).data);
    handlers.onRanked(data.ranked as RankedOptions, data.spec);
  });
  es.addEventListener("session_start", (ev) => {
    handlers.onSessionStart(JSON.parse((ev as MessageEvent).data));
  });
  es.addEventListener("message", (ev) => {
    handlers.onMessage(JSON.parse((ev as MessageEvent).data));
  });
  es.addEventListener("session_end", (ev) => {
    handlers.onSessionEnd(JSON.parse((ev as MessageEvent).data));
  });
  es.addEventListener("recommendation", (ev) => {
    const data = JSON.parse((ev as MessageEvent).data);
    handlers.onRecommendation(data.recommendation);
  });
  es.addEventListener("done", () => {
    handlers.onDone();
    es.close();
  });
  es.onerror = () => {
    handlers.onError(new Error("SSE connection failed"));
    es.close();
  };

  return () => es.close();
}

export function vendorForOption(
  options: Option[],
  optionId: string | undefined,
): string {
  if (!optionId) return "—";
  return options.find((o) => o.option_id === optionId)?.vendor ?? optionId;
}

export function formatUsd(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}
