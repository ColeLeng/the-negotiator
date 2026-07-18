"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchDemo,
  formatUsd,
  streamDemo,
  vendorForOption,
} from "@/lib/api";
import type {
  NegotiationMessage,
  NegotiationSession,
  Option,
  RankedOptions,
} from "@/lib/types";

type TranscriptLine = {
  key: string;
  session_id: string;
  option_id: string;
  message: NegotiationMessage;
};

type RunState = "idle" | "running" | "done" | "error";

export default function HomePage() {
  const [runState, setRunState] = useState<RunState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<Option[]>([]);
  const [tickerPrice, setTickerPrice] = useState<number | null>(null);
  const [tickerVendor, setTickerVendor] = useState<string>("—");
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [recommendation, setRecommendation] = useState<NegotiationSession | null>(null);
  const [tickFlash, setTickFlash] = useState(false);
  const stopRef = useRef<null | (() => void)>(null);
  const lineRef = useRef(0);

  const reset = useCallback(() => {
    stopRef.current?.();
    stopRef.current = null;
    setError(null);
    setOptions([]);
    setTickerPrice(null);
    setTickerVendor("—");
    setActiveSession(null);
    setTranscript([]);
    setRecommendation(null);
    lineRef.current = 0;
  }, []);

  const runFallback = useCallback(async () => {
    const payload = await fetchDemo();
    setOptions(payload.ranked.options);
    setRecommendation(payload.recommendation);
    const lines: TranscriptLine[] = [];
    let lastPrice: number | null = null;
    let lastVendor = "—";
    for (const session of payload.sessions) {
      const vendor = vendorForOption(payload.ranked.options, session.option_id);
      for (const message of session.messages) {
        lines.push({
          key: `${session.session_id}-${lines.length}`,
          session_id: session.session_id,
          option_id: session.option_id,
          message,
        });
        if (message.price != null) {
          lastPrice = message.price;
          lastVendor = vendor;
        }
      }
    }
    setTranscript(lines);
    setTickerPrice(payload.recommendation?.current_price ?? lastPrice);
    setTickerVendor(
      vendorForOption(payload.ranked.options, payload.recommendation?.option_id) || lastVendor,
    );
    setActiveSession(payload.recommendation?.session_id ?? null);
    setRunState("done");
  }, []);

  const runDemo = useCallback(() => {
    reset();
    setRunState("running");

    let rankedOptions: Option[] = [];

    stopRef.current = streamDemo({
      onRanked: (ranked: RankedOptions) => {
        rankedOptions = ranked.options;
        setOptions(ranked.options);
      },
      onSessionStart: (info) => {
        setActiveSession(info.session_id);
        setTickerVendor(vendorForOption(rankedOptions, info.option_id));
        if (info.current_price != null) setTickerPrice(info.current_price);
      },
      onMessage: ({ session_id, option_id, message, current_price }) => {
        const key = `${session_id}-${lineRef.current++}`;
        setTranscript((prev) => [...prev, { key, session_id, option_id, message }]);
        setTickerVendor(vendorForOption(rankedOptions, option_id));
        if (current_price != null) {
          setTickerPrice(current_price);
          setTickFlash(true);
          window.setTimeout(() => setTickFlash(false), 220);
        }
      },
      onSessionEnd: () => {
        /* status already on recommendation / table */
      },
      onRecommendation: (rec) => {
        setRecommendation(rec);
        if (rec?.current_price != null) setTickerPrice(rec.current_price);
        if (rec?.option_id) {
          setTickerVendor(vendorForOption(rankedOptions, rec.option_id));
          setActiveSession(rec.session_id);
        }
      },
      onDone: () => setRunState("done"),
      onError: async () => {
        try {
          await runFallback();
        } catch (err) {
          setRunState("error");
          setError(err instanceof Error ? err.message : "Demo failed");
        }
      },
    });
  }, [reset, runFallback]);

  useEffect(() => {
    runDemo();
    return () => stopRef.current?.();
  }, [runDemo]);

  const statusLabel =
    runState === "running"
      ? "negotiating…"
      : runState === "done"
        ? "complete"
        : runState === "error"
          ? "error"
          : "ready";

  return (
    <main className="app">
      <header className="top">
        <div>
          <h1 className="brand">The Negotiator</h1>
          <p className="tagline">
            Agents that shop and haggle for you — watch a real price move as buyer and
            seller push against each other.
          </p>
        </div>
        <div className="controls">
          <span className="status-pill">{statusLabel}</span>
          <button className="run-btn" onClick={runDemo} disabled={runState === "running"}>
            {runState === "running" ? "Running…" : "Run demo"}
          </button>
        </div>
      </header>

      <section className="hero-ticker">
        <div className="panel">
          <h2>Moving price</h2>
          <div className={`price ${tickFlash ? "tick" : ""}`}>{formatUsd(tickerPrice)}</div>
          <div className="price-meta">
            Active session · <strong>{tickerVendor}</strong>
            {activeSession ? ` · ${activeSession}` : ""}
          </div>
        </div>
        <div className="panel rec">
          <h2>Recommendation</h2>
          {recommendation ? (
            <>
              <p className="rec-label">
                {vendorForOption(options, recommendation.option_id)}
              </p>
              <p className="rec-detail">
                <span className="ok">{recommendation.status}</span>
                {" · "}
                {formatUsd(recommendation.current_price)}
                {" · "}
                {recommendation.messages.length} turns
              </p>
            </>
          ) : (
            <p className="empty">
              {runState === "running"
                ? "Waiting for sessions to close…"
                : "No recommendation yet."}
            </p>
          )}
        </div>
      </section>

      <section className="layout">
        <div className="panel">
          <h2>Ranked options</h2>
          {options.length === 0 ? (
            <p className="empty">Pulling comparable listings…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th className="num">List</th>
                  <th className="num">Match</th>
                  <th>Style</th>
                  <th>Channel</th>
                </tr>
              </thead>
              <tbody>
                {options.map((opt) => (
                  <tr key={opt.option_id}>
                    <td className="vendor">
                      {opt.source_url ? (
                        <a href={opt.source_url} target="_blank" rel="noreferrer">
                          {opt.vendor}
                        </a>
                      ) : (
                        opt.vendor
                      )}
                      <div className="chips">
                        {Object.entries(opt.matched_attributes).map(([k, v]) => (
                          <span className="chip" key={k}>
                            {k}: {v}
                          </span>
                        ))}
                        {opt.unmet_soft.map((name) => (
                          <span className="chip warn" key={`u-${name}`}>
                            unmet {name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="num">{formatUsd(opt.listed_price)}</td>
                    <td className="num">
                      <span className="score">{opt.match_score.toFixed(2)}</span>
                    </td>
                    <td>{opt.negotiation_style?.replaceAll("_", " ") ?? "—"}</td>
                    <td>{opt.channel?.type ?? "mock"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="panel">
          <h2>Live transcript</h2>
          <div className="transcript">
            {transcript.length === 0 ? (
              <p className="empty">Messages will stream as negotiations run.</p>
            ) : (
              transcript.map((line) => (
                <article key={line.key} className={`msg ${line.message.from}`}>
                  <div className="msg-head">
                    <span className="side">{line.message.from}</span>
                    <span>
                      {line.message.intent}
                      {" · "}
                      {vendorForOption(options, line.option_id)}
                    </span>
                  </div>
                  <div className="msg-body">
                    {line.message.price != null && (
                      <span className="price-inline">{formatUsd(line.message.price)}</span>
                    )}
                    {line.message.rationale || line.message.text || "—"}
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>

      {error && <div className="error">{error}</div>}
    </main>
  );
}
