/**
 * AnalysisPage — Word Analysis + Sentiment + AI Summary combined in one page.
 * Select a document once; tabs switch between the three views.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3, MessageSquare, BookOpen, Search,
} from "lucide-react";
import { useLocation } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Treemap,
  PieChart, Pie, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
} from "recharts";
import {
  getWordAnalysis, getWordCloud, getLexicalDiversity,
  getSentiment, getEmotions, getSummary, getDocumentStats,
} from "../lib/api";
import { DocSelector } from "../components/DocSelector";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { KpiCard } from "../components/KpiCard";

const COLORS = ["#6366f1","#8b5cf6","#a855f7","#ec4899","#06b6d4","#10b981","#f59e0b","#ef4444"];
const SENT_COLORS: Record<string,string> = { positive:"#22c55e", negative:"#ef4444", neutral:"#94a3b8", mixed:"#f59e0b" };
const EMOT_COLORS = ["#6366f1","#ec4899","#f59e0b","#ef4444","#10b981","#06b6d4","#8b5cf6","#f97316"];

type Tab = "words" | "sentiment" | "summary";

// ─── Word Analysis sub-view ───────────────────────────────────────────────────
function WordsTab({ docId }: { docId: number }) {
  const [topN, setTopN] = useState(25);
  const [useStemming, setUseStemming] = useState(false);
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"bar"|"table"|"cloud"|"treemap">("bar");

  const { data, isLoading } = useQuery({
    queryKey: ["words", docId, topN, useStemming],
    queryFn: () => getWordAnalysis(docId, topN, useStemming).then(r => r.data),
  });

  const { data: statsData } = useQuery({
    queryKey: ["stats", docId],
    queryFn: () => getDocumentStats(docId).then(r => r.data),
  });

  const { data: wcData, isLoading: wcLoading } = useQuery({
    queryKey: ["wordcloud", docId],
    queryFn: () => getWordCloud(docId).then(r => r.data),
    enabled: view === "cloud",
  });

  const { data: lexData } = useQuery({
    queryKey: ["lexical", docId],
    queryFn: () => getLexicalDiversity(docId).then(r => r.data),
  });

  const words: any[] = data?.frequency || [];
  const filtered = words.filter(w => !search || w.word.toLowerCase().includes(search.toLowerCase()));

  if (isLoading) return <LoadingSpinner text="Analyzing words…" />;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-5">
        <select value={topN} onChange={e => setTopN(Number(e.target.value))} className="input-field w-28">
          {[10,25,50,100,200].map(n => <option key={n} value={n}>Top {n}</option>)}
        </select>
        <select value={useStemming ? "stem" : "lemma"} onChange={e => setUseStemming(e.target.value==="stem")} className="input-field w-44">
          <option value="lemma">Lemmatization</option>
          <option value="stem">Stemming (Porter)</option>
        </select>
      </div>

      {/* Stats */}
      {statsData && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-5">
          {[
            { label:"Words",      val: statsData.word_count?.toLocaleString(),        color:"text-brand-400" },
            { label:"Sentences",  val: statsData.sentence_count?.toLocaleString(),    color:"text-purple-400" },
            { label:"Paragraphs", val: statsData.paragraph_count?.toLocaleString(),   color:"text-blue-400" },
            { label:"Unique Words",val: statsData.unique_word_count?.toLocaleString(),color:"text-emerald-400" },
            { label:"Read Time",  val: `${statsData.reading_time_minutes}m`,          color:"text-amber-400" },
            { label:"Grade Level",val: `Grade ${statsData.reading_grade_level}`,      color:"text-pink-400" },
          ].map(({label,val,color}) => (
            <div key={label} className="glass-card p-3 text-center">
              <div className={`text-lg font-bold ${color}`}>{val ?? "—"}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Readability */}
      {statsData && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          <div className="glass-card p-4">
            <div className="text-xs text-slate-400 mb-1">Flesch Reading Ease</div>
            <div className="text-2xl font-bold text-brand-400">{statsData.flesch_reading_ease ?? "—"}</div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
              <div className="bg-brand-500 h-1.5 rounded-full" style={{ width:`${Math.min(100,Math.max(0,statsData.flesch_reading_ease))}%` }} />
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-slate-400 mb-1">Lexical Diversity</div>
            <div className="text-2xl font-bold text-purple-400">{lexData?.lexical_diversity?.toFixed(3) ?? "—"}</div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-slate-400 mb-1">Avg Sentence Length</div>
            <div className="text-2xl font-bold text-emerald-400">{statsData.average_sentence_length ?? "—"} <span className="text-sm font-normal text-slate-400">words</span></div>
          </div>
        </div>
      )}

      {/* View tabs */}
      <div className="flex gap-2 mb-4">
        {(["bar","table","cloud","treemap"] as const).map(t => (
          <button key={t} onClick={() => setView(t)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${view===t ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"}`}>
            {t.charAt(0).toUpperCase()+t.slice(1)}
          </button>
        ))}
      </div>

      {view === "bar" && (
        <div className="glass-card p-6">
          <h3 className="section-title mb-4">Top {topN} Words</h3>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={words.slice(0,topN)} margin={{ bottom:60 }}>
              <XAxis dataKey="word" angle={-45} textAnchor="end" tick={{ fill:"#94a3b8", fontSize:11 }} />
              <YAxis tick={{ fill:"#94a3b8", fontSize:11 }} />
              <Tooltip contentStyle={{ background:"#1a1a2e", border:"1px solid #2d2d4a", borderRadius:8 }} />
              <Bar dataKey="count" radius={[4,4,0,0]}>
                {words.slice(0,topN).map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {view === "table" && (
        <div className="glass-card overflow-hidden">
          <div className="p-4 border-b border-white/10 flex items-center gap-2">
            <Search size={14} className="text-slate-400" />
            <input className="input-field text-sm" placeholder="Filter words…" value={search} onChange={e=>setSearch(e.target.value)} />
            <span className="text-xs text-slate-500 shrink-0">{filtered.length} results</span>
          </div>
          <div className="overflow-y-auto max-h-[480px]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-[#1a1a2e]">
                <tr className="border-b border-white/10">
                  <th className="p-3 text-left text-slate-400 font-medium">Rank</th>
                  <th className="p-3 text-left text-slate-400 font-medium">Word</th>
                  <th className="p-3 text-right text-slate-400 font-medium">Count</th>
                  <th className="p-3 text-right text-slate-400 font-medium">%</th>
                  <th className="p-3 text-right text-slate-400 font-medium w-28">Bar</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((w:any) => (
                  <tr key={w.rank} className="border-b border-white/5 hover:bg-white/5">
                    <td className="p-3 text-slate-500 text-xs">#{w.rank}</td>
                    <td className="p-3 font-medium text-white">{w.word}</td>
                    <td className="p-3 text-right text-brand-300 font-mono">{w.count}</td>
                    <td className="p-3 text-right text-slate-400">{w.percentage}%</td>
                    <td className="p-3">
                      <div className="w-full bg-white/10 rounded-full h-1.5">
                        <div className="bg-brand-500 h-1.5 rounded-full" style={{ width:`${Math.min(100,w.percentage*5)}%` }} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {view === "cloud" && (
        <div className="glass-card p-6">
          {wcLoading && <LoadingSpinner text="Generating word cloud…" />}
          {wcData?.image_base64 && <img src={`data:image/png;base64,${wcData.image_base64}`} alt="Word Cloud" className="w-full rounded-xl" />}
          {wcData && !wcData.image_base64 && wcData.data && (
            <div className="flex flex-wrap gap-2 justify-center p-4">
              {wcData.data.slice(0,80).map((w:any,i:number) => (
                <span key={i} className="text-brand-300 hover:text-white transition-colors cursor-default"
                  style={{ fontSize:`${Math.max(0.75,Math.min(2.5,w.weight*8))}rem` }}>{w.text}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {view === "treemap" && (
        <div className="glass-card p-6">
          <h3 className="section-title mb-4">Vocabulary Treemap</h3>
          <ResponsiveContainer width="100%" height={420}>
            <Treemap data={words.slice(0,40).map(w=>({name:w.word,size:w.count}))} dataKey="size" aspectRatio={4/3}
              content={(({x,y,width,height,name}:any)=>(
                <g>
                  <rect x={x} y={y} width={width} height={height} fill={COLORS[Math.floor(Math.random()*COLORS.length)]} fillOpacity={0.85} stroke="#0f0f1a" strokeWidth={2} rx={4}/>
                  {width>40&&height>20&&<text x={x+width/2} y={y+height/2} textAnchor="middle" dominantBaseline="middle" fill="white" fontSize={Math.min(14,width/6)}>{name}</text>}
                </g>
              )) as any}
            />
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  );
}

// ─── Sentiment sub-view ───────────────────────────────────────────────────────
function SentimentTab({ docId }: { docId: number }) {
  const [view, setView] = useState<"sentiment"|"emotions">("sentiment");

  const { data: sentData, isLoading: sentLoading } = useQuery({
    queryKey: ["sentiment", docId],
    queryFn: () => getSentiment(docId).then(r => r.data),
  });

  const { data: emotData, isLoading: emotLoading } = useQuery({
    queryKey: ["emotions", docId],
    queryFn: () => getEmotions(docId).then(r => r.data),
    enabled: view === "emotions",
  });

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="flex gap-2 mb-5">
        {(["sentiment","emotions"] as const).map(t => (
          <button key={t} onClick={()=>setView(t)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${view===t?"bg-brand-600 text-white":"bg-white/5 text-slate-400 hover:text-white"}`}>
            {t.charAt(0).toUpperCase()+t.slice(1)}
          </button>
        ))}
      </div>

      {view==="sentiment" && sentLoading && <LoadingSpinner text="Analyzing sentiment…" />}
      {view==="sentiment" && sentData && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Overall Sentiment" value={(sentData.sentiment_label||"").toUpperCase()} color="green" delay={0.05} />
            <KpiCard label="Polarity" value={sentData.polarity?.toFixed(3)} color="brand" delay={0.1} />
            <KpiCard label="Subjectivity" value={sentData.subjectivity?.toFixed(3)} color="yellow" delay={0.15} />
            <KpiCard label="Sentences" value={sentData.sentence_sentiments?.length ?? "—"} color="purple" delay={0.2} />
          </div>

          {/* Sentence list */}
          <div className="glass-card p-5">
            <h3 className="section-title mb-3">Sentence-Level Sentiments</h3>
            <div className="space-y-2 max-h-80 overflow-y-auto">
              {(sentData.sentence_sentiments || []).slice(0,30).map((s:any,i:number) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                  <span className="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium capitalize"
                    style={{ background:`${SENT_COLORS[s.label]}22`, color:SENT_COLORS[s.label] }}>
                    {s.label}
                  </span>
                  <span className="text-sm text-slate-300 flex-1 leading-relaxed">{s.sentence}</span>
                  <span className="text-xs text-slate-500 shrink-0 font-mono">{s.polarity?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {view==="emotions" && emotLoading && <LoadingSpinner text="Detecting emotions…" />}
      {view==="emotions" && emotData && (
        <div className="grid grid-cols-2 gap-6">
          <div className="glass-card p-6">
            <h3 className="section-title mb-3">Emotion Radar</h3>
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={Object.entries(emotData.emotions||{}).map(([k,v])=>({ emotion:k, value:v as number }))}>
                <PolarGrid stroke="#2d2d4a" />
                <PolarAngleAxis dataKey="emotion" tick={{ fill:"#94a3b8", fontSize:11 }} />
                <Radar name="Score" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} strokeWidth={2} />
                <Tooltip contentStyle={{ background:"#1a1a2e", border:"1px solid #2d2d4a", borderRadius:8 }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="glass-card p-6">
            <h3 className="section-title mb-3">Emotion Scores</h3>
            <div className="space-y-3">
              {Object.entries(emotData.emotions||{}).map(([emotion,val]:any,i:number)=>(
                <div key={emotion} className="flex items-center gap-3">
                  <span className="text-sm text-slate-300 w-28 capitalize">{emotion}</span>
                  <div className="flex-1 bg-white/10 rounded-full h-2 overflow-hidden">
                    <motion.div initial={{ width:0 }} animate={{ width:`${val}%` }} transition={{ delay:i*0.05, duration:0.6 }}
                      className="h-full rounded-full" style={{ background:EMOT_COLORS[i%EMOT_COLORS.length] }} />
                  </div>
                  <span className="text-xs text-slate-400 w-10 text-right">{(val as number).toFixed(1)}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 p-3 rounded-xl bg-white/5 text-center">
              <div className="text-xs text-slate-400">Dominant Emotion</div>
              <div className="text-xl font-bold text-brand-300 capitalize mt-1">{emotData.dominant_emotion}</div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ─── Summary sub-view ─────────────────────────────────────────────────────────
function SummaryTab({ docId }: { docId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["summary", docId],
    queryFn: () => getSummary(docId).then(r => r.data),
  });

  if (isLoading) return <LoadingSpinner text="Generating AI summary…" />;
  if (!data) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
      {/* Executive */}
      <div className="glass-card p-6">
        <h3 className="section-title mb-3"><BookOpen size={15} className="text-brand-400" /> Executive Summary</h3>
        <p className="text-slate-300 leading-relaxed text-sm">{data.executive || "No summary available."}</p>
      </div>

      {/* Bullet points */}
      {data.bullet_points?.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="section-title mb-3"><BookOpen size={15} className="text-purple-400" /> Key Points</h3>
          <ul className="space-y-2">
            {data.bullet_points.map((pt: string, i: number) => (
              <li key={i} className="flex items-start gap-3 text-sm text-slate-300">
                <span className="text-brand-400 shrink-0 mt-0.5">•</span>
                <span className="leading-relaxed">{pt}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Key sentences */}
      {data.key_sentences?.length > 0 && (
        <div className="glass-card p-6">
          <h3 className="section-title mb-3"><BookOpen size={15} className="text-emerald-400" /> Most Important Sentences</h3>
          <div className="space-y-3">
            {data.key_sentences.map((s: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                <span className="text-xs bg-brand-600/30 text-brand-300 px-2 py-0.5 rounded-lg shrink-0">#{i+1}</span>
                <p className="text-sm text-slate-300 leading-relaxed flex-1">{s.sentence}</p>
                <span className="text-xs text-slate-500 shrink-0">{s.score}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Meta */}
      <div className="grid grid-cols-2 gap-3">
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold text-brand-400">{data.sentence_count}</div>
          <div className="text-xs text-slate-400 mt-1">Total Sentences</div>
        </div>
        <div className="glass-card p-4 text-center">
          <div className="text-2xl font-bold text-purple-400">{(data.summary_ratio*100).toFixed(0)}%</div>
          <div className="text-xs text-slate-400 mt-1">Compression Ratio</div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export function AnalysisPage() {
  const location = useLocation();
  const [docId, setDocId] = useState<number | null>(location.state?.docId ?? null);
  const [tab, setTab] = useState<Tab>("words");

  const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id:"words",     label:"Word Analysis",    icon:<BarChart3 size={14} /> },
    { id:"sentiment", label:"Sentiment",         icon:<MessageSquare size={14} /> },
    { id:"summary",   label:"AI Summary",        icon:<BookOpen size={14} /> },
  ];

  return (
    <div className="p-8">
      <PageHeader
        title="Document Analysis"
        subtitle="Word frequency, sentiment, and AI summary — all in one place"
        icon={<BarChart3 size={22} />}
      />

      {/* Doc selector + tab bar */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <DocSelector value={docId} onChange={id => { setDocId(id); }} className="max-w-xs flex-1" />
        {docId && (
          <div className="flex gap-2">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${tab===t.id ? "bg-brand-600 text-white" : "bg-white/5 text-slate-400 hover:text-white"}`}>
                {t.icon}{t.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {!docId && (
        <div className="glass-card p-14 text-center text-slate-400">
          Select a document to start analysis
        </div>
      )}

      {docId && (
        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0, y:-8 }} transition={{ duration:0.2 }}>
            {tab === "words"     && <WordsTab     docId={docId} />}
            {tab === "sentiment" && <SentimentTab docId={docId} />}
            {tab === "summary"   && <SummaryTab   docId={docId} />}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
