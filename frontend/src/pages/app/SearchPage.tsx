import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Search as SearchIcon } from "lucide-react";
import { searchAcademic } from "../../lib/api";

interface Results {
  subjects: any[];
  chapters: any[];
  concepts: any[];
  notes: any[];
  questions: any[];
  documents: any[];
  chunks: any[];
}

const EMPTY: Results = {
  subjects: [], chapters: [], concepts: [], notes: [], questions: [], documents: [], chunks: [],
};

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const [term, setTerm] = useState(query);
  const [results, setResults] = useState<Results>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { setTerm(query); }, [query]);

  useEffect(() => {
    if (!query.trim()) { setResults(EMPTY); return; }
    let cancelled = false;
    setLoading(true);
    setError(null);
    searchAcademic(query)
      .then(res => { if (!cancelled) setResults({ ...EMPTY, ...res.data }); })
      .catch(e => { if (!cancelled) setError(e?.message || "Search failed"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [query]);

  const total =
    results.subjects.length + results.chapters.length + results.concepts.length +
    results.notes.length + results.questions.length + results.documents.length +
    results.chunks.length;

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="mb-6">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{title}</h2>
      <div className="space-y-2">{children}</div>
    </div>
  );

  const Row = ({ to, primary, secondary }: { to?: string; primary: string; secondary?: string }) => {
    const body = (
      <div className="bg-white/3 border border-white/6 rounded-xl px-4 py-3 hover:bg-white/5 transition-all">
        <div className="text-sm text-white">{primary}</div>
        {secondary && <div className="text-xs text-slate-500 mt-0.5">{secondary}</div>}
      </div>
    );
    return to ? <Link to={to}>{body}</Link> : body;
  };

  return (
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-1">Search</h1>
      <p className="text-slate-400 text-sm mb-6">
        Searches your curriculum, notes, questions and uploaded documents.
      </p>

      <form
        className="flex gap-2 mb-8"
        onSubmit={e => { e.preventDefault(); setParams(term.trim() ? { q: term.trim() } : {}); }}
      >
        <div className="flex-1 flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4">
          <SearchIcon size={15} className="text-slate-500 shrink-0" />
          <input
            value={term}
            onChange={e => setTerm(e.target.value)}
            placeholder="Search concepts, notes, PYQs, documents…"
            className="flex-1 bg-transparent py-3 text-sm text-white outline-none"
          />
        </div>
        <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 rounded-xl text-sm font-semibold">
          Search
        </button>
      </form>

      {error && <p className="text-sm text-red-300 mb-4">{error}</p>}
      {loading && <p className="text-sm text-slate-400">Searching…</p>}

      {!loading && query && total === 0 && !error && (
        <p className="text-sm text-slate-500">No matches for “{query}”.</p>
      )}

      {results.concepts.length > 0 && (
        <Section title={`Concepts (${results.concepts.length})`}>
          {results.concepts.map((c: any) => (
            <Row key={c.id} to={`/app/concepts/${c.id}`} primary={c.name} secondary={c.description || c.subjectId} />
          ))}
        </Section>
      )}
      {results.subjects.length > 0 && (
        <Section title={`Subjects (${results.subjects.length})`}>
          {results.subjects.map((s: any) => (
            <Row key={s.id} to={`/app/subjects/${s.id}`} primary={s.name} secondary={s.description} />
          ))}
        </Section>
      )}
      {results.chapters.length > 0 && (
        <Section title={`Chapters (${results.chapters.length})`}>
          {results.chapters.map((c: any) => (
            <Row key={c.id} to={`/app/chapters/${c.id}`} primary={c.name} secondary={c.description} />
          ))}
        </Section>
      )}
      {results.notes.length > 0 && (
        <Section title={`Notes (${results.notes.length})`}>
          {results.notes.map((n: any) => (
            <Row key={n.id} to={`/app/notes/${n.id}`} primary={n.title} secondary={n.source} />
          ))}
        </Section>
      )}
      {results.questions.length > 0 && (
        <Section title={`Questions (${results.questions.length})`}>
          {results.questions.map((q: any) => (
            <Row key={q.id} primary={q.question} secondary={[q.source, q.year].filter(Boolean).join(" · ")} />
          ))}
        </Section>
      )}
      {results.documents.length > 0 && (
        <Section title={`Documents (${results.documents.length})`}>
          {results.documents.map((d: any) => (
            <Row key={d.id} to={`/app/library/${d.id}`} primary={d.filename} secondary={d.status} />
          ))}
        </Section>
      )}
      {results.chunks.length > 0 && (
        <Section title={`Passages (${results.chunks.length})`}>
          {results.chunks.map((c: any) => (
            <Row key={c.id} to={`/app/library/${c.documentId}`} primary={c.snippet}
              secondary={c.page ? `Page ${c.page}` : undefined} />
          ))}
        </Section>
      )}
    </div>
  );
}
