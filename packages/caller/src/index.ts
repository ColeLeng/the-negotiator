import type { JobSpec, Quote, VerticalConfig } from "@negotiator/shared";

/**
 * Module 2 — The Caller.
 *
 * Build a call list from the vertical config (Google Places / Yelp), fan out
 * parallel calls (Batch / Twilio / SIP), survive friction, and extract an
 * itemized, comparable Quote from each call. Every call ends in a structured
 * outcome: itemized_quote | callback_commitment | declined.
 *
 * See ./README.md.
 */
export async function runCaller(_spec: JobSpec, _config: VerticalConfig): Promise<Quote[]> {
  throw new Error("Not implemented — build the call-list + batch calling + quote extraction here.");
}
