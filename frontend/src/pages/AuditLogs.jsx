import { useEffect, useState } from "react";
import axios from "axios";
import { ShieldCheck, Link as LinkIcon, RefreshCw, FileSearch } from "lucide-react";

const API = "http://localhost:8000";

export default function AuditLogs() {
  const [verify, setVerify] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [anchors, setAnchors] = useState([]);
  const [selectedProof, setSelectedProof] = useState(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setSelectedProof(null);
    try {
      const [v, c, a] = await Promise.all([
        axios.get(`${API}/api/audit/verify`),
        axios.get(`${API}/api/audit/chain?limit=200`),
        axios.get(`${API}/api/audit/anchors?limit=50`),
      ]);
      setVerify(v.data);
      setBlocks(c.data);
      setAnchors(a.data);
    } catch (e) {
      console.error(e);
      alert("Failed to load audit data. Check backend + /docs.");
    } finally {
      setLoading(false);
    }
  };

  const viewProof = async (blockIndex) => {
    try {
      const res = await axios.get(`${API}/api/audit/proof/${blockIndex}`);
      setSelectedProof(res.data);
    } catch (e) {
      console.error(e);
      const msg = e?.response?.data?.detail || "Could not load proof.";
      alert(msg);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const chainOk = verify?.ok === true;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8F9FA] via-white to-[#ECEFF1] px-4 py-10 font-['Roboto',sans-serif] text-slate-800">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h2 className="text-[#0B3D91] text-2xl font-bold">Audit Logs</h2>
            <p className="text-sm text-slate-600">
              Read-only view of the tamper-evident ledger and on-chain anchor batches.
            </p>
          </div>

          <button
            onClick={refresh}
            className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-[#0B3D91] shadow-sm ring-1 ring-slate-200 transition hover:bg-[#0B3D91]/5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Status row */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <span className={`inline-flex h-10 w-10 items-center justify-center rounded-full ${chainOk ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"}`}>
                <ShieldCheck className="h-5 w-5" />
              </span>
              <div>
                <p className="text-sm text-slate-500">Ledger integrity</p>
                <p className="font-semibold">
                  {verify ? (chainOk ? "Chain OK" : "BROKEN") : "Loading..."}
                </p>
              </div>
            </div>
            {verify && !chainOk && (
              <p className="mt-3 text-sm text-rose-600">
                Broken at index: {verify.broken_at_index ?? "unknown"}
              </p>
            )}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-[#0B3D91]/10 text-[#0B3D91]">
                <LinkIcon className="h-5 w-5" />
              </span>
              <div>
                <p className="text-sm text-slate-500">Anchors</p>
                <p className="font-semibold">{anchors.length}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Each anchor batches a range of audit blocks into one Merkle root.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-50 text-slate-700">
                <FileSearch className="h-5 w-5" />
              </span>
              <div>
                <p className="text-sm text-slate-500">Blocks loaded</p>
                <p className="font-semibold">{blocks.length}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Showing up to 200 most recent blocks (chronological).
            </p>
          </div>
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Blocks */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-base font-semibold text-slate-800">Audit Chain</h3>
            <p className="mt-1 text-xs text-slate-500">Click “Proof” only for anchored blocks.</p>

            <div className="mt-4 max-h-[520px] overflow-auto rounded-xl border border-slate-100">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-slate-100">
                    <th className="px-3 py-2 text-xs font-semibold text-slate-500">#</th>
                    <th className="px-3 py-2 text-xs font-semibold text-slate-500">Action</th>
                    <th className="px-3 py-2 text-xs font-semibold text-slate-500">Contract</th>
                    <th className="px-3 py-2 text-xs font-semibold text-slate-500">Anchor</th>
                    <th className="px-3 py-2 text-xs font-semibold text-slate-500"></th>
                  </tr>
                </thead>
                <tbody>
                  {blocks.map((b) => {
                    const anchored = b.anchor_id !== null && b.anchor_id !== undefined;
                    return (
                      <tr key={b.block_index} className="border-b border-slate-50 hover:bg-[#0B3D91]/5">
                        <td className="px-3 py-2 font-mono text-xs">{b.block_index}</td>
                        <td className="px-3 py-2">{b.action_type}</td>
                        <td className="px-3 py-2 text-xs text-slate-600">
                          {b.contract_id || "-"}
                        </td>
                        <td className="px-3 py-2 text-xs">
                          {anchored ? (
                            <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">
                              #{b.anchor_id}
                            </span>
                          ) : (
                            <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-600">
                              unanchored
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button
                            disabled={!anchored}
                            onClick={() => viewProof(b.block_index)}
                            className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                              anchored
                                ? "bg-[#0B3D91]/10 text-[#0B3D91] hover:bg-[#0B3D91]/15"
                                : "bg-slate-100 text-slate-400 cursor-not-allowed"
                            }`}
                          >
                            Proof
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {blocks.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                        No audit blocks loaded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Anchors + Proof panel */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-800">Anchor Batches</h3>
              <div className="mt-4 max-h-[260px] overflow-auto rounded-xl border border-slate-100">
                <table className="w-full text-left text-sm">
                  <thead className="sticky top-0 bg-white">
                    <tr className="border-b border-slate-100">
                      <th className="px-3 py-2 text-xs font-semibold text-slate-500">Anchor</th>
                      <th className="px-3 py-2 text-xs font-semibold text-slate-500">Range</th>
                      <th className="px-3 py-2 text-xs font-semibold text-slate-500">Network</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anchors.map((a) => (
                      <tr key={a.anchor_id} className="border-b border-slate-50">
                        <td className="px-3 py-2 font-mono text-xs">#{a.anchor_id}</td>
                        <td className="px-3 py-2 text-xs text-slate-600">
                          {a.block_start}..{a.block_end}
                        </td>
                        <td className="px-3 py-2 text-xs text-slate-600">{a.network || "-"}</td>
                      </tr>
                    ))}
                    {anchors.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                          No anchors yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-base font-semibold text-slate-800">Proof Bundle</h3>
              <p className="mt-1 text-xs text-slate-500">
                Loaded when you click “Proof” for an anchored block.
              </p>

              {!selectedProof ? (
                <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-white/80 p-6 text-sm text-slate-500">
                  No proof selected.
                </div>
              ) : (
                <>
                    <pre className="mt-4 max-h-[320px] overflow-auto rounded-xl border border-slate-100 bg-slate-50 p-4 text-xs text-slate-800">
                    {JSON.stringify(selectedProof, null, 2)}
                    </pre>

                    <button
                    onClick={async () => {
                        const idx = selectedProof.block_index;
                        const r = await axios.get(`${API}/api/audit/verify-inclusion/${idx}`);
                        alert(r.data.ok ? " Inclusion verified" : " Inclusion failed");
                    }}
                    className="mt-3 rounded-full bg-[#0B3D91]/10 px-4 py-2 text-xs font-semibold text-[#0B3D91] hover:bg-[#0B3D91]/15"
                    >
                    Verify Inclusion
                    </button>
                </>
                )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
