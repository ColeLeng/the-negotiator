export type Channel = {
  type: "voice" | "ucp" | "mock";
  endpoint?: string | null;
};

export type Option = {
  option_id: string;
  vendor: string;
  source_url?: string | null;
  listed_price: number;
  currency?: string;
  matched_attributes: Record<string, string>;
  unmet_soft: string[];
  match_score: number;
  channel: Channel;
};

export type RankedOptions = {
  spec_id: string;
  options: Option[];
};

export type NegotiationMessage = {
  ts?: string | null;
  from: "buyer" | "seller";
  intent: string;
  price?: number | null;
  terms_delta?: Record<string, string>;
  text?: string | null;
  rationale?: string | null;
};

export type NegotiationSession = {
  session_id: string;
  option_id: string;
  spec_id: string;
  status: string;
  current_price?: number | null;
  batna_utility?: number | null;
  messages: NegotiationMessage[];
};

export type DemoPayload = {
  spec: Record<string, unknown>;
  ranked: RankedOptions;
  recommendation: NegotiationSession | null;
  sessions: NegotiationSession[];
};
