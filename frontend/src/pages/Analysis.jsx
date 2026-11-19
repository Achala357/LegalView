import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";

/**
 * Split the clause risk_reason into:
 * - clausePart: the first segment (usually base -> adjusted)
 * - contractContext: everything after the first semicolon (contract-wide context)
 */
function splitRiskReason(reason) {
  const s = (reason || "").toString().trim();
  if (!s) return { clausePart: "", contractContext: "" };

  const idx = s.indexOf(";");
  if (idx === -1) return { clausePart: s, contractContext: "" };

  const clausePart = s.slice(0, idx).trim();
  const contractContext = s.slice(idx + 1).trim();
  return { clausePart, contractContext };
}

function semicolonBullets(text) {
  const s = (text || "").toString().trim();
  if (!s) return [];
  // split on semicolons, keep meaningful pieces
  return s
    .split(";")
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => (x.endsWith(".") ? x : `${x}.`));
}

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

function formatClauseType(t) {
  if (!t) return "unknown";
  return t.replaceAll("_", " ");
}

function formatNum(n, digits = 4) {
  if (typeof n !== "number") return n ?? "";
  return Number.isFinite(n) ? n.toFixed(digits) : String(n);
}

export default function Analysis() {
  const { filename } = useParams();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [question, setQuestion] = useState("");
  const [qaResult, setQaResult] = useState(null);
  const [asking, setAsking] = useState(false);
  const [qaError, setQaError] = useState(null);

  const [clauseFilter, setClauseFilter] = useState("all"); // all | risky | safe

  useEffect(() => {
    if (!filename) {
      setError("No file specified for analysis.");
      setLoading(false);
      return;
    }

    const runAnalysis = async () => {
      try {
        const fileRes = await fetch(
          `http://localhost:8000/uploads/${encodeURIComponent(filename)}`
        );

        if (!fileRes.ok) {
          throw new Error("Failed to fetch file from server.");
        }

        const blob = await fileRes.blob();

        const file = new File([blob], filename, {
          type: blob.type || "text/plain",
        });

        const formData = new FormData();
        formData.append("file", file);

        const res = await axios.post(
          "http://localhost:8000/api/contracts/analyze",
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
          }
        );

        setData(res.data);
      } catch (err) {
        console.error(err);
        setError("Failed to run analysis.");
      } finally {
        setLoading(false);
      }
    };

    runAnalysis();
  }, [filename]);

  const askQuestion = async () => {
    if (!question.trim()) return;

    setAsking(true);
    setQaResult(null);
    setQaError(null);

    try {
      const res = await axios.post("http://localhost:8000/api/qa/ask", {
        question,
        structured_context: {
          ...(data || {}),
          // Make sure filename is present for upload-index retrieval if your backend uses it
          filename: data?.filename || filename || null,
        },
      });

      setQaResult(res.data);
    } catch (err) {
      console.error(err);
      setQaError("Failed to retrieve answer.");
    } finally {
      setAsking(false);
    }
  };

  // ----- Clause list + filters -----
  const riskClauses = data?.risk_clauses || [];
  const filteredClauses = useMemo(() => {
    if (clauseFilter === "risky") {
      return riskClauses.filter((c) => c?.risk_label === "risky");
    }
    if (clauseFilter === "safe") {
      return riskClauses.filter((c) => c?.risk_label !== "risky");
    }
    return riskClauses;
  }, [riskClauses, clauseFilter]);

  const riskyCount = useMemo(
    () => riskClauses.filter((c) => c?.risk_label === "risky").length,
    [riskClauses]
  );
  const safeCount = useMemo(
    () => riskClauses.length - riskyCount,
    [riskClauses, riskyCount]
  );

  // ----- Extract the contract-wide context ONCE (so it doesn't repeat per clause card) -----
  const contractWideContext = useMemo(() => {
    const contexts = riskClauses
      .map((c) => splitRiskReason(c?.risk_reason).contractContext)
      .filter(Boolean);

    if (contexts.length === 0) {
      return { text: "", coverage: 0, bullets: [] };
    }

    const counts = new Map();
    for (const ctx of contexts) {
      counts.set(ctx, (counts.get(ctx) || 0) + 1);
    }
    const best = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
    const bestText = best?.[0] || "";
    const bestCount = best?.[1] || 0;

    const coverage = contexts.length ? bestCount / contexts.length : 0;
    const bullets = semicolonBullets(bestText);

    return { text: bestText, coverage, bullets };
  }, [riskClauses]);

  if (loading) {
    return <div className="p-8 text-slate-600">Running analysis…</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">{error}</div>;
  }

  if (!data) {
    return <div className="p-8 text-slate-600">No analysis data available.</div>;
  }

  // ✅ PATCH: out-of-scope guard (show message + still allow Q&A)
  // ✅ PATCH: out-of-scope guard (show ONLY the out-of-scope UI)
  if (data?.out_of_scope) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10">
        <div className="mx-auto max-w-5xl space-y-8">
          <header>
            <h1 className="text-3xl font-bold text-[#0B3D91]">
              Contract Analysis Report
            </h1>
            <p className="text-slate-500">{data?.filename || filename}</p>
          </header>

          <section className="rounded-xl border bg-white p-6 shadow">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <p className="text-sm">
                  <strong>Contract Type:</strong>{" "}
                  <span className="font-semibold capitalize">
                    {data?.contract_type || "other"}
                  </span>
                </p>

                <p className="text-sm text-slate-700 whitespace-pre-wrap">
                  {data?.message ||
                    "This contract was classified as 'other' and is currently out of scope for the automated clause/risk analysis pipeline."}
                </p>
              </div>

              <span className="rounded-full border border-slate-200 bg-slate-50 px-4 py-1 text-sm font-semibold text-slate-700">
                Out of scope
              </span>
            </div>

            <p className="mt-3 text-xs text-slate-500">
              Automated clause extraction and risk scoring are only available for
              supported contract types.
            </p>
          </section>
        </div>
      </div>
    );
  }


  const riskLevel = data?.risk_assessment?.risk_level;
  const riskScore = data?.risk_assessment?.contract_risk_score;
  const numClauses = data?.risk_assessment?.num_clauses;
  const missingClauses = data?.risk_assessment?.missing_clauses || [];

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* HEADER */}
        <header>
          <h1 className="text-3xl font-bold text-[#0B3D91]">
            Contract Analysis Report
          </h1>
          <p className="text-slate-500">{data?.filename || filename}</p>
        </header>

        {/* OVERVIEW */}
        <section className="rounded-xl border bg-white p-6 shadow">
          <h2 className="mb-3 text-lg font-semibold text-[#0B3D91]">
            Contract Overview
          </h2>

          <div className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
            <p>
              <strong>Contract Type:</strong>{" "}
              <span className="capitalize">{data?.contract_type || "unknown"}</span>
            </p>

            <p>
              <strong>Risk Level:</strong>{" "}
              <span
                className={cn(
                  "font-semibold",
                  riskLevel === "HIGH"
                    ? "text-red-600"
                    : riskLevel === "MEDIUM"
                    ? "text-orange-600"
                    : "text-green-600"
                )}
              >
                {riskLevel || "UNKNOWN"}
              </span>
            </p>

            <p>
              <strong>Risk Score:</strong> {riskScore ?? "—"}
            </p>

            <p>
              <strong>Clauses Analysed:</strong> {numClauses ?? "—"}
            </p>
          </div>
        </section>

        {/* RISK SUMMARY */}
        <section className="rounded-xl border bg-white p-6 shadow">
          <h2 className="mb-3 text-lg font-semibold text-[#0B3D91]">
            Risk Summary
          </h2>

          <p className="text-sm text-slate-800">{data?.risk_assessment?.summary}</p>

          {missingClauses?.length > 0 && (
            <>
              <p className="mt-4 text-sm font-semibold text-slate-900">
                Missing Clauses
              </p>
              <ul className="mt-1 ml-6 list-disc text-sm text-slate-700">
                {missingClauses.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </>
          )}

          {/* ✅ Show contract-wide scoring context ONCE */}
          {contractWideContext.text && contractWideContext.coverage >= 0.6 && (
            <div className="mt-5 rounded-lg border bg-slate-50 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-semibold text-[#0B3D91]">
                  Contract-wide context used to adjust clause scoring
                </p>
                <span className="text-xs text-slate-500">
                  seen in {(contractWideContext.coverage * 100).toFixed(0)}% of clauses
                </span>
              </div>

              <p className="mt-1 text-xs text-slate-600">
                This context is contract-level (so it’s shown once here to avoid
                making it look like a clause-specific explanation).
              </p>

              {contractWideContext.bullets.length > 0 ? (
                <ul className="mt-3 ml-5 list-disc space-y-1 text-sm text-slate-700">
                  {contractWideContext.bullets.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm text-slate-700 whitespace-pre-wrap">
                  {contractWideContext.text}
                </p>
              )}
            </div>
          )}
        </section>

        {/* CLAUSE RISKS */}
        <section className="rounded-xl border bg-white p-6 shadow">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-[#0B3D91]">
              Clause-Level Risk Analysis
            </h2>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setClauseFilter("all")}
                className={cn(
                  "rounded-full border px-4 py-1 text-sm font-semibold transition",
                  clauseFilter === "all"
                    ? "border-[#0B3D91] bg-slate-50 text-[#0B3D91]"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                )}
              >
                All ({riskClauses.length})
              </button>

              <button
                onClick={() => setClauseFilter("risky")}
                className={cn(
                  "rounded-full border px-4 py-1 text-sm font-semibold transition",
                  clauseFilter === "risky"
                    ? "border-red-500 bg-red-50 text-red-700"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                )}
              >
                Risky ({riskyCount})
              </button>

              <button
                onClick={() => setClauseFilter("safe")}
                className={cn(
                  "rounded-full border px-4 py-1 text-sm font-semibold transition",
                  clauseFilter === "safe"
                    ? "border-green-500 bg-green-50 text-green-700"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                )}
              >
                Safe ({safeCount})
              </button>
            </div>
          </div>

          {filteredClauses.length === 0 ? (
            <p className="text-sm text-slate-500">No clauses to display.</p>
          ) : (
            <div className="space-y-5">
              {filteredClauses.map((clause, idx) => {
                const isRisky = clause?.risk_label === "risky";
                const decision = isRisky ? "RISKY" : "SAFE";
                const conf = clause?.risk_confidence;

                const { clausePart } = splitRiskReason(clause?.risk_reason);

                return (
                  <div key={idx} className="rounded-xl border bg-slate-50 p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold capitalize text-slate-900">
                          {formatClauseType(clause?.clause_type)}
                        </p>

                        <p className="mt-1 text-sm text-slate-700">
                          <span className="font-medium">Clause decision:</span>{" "}
                          <span
                            className={cn(
                              isRisky ? "text-red-700" : "text-green-700",
                              "font-semibold"
                            )}
                          >
                            {decision}
                          </span>{" "}
                          <span className="text-slate-400">•</span>{" "}
                          <span className="font-medium">confidence</span>{" "}
                          <span className="font-semibold text-slate-900">
                            {formatNum(conf, 6)}
                          </span>
                        </p>
                      </div>

                      <span
                        className={cn(
                          "rounded-full px-4 py-1 text-sm font-semibold",
                          isRisky
                            ? "bg-red-100 text-red-700"
                            : "bg-green-100 text-green-700"
                        )}
                      >
                        {decision}
                      </span>
                    </div>

                    {/* ✅ Clause-level explanation ONLY */}
                    {clausePart && (
                      <div className="mt-4 rounded-xl border bg-white p-4">
                        <p className="text-sm font-semibold text-slate-900">
                          Clause-level explanation
                        </p>
                        <p className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">
                          {clausePart}
                        </p>

                        {contractWideContext.text &&
                          contractWideContext.coverage >= 0.6 && (
                            <p className="mt-2 text-xs text-slate-500">
                              Note: contract-wide scoring context is shown once in
                              the Risk Summary.
                            </p>
                          )}
                      </div>
                    )}

                    <details className="mt-4 rounded-xl border bg-white p-4">
                      <summary className="cursor-pointer text-sm font-semibold text-[#0B3D91]">
                        View clause text
                      </summary>
                      <p className="mt-3 whitespace-pre-wrap text-xs text-slate-700">
                        {clause?.clause_text || "No clause text available."}
                      </p>
                    </details>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* EXTRACTED SPANS */}
        <section className="rounded-xl border bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-[#0B3D91]">
            Extracted Evidence
          </h2>

          {!data?.extracted_spans || data.extracted_spans.length === 0 ? (
            <p className="text-sm text-slate-500">No extracted spans available.</p>
          ) : (
            data.extracted_spans.map((span, idx) => (
              <div key={idx} className="mb-4 text-sm">
                <p className="font-semibold text-slate-900">{span?.question}</p>
                <p className="mt-1 italic text-slate-700">{span?.clause_text}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Score: {formatNum(span?.score, 4)}
                </p>
                <hr className="my-3" />
              </div>
            ))
          )}
        </section>

        {/* RAG QUESTION ANSWERING */}
        <section className="rounded-xl border bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-[#0B3D91]">
            Ask Questions About This Contract
          </h2>

          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What does this contract say about termination without cause?"
            className="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-[#0B3D91] focus:outline-none focus:ring-1 focus:ring-[#0B3D91]"
            rows={3}
          />

          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={askQuestion}
              disabled={asking}
              className="rounded-full bg-[#0B3D91] px-5 py-2 text-sm font-semibold text-white shadow transition hover:bg-[#082d6b] disabled:opacity-60"
            >
              {asking ? "Thinking…" : "Ask"}
            </button>

            {qaError && <span className="text-sm text-red-600">{qaError}</span>}
          </div>

          {qaResult && (
            <div className="mt-6 space-y-4">
              {/* Answer */}
              <div className="rounded-lg border bg-slate-50 p-4">
                <p className="mb-2 text-sm font-semibold text-[#0B3D91]">Answer</p>
                <p className="whitespace-pre-wrap text-sm text-slate-800">
                  {qaResult?.answer}
                </p>
              </div>

              {/* Contract Evidence */}
              <div className="rounded-lg border bg-white p-4">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-semibold text-[#0B3D91]">
                    Contract Evidence
                  </p>
                  <span className="text-xs text-slate-500">
                    {qaResult?.contract_evidence?.length || 0} snippets
                  </span>
                </div>

                {!qaResult.contract_evidence ||
                qaResult.contract_evidence.length === 0 ? (
                  <p className="text-sm text-slate-500">No evidence returned.</p>
                ) : (
                  <div className="space-y-2">
                    {qaResult.contract_evidence.map((ev, i) => {
                      const contractId = ev?.meta?.contract_id || "UNKNOWN";
                      const chunk = ev?.meta?.chunk_index ?? "?";
                      const score =
                        typeof ev?.score === "number"
                          ? ev.score.toFixed(4)
                          : ev?.score;

                      return (
                        <details
                          key={`${contractId}-${chunk}-${i}`}
                          className="rounded-md border bg-slate-50 p-3"
                        >
                          <summary className="cursor-pointer text-sm font-semibold text-slate-900">
                            {contractId} <span className="text-slate-400">•</span>{" "}
                            chunk {chunk} <span className="text-slate-400">•</span>{" "}
                            score {score}
                          </summary>
                          <p className="mt-2 whitespace-pre-wrap text-xs text-slate-700">
                            {ev?.text}
                          </p>
                        </details>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Sri Lankan Precedents */}
              <div className="rounded-lg border bg-white p-4">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-semibold text-[#0B3D91]">
                    Sri Lankan Case Law References
                  </p>
                  <span className="text-xs text-slate-500">
                    {qaResult?.sri_lanka_precedents?.length || 0} cases
                  </span>
                </div>

                {!qaResult.sri_lanka_precedents ||
                qaResult.sri_lanka_precedents.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No case law references used for this question.
                  </p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {qaResult.sri_lanka_precedents.map((c, i) => {
                      const caseId = c?.case_id || "UNKNOWN_CASE";
                      const p1 = c?.page_start ?? "?";
                      const p2 = c?.page_end ?? "?";
                      const score =
                        typeof c?.score === "number"
                          ? c.score.toFixed(4)
                          : c?.score;

                      return (
                        <li
                          key={`${caseId}-${i}`}
                          className="rounded-md border bg-slate-50 p-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-semibold">{caseId}</span>
                            <span className="text-xs text-slate-600">
                              score {score}
                            </span>
                          </div>
                          <div className="text-xs text-slate-600">
                            pp. {p1}–{p2}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
