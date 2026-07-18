/**
 * Shared, typed contracts for The Negotiator.
 *
 * The JobSpec is the single interface every module agrees on:
 *   Estimator PRODUCES it → Caller CONSUMES it (verbatim) → Closer NEGOTIATES against it.
 *
 * Keep this file in sync with ../../schemas/job-spec.schema.json.
 */

export type SpecSource = "voice_interview" | "document" | "hybrid";

export interface Buyer {
  name?: string;
  location?: string;
  phone?: string;
  email?: string;
  /** How the agent names itself and who it acts for. Required — drives AI disclosure. */
  disclosureName: string;
}

/** The buyer's ZOPA — Zone Of Possible Agreement. */
export interface Budget {
  currency: string;
  /** The price the buyer hopes to pay. */
  target: number;
  /** The most the buyer will pay. Above this, decline. */
  walkAway: number;
}

export interface Timeline {
  /** Hard deadline (wedding date, move date). */
  neededBy?: string;
  /** Timing flexibility is itself a negotiation lever. */
  flexible?: boolean;
}

export interface Constraints {
  mustHave?: string[];
  niceToHave?: string[];
  dealBreaker?: string[];
}

export interface NegotiationConfig {
  /** Allowed levers for this job (subset of the vertical config's negotiationLevers). */
  levers?: string[];
  redFlags?: {
    /** A quote this far below the vertical benchmark is a warning, not a win. Default 30. */
    belowMarketPct?: number;
  };
}

/** Vertical-specific requirements. Shape is declared by the vertical config's `specFields`. */
export type VerticalSpec = Record<string, unknown>;

/** THE contract. Built once, confirmed by the user, reused verbatim on every call. */
export interface JobSpec {
  jobId: string;
  vertical: string;
  createdAt?: string;
  source: SpecSource;
  /** MUST be true before any call is made. */
  confirmedByUser: boolean;
  buyer: Buyer;
  budget: Budget;
  timeline?: Timeline;
  spec: VerticalSpec;
  /** Acceptable substitutions the buyer will consider (partial specs). */
  alternatives?: VerticalSpec[];
  constraints?: Constraints;
  negotiation?: NegotiationConfig;
}

/** A single itemized fee line — the unit that makes quotes comparable. */
export interface FeeLine {
  label: string;
  amount: number;
  /** true if the agent judged this fee optional / strippable. */
  optional?: boolean;
}

export type CallOutcome = "itemized_quote" | "callback_commitment" | "declined";

/** What the Caller extracts from one call. Every call ends in one of these — never a vague range. */
export interface Quote {
  quoteId: string;
  jobId: string;
  vendor: {
    name: string;
    phone: string;
    placesId?: string;
    rating?: number;
  };
  outcome: CallOutcome;
  currency: string;
  /** Sum the agent should treat as the real all-in price. Null on non-quote outcomes. */
  total: number | null;
  fees: FeeLine[];
  /** The negotiation style the counterparty exhibited. */
  counterpartyStyle?: string;
  /** Below-market / risk flags raised for this quote. */
  redFlags: string[];
  /** true once a competing bid or lever moved this number during the call. */
  movedByLeverage?: boolean;
  callbackAt?: string;
  transcriptUrl?: string;
  recordingUrl?: string;
  notes?: string;
}

/** The Closer's final, ranked, evidence-cited recommendation. */
export interface NegotiationOutcome {
  jobId: string;
  /** All quotes, best-first. */
  ranked: Quote[];
  recommendedQuoteId: string;
  /** Plain-language explanation of why, with transcript citations. */
  rationale: string;
  /** At least one entry where price/terms changed during the call because of leverage. */
  leverageWins: Array<{ quoteId: string; before: number; after: number; lever: string; transcriptUrl?: string }>;
}

/** Vertical configuration — the "config, not code" surface. Loaded from config/verticals/<vertical>.json. */
export interface VerticalConfig {
  vertical: string;
  displayName: string;
  market: string;
  description?: string;
  specFields: Array<{ key: string; type: string; values?: string[]; required?: boolean; prompt?: string }>;
  priceBenchmark: { source: string; currency: string; median: number; p25: number; p75: number; note?: string };
  redFlags: Array<{ rule: string; thresholdPct?: number; message: string }>;
  negotiationLevers: string[];
  callListSource: { provider: string; query: string; filters?: Record<string, unknown>; note?: string };
  counterpartyStyles: Array<{ id: string; description: string }>;
  disclosure: string;
}
