export type Channel = {
  type: "voice" | "ucp" | "mock";
  endpoint?: string | null;
};

export type FeeLine = {
  code: string;
  label: string;
  amount: number;
  optional?: boolean;
};

export type CallListProvenance = {
  provider: string;
  query?: string | null;
  place_id?: string | null;
  note?: string | null;
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
  negotiation_style?: string | null;
  phone?: string | null;
  call_list_source?: CallListProvenance | null;
  fee_template?: FeeLine[];
};

export type RankedOptions = {
  spec_id: string;
  options: Option[];
  call_list_provenance?: CallListProvenance | null;
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

export type ItemizedQuote = {
  currency?: string;
  line_items: FeeLine[];
  total: number;
  notes?: string | null;
};

export type NegotiationSession = {
  session_id: string;
  option_id: string;
  spec_id: string;
  status: string;
  current_price?: number | null;
  batna_utility?: number | null;
  messages: NegotiationMessage[];
  negotiation_style?: string | null;
  call_ending?: string | null;
  itemized_quote?: ItemizedQuote | null;
};

export type DemoPayload = {
  spec: Record<string, unknown>;
  ranked: RankedOptions;
  recommendation: NegotiationSession | null;
  sessions: NegotiationSession[];
};
