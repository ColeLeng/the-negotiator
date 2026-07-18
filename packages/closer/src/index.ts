import type { JobSpec, Quote, NegotiationOutcome, VerticalConfig } from "@negotiator/shared";

/**
 * Module 3 — The Closer.
 *
 * Negotiate using REAL leverage only (competing quotes that exist with a transcript),
 * push on fees, apply red-flag rules (30%+ below market = warning), then rank all
 * quotes and produce a plain-language report with transcript citations. At least one
 * negotiation must show price/terms change during the call because of leverage.
 *
 * See ./README.md.
 */
export async function runCloser(
  _spec: JobSpec,
  _quotes: Quote[],
  _config: VerticalConfig
): Promise<NegotiationOutcome> {
  throw new Error("Not implemented — build the negotiation loop + ranked report here.");
}
