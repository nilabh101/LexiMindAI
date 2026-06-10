import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Search, MapPin, Hash, BarChart2, ToggleLeft, ToggleRight, AlertCircle } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { searchInDocument } from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { PageHeader } from "../components/PageHeader";
import { LoadingSpinner } from "../components/LoadingSpinner";

function highlight(text: string, query: string, caseSensitive: boolean) {
  if (!query) return <span>{text}</span>;
  const flags = caseSensitive ? "g" : "gi";
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`(${escaped})`, flags);
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        new RegExp(escaped, flags).test(part) ? (
          <mark key={i} className="bg-amber-400/30 text-amber-200 rounded px-0.5">{part}</mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

export function SearchPage() {
  const [searchParams] = useSearchParams();
  const [docId, setDocId] = useState<number | null>(
    searchParams.get("doc") ? Number(searchParams.get("doc")) : null
  );
  const [query, setQuery]             = useState("");
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [submitted, setSubmitted]     = useState("");
  const [page, setPage]               = useState(1);
  const PER_PAGE = 20;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["search", docId, submitted, caseSensitive],
    queryFn: () => searchInDocument(docId!, submitted, caseSensitive).then(r => r.data),
    enabled: !!docId && !!submitted,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setPage(1);
    setSubmitted(query.trim());
  };

  const occurrences: any[] = data?.occurrences || [];
  const totalPages = Math.ceil(occurrences.length / PER_PAGE);
  const paginated  = occurrences.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="p-8">
      <PageHeader
        title="Search Document"
        subtitle="Find any word or phrase — every location, line number, and context snippet"
        icon={<Search size={22} />}
      />

      {/* Controls */}
      <div className="glass-card p-5 mb-6">
        <form onSubmit={handleSearch} className="flex flex-col gap-4">
          <DocSelector value={docId} onChange={id => { setDocId(id); setSubmitted(""); }} className="max-w-xs" />
          <div className="flex gap-3 items-center">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                className="input-field pl-9"
                placeholder="Enter a word or phrase…"
                value={query}
                onChange={e => setQuery(e.target.value)}
                disabled={!docId}
              />
            </div>
            <button
              type="button"
              onClick={() => setCaseSensitive(v => !v)}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all border ${
                caseSensitive
                  ? "border-brand-500/60 bg-brand-600/20 text-brand-300"
                  : "border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"
              }`}
            >
              {caseSensitive ? <ToggleRight size={16} /> : <ToggleLeft size={16} />} Aa
            </button>
            <button
              type="submit"
              disabled={!docId || !query.trim()}
              className="btn-primary flex items-center gap-2 disabled:opacity-40"
            >
              <Search size={14} /> Search
            </button>
          </div>
        </form>
      </div>

      {!docId && (
        <div className="glass-card p-12 text-center text-slate-400">Select a document first, then enter a search term</div>
      )}
      {docId && !submitted && (
        <div className="glass-card p-12 text-center text-slate-500">Enter a word or phrase above and click Search</div>
      )}
      {isLoading && <LoadingSpinner text="Searching document…" />}
      {isError && (
        <div className="glass-card p-5 flex items-center gap-3 text-red-400">
          <AlertCircle size={17} /> <span>{(error as Error)?.message || "Search failed"}</span>
        </div>
      )}

      {data && submitted && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>

          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="glass-card p-4 text-center">
              <div className="text-3xl font-bold text-brand-400">{data.total_count}</div>
              <div className="text-xs text-slate-400 mt-1">Total Occurrences</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-3xl font-bold text-purple-400">{data.total_paragraphs_with_match}</div>
              <div className="text-xs text-slate-400 mt-1">Paragraphs Matched</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-lg font-bold text-emerald-400 break-all">"{submitted}"</div>
              <div className="text-xs text-slate-400 mt-1">Query</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-sm font-bold text-amber-400">{caseSensitive ? "Case Sensitive" : "Case Insensitive"}</div>
              <div className="text-xs text-slate-400 mt-1">Match Mode</div>
            </div>
          </div>

          {data.total_count === 0 ? (
            <div className="glass-card p-12 text-center">
              <Search size={36} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No matches for <span className="text-white font-medium">"{submitted}"</span></p>
            </div>
          ) : (
            <>
              {/* Paragraph distribution */}
              {data.paragraph_distribution?.length > 0 && (
                <div className="glass-card p-5 mb-5">
                  <h3 className="section-title mb-3"><BarChart2 size={15} className="text-brand-400" /> Paragraph Distribution</h3>
                  <div className="flex flex-wrap gap-2">
                    {data.paragraph_distribution.map((p: any) => (
                      <span key={p.paragraph} className="px-3 py-1.5 rounded-xl bg-brand-600/20 border border-brand-500/30 text-sm text-brand-300">
                        ¶{p.paragraph} <span className="text-xs opacity-70">×{p.count}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Occurrences list */}
              <div className="glass-card overflow-hidden">
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                  <h3 className="font-semibold text-white flex items-center gap-2">
                    <MapPin size={14} className="text-brand-400" /> All Occurrences
                    <span className="text-xs text-slate-500 font-normal">
                      ({(page-1)*PER_PAGE+1}–{Math.min(page*PER_PAGE, occurrences.length)} of {occurrences.length})
                    </span>
                  </h3>
                  {totalPages > 1 && (
                    <div className="flex items-center gap-2">
                      <button disabled={page===1}           onClick={()=>setPage(p=>p-1)} className="px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 text-sm hover:bg-white/10 disabled:opacity-30">‹ Prev</button>
                      <span className="text-xs text-slate-400">{page} / {totalPages}</span>
                      <button disabled={page===totalPages}  onClick={()=>setPage(p=>p+1)} className="px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 text-sm hover:bg-white/10 disabled:opacity-30">Next ›</button>
                    </div>
                  )}
                </div>

                <AnimatePresence mode="wait">
                  <motion.div key={page} initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} className="divide-y divide-white/5">
                    {paginated.map((occ: any) => (
                      <div key={occ.occurrence_number} className="p-4 hover:bg-white/5 transition-colors">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-xs font-mono bg-brand-600/20 text-brand-300 px-2 py-0.5 rounded-lg border border-brand-500/30">
                            #{occ.occurrence_number}
                          </span>
                          <span className="flex items-center gap-1 text-xs text-slate-400"><Hash size={10} />Line {occ.line}</span>
                          <span className="flex items-center gap-1 text-xs text-slate-500"><MapPin size={10} />Char {occ.char_position}</span>
                        </div>
                        <p className="text-sm text-slate-300 leading-relaxed font-mono">
                          {highlight(occ.snippet, submitted, caseSensitive)}
                        </p>
                      </div>
                    ))}
                  </motion.div>
                </AnimatePresence>
              </div>
            </>
          )}
        </motion.div>
      )}
    </div>
  );
}
