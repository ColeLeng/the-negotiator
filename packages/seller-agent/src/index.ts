import type { JobSpec, Quote, VerticalConfig } from "@negotiator/shared";

/**
 * The Seller-side agent — the other end of the line.
 *
 * Vendor/counterparty agents that answer the Caller's calls and negotiate against
 * the Closer, each configured to a counterparty style from the vertical config.
 * Runs agent-to-agent (simulated market) — ideally over UCP (Universal Commerce
 * Protocol) — so a price can actually move during a call. Honest counterparty:
 * may be evasive or upsell, but concessions must come from real leverage, not a script.
 *
 * See ./README.md.
 */
export type CounterpartyStyle = "tough_negotiator" | "stonewaller" | "hard_sell_upseller";

/** Answer a call for the described job and return the seller's current offer. */
export async function runSellerAgent(
  _spec: JobSpec,
  _style: CounterpartyStyle,
  _config: VerticalConfig
): Promise<Quote> {
  throw new Error("Not implemented — build the seller/counterparty agent(s) here.");
}
