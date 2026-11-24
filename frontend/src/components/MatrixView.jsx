import React, { useEffect, useState } from 'react';
import { Download, RefreshCw, AlertTriangle, Award, Table as TableIcon } from 'lucide-react';
import { fetchMatrix } from '../api';

export default function MatrixView() {
  const [matrixData, setMatrixData] = useState({
    matrix_rows: [],
    contradictions: [],
    outperforms: []
  });
  const [isLoading, setIsLoading] = useState(true);

  const loadMatrix = async () => {
    setIsLoading(true);
    try {
      const data = await fetchMatrix();
      setMatrixData(data);
    } catch (err) {
      console.error("Failed to load matrix:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMatrix();
  }, []);

  const exportCSV = () => {
    if (!matrixData.matrix_rows || matrixData.matrix_rows.length === 0) return;
    const headers = ["Paper Title", "Proposed Methods / Models", "Datasets Evaluated", "Metrics & Scores", "Known Limitations"];
    const rows = matrixData.matrix_rows.map(r => [
      `"${r["Paper Title"] || ""}"`,
      `"${r["Proposed Methods / Models"] || ""}"`,
      `"${r["Datasets Evaluated"] || ""}"`,
      `"${r["Metrics & Scores"] || ""}"`,
      `"${r["Known Limitations"] || ""}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `research_matrix_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-canvas p-6 overflow-y-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="font-heading font-bold text-xl tracking-tight text-black">
            CROSS-PAPER COMPARATIVE MATRIX
          </h2>
          <span className="font-mono text-xs text-gray-600 block">
            STRUCTURED SIDE-BY-SIDE SYNTHESIS ACROSS INGESTED LITERATURE
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadMatrix}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-black text-xs font-heading font-bold shadow-[2px_2px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5"
            title="Refresh Matrix"
          >
            <RefreshCw size={13} strokeWidth={2} />
            <span>REFRESH</span>
          </button>

          <button
            onClick={exportCSV}
            disabled={matrixData.matrix_rows.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-ochre border-2 border-black text-xs font-heading font-bold shadow-[3px_3px_0px_0px_#000] active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50"
          >
            <Download size={13} strokeWidth={2} />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] mb-8 overflow-hidden">
        {matrixData.matrix_rows.length === 0 ? (
          <div className="py-16 text-center font-mono text-xs text-gray-500">
            <TableIcon size={32} className="mx-auto mb-2 text-gray-400" />
            <span className="font-bold block text-sm">NO COMPARATIVE DATA AVAILABLE</span>
            <span>Upload research PDFs in the Chat tab or load sample benchmarks to generate this matrix.</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse font-sans text-xs">
              <thead>
                <tr className="bg-[#FFD166] border-b-2 border-black font-heading font-black text-[11px] tracking-wider text-black">
                  <th className="p-3.5 border-r-2 border-black w-48">PAPER TITLE</th>
                  <th className="p-3.5 border-r-2 border-black w-56">PROPOSED METHODOLOGY</th>
                  <th className="p-3.5 border-r-2 border-black w-48">DATASETS EVALUATED</th>
                  <th className="p-3.5 border-r-2 border-black">KEY METRICS & SCORES</th>
                  <th className="p-3.5 w-64 bg-[#FFDDD2] text-[#C94A4A]">KNOWN LIMITATIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black font-mono">
                {matrixData.matrix_rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-amber-50/40 transition-colors">
                    <td className="p-3.5 border-r-2 border-black font-bold text-black font-heading text-xs bg-canvas/30">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-[#00A896] border border-black inline-block shrink-0"></span>
                        <span>{row["Paper Title"]}</span>
                      </div>
                    </td>
                    <td className="p-3.5 border-r-2 border-black text-gray-900">
                      <span className="inline-block bg-[#E0F7FA] border border-black px-2 py-0.5 font-bold text-[11px]">
                        {row["Proposed Methods / Models"]}
                      </span>
                    </td>
                    <td className="p-3.5 border-r-2 border-black text-gray-900">
                      <span className="inline-block bg-[#FFF3E0] border border-black px-2 py-0.5 font-bold text-[11px]">
                        {row["Datasets Evaluated"]}
                      </span>
                    </td>
                    <td className="p-3.5 border-r-2 border-black text-gray-900 font-bold">
                      <span className="inline-block bg-[#D8F3DC] border border-black px-2 py-0.5 text-[11px] text-[#006644]">
                        {row["Metrics & Scores"]}
                      </span>
                    </td>
                    <td className="p-3.5 text-[#C94A4A] font-bold bg-[#FFF5F5]">
                      <span className="inline-block bg-[#FFEBEE] border border-[#C94A4A] px-2 py-0.5 text-[11px]">
                        {row["Known Limitations"]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Contradiction & Outperformance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Contradictions */}
        <div className="bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-5">
          <div className="flex items-center gap-2 border-b-2 border-black pb-2.5 mb-3 bg-[#FFDDD2] p-2 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            <AlertTriangle size={18} strokeWidth={2} className="text-[#C94A4A]" />
            <h3 className="font-heading font-black text-xs tracking-wider text-black">
              CONTRADICTIONS & DIVERGENT CLAIMS
            </h3>
          </div>

          {matrixData.contradictions.length === 0 ? (
            <p className="font-mono text-xs text-gray-500 py-4">
              No direct empirical contradictions documented between uploaded models.
            </p>
          ) : (
            <div className="space-y-3">
              {matrixData.contradictions.map((c, idx) => (
                <div key={idx} className="p-3 border-2 border-black bg-[#FFF5F5] text-xs font-mono shadow-[2px_2px_0px_0px_#000]">
                  <div className="font-bold text-[#C94A4A] mb-1 flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#C94A4A] border border-black inline-block"></span>
                    <span>{c.source} CONTRADICTS {c.target}</span>
                  </div>
                  <p className="text-black font-sans text-xs mb-2 leading-relaxed">{c.details}</p>
                  <span className="inline-block bg-[#FFD166] border border-black px-1.5 py-0.5 text-[10px] font-bold">
                    {c.citation}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Outperformance */}
        <div className="bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-5">
          <div className="flex items-center gap-2 border-b-2 border-black pb-2.5 mb-3 bg-[#D8F3DC] p-2 border-2 border-black shadow-[2px_2px_0px_0px_#000]">
            <Award size={18} strokeWidth={2} className="text-[#00A896]" />
            <h3 className="font-heading font-black text-xs tracking-wider text-black">
              DOCUMENTED OUTPERFORMANCE CLAIMS
            </h3>
          </div>

          {matrixData.outperforms.length === 0 ? (
            <p className="font-mono text-xs text-gray-500 py-4">
              No direct head-to-head outperformance claims recorded in the graph.
            </p>
          ) : (
            <div className="space-y-3">
              {matrixData.outperforms.map((o, idx) => (
                <div key={idx} className="p-3 border-2 border-black bg-[#F0FDF4] text-xs font-mono shadow-[2px_2px_0px_0px_#000]">
                  <div className="font-bold text-[#00A896] mb-1 flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-[#00A896] border border-black inline-block"></span>
                    <span>{o.source} OUTPERFORMS {o.target}</span>
                  </div>
                  <p className="text-black font-sans text-xs mb-2 leading-relaxed">{o.details}</p>
                  <span className="inline-block bg-[#FFD166] border border-black px-1.5 py-0.5 text-[10px] font-bold">
                    {o.citation}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
