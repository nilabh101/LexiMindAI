import { motion } from "framer-motion";
import { Brain, ArrowRight, Code2, Cpu, BarChart3, MessageSquare, Layers, Zap, Globe } from "lucide-react";

const EVOLUTION_STAGES = [
  {
    stage: 1, title: "Word Counting",
    description: "The journey begins — count how many times each word appears in a file.",
    code: `# Stage 1: Basic Word Counter
def count_words(filename):
    with open(filename) as f:
        text = f.read()
    words = text.split()
    return len(words)`,
    icon: Code2, color: "from-slate-500 to-slate-600",
  },
  {
    stage: 2, title: "Frequency Analysis",
    description: "Discover which words are most important by ranking their frequency.",
    code: `# Stage 2: Word Frequency
from collections import Counter

def word_frequency(text):
    words = text.lower().split()
    return Counter(words).most_common(10)`,
    icon: BarChart3, color: "from-blue-500 to-blue-600",
  },
  {
    stage: 3, title: "NLP Processing",
    description: "Apply tokenization, lemmatization, and stopword removal for clean analysis.",
    code: `# Stage 3: NLP Pipeline
import nltk
from nltk.stem import WordNetLemmatizer

def nlp_process(text):
    tokens = nltk.word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    clean = [lemmatizer.lemmatize(t.lower())
             for t in tokens if t.isalpha()
             and t not in stopwords]
    return Counter(clean)`,
    icon: Cpu, color: "from-indigo-500 to-indigo-600",
  },
  {
    stage: 4, title: "Sentiment Analysis",
    description: "Determine the emotional tone — positive, negative, or neutral.",
    code: `# Stage 4: Sentiment Analysis
from textblob import TextBlob

def analyze_sentiment(text):
    blob = TextBlob(text)
    return {
        "polarity": blob.sentiment.polarity,
        "label": "positive" if blob.sentiment.polarity > 0.1
                 else "negative" if blob.sentiment.polarity < -0.1
                 else "neutral"
    }`,
    icon: MessageSquare, color: "from-emerald-500 to-emerald-600",
  },
  {
    stage: 5, title: "Topic Modeling",
    description: "Use TF-IDF and keyword clustering to discover document themes.",
    code: `# Stage 5: Topic Detection
from sklearn.feature_extraction.text import TfidfVectorizer

def detect_topics(documents):
    vectorizer = TfidfVectorizer(max_features=1000)
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    return feature_names[:20]  # top topic keywords`,
    icon: Layers, color: "from-amber-500 to-amber-600",
  },
  {
    stage: 6, title: "AI Understanding",
    description: "Apply transformer models and semantic embeddings for deep understanding.",
    code: `# Stage 6: Semantic AI
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

def semantic_similarity(text1, text2):
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    return np.dot(emb1, emb2) / (
        np.linalg.norm(emb1) * np.linalg.norm(emb2))`,
    icon: Brain, color: "from-purple-500 to-purple-600",
  },
  {
    stage: 7, title: "Document Intelligence",
    description: "Full-stack AI platform: entity extraction, DNA, bias detection, quiz generation, auto-reports.",
    code: `# Stage 7: Document Intelligence Platform
class LexiMindAI:
    def analyze(self, document):
        return {
            "stats":    compute_stats(document),
            "sentiment":analyze_document_sentiment(document),
            "emotions": analyze_emotions(document),
            "topics":   detect_topics(document),
            "entities": extract_entities(document),
            "dna":      compute_document_dna(document),
            "summary":  generate_summaries(document),
            "insights": generate_insights(...),
            "bias":     analyze_bias(document),
            "quiz":     generate_quiz(document),
            "cards":    generate_flashcards(document),
            "report":   generate_pdf_report(...),
        }`,
    icon: Globe, color: "from-brand-500 to-purple-600",
  },
];

const TECH_STACK = [
  { name: "FastAPI",        category: "Backend",   color: "#009688" },
  { name: "React 18",       category: "Frontend",  color: "#61dafb" },
  { name: "spaCy",          category: "NLP",       color: "#09a3d5" },
  { name: "TextBlob",       category: "NLP",       color: "#4caf50" },
  { name: "scikit-learn",   category: "ML",        color: "#f57c00" },
  { name: "SQLAlchemy",     category: "Database",  color: "#d35400" },
  { name: "NLTK",           category: "NLP",       color: "#3776ab" },
  { name: "Recharts",       category: "Viz",       color: "#8884d8" },
  { name: "Framer Motion",  category: "UI/UX",     color: "#bb86fc" },
  { name: "TailwindCSS",    category: "Styling",   color: "#38bdf8" },
  { name: "Pydantic",       category: "Validation",color: "#e74c3c" },
  { name: "TypeScript",     category: "Language",  color: "#3178c6" },
];

const MODULES = [
  "Smart Document Ingestion (500 MB)",
  "Document Dashboard & KPIs",
  "Word Frequency Analysis",
  "TF-IDF Keyword Extraction",
  "Word Cloud Generator",
  "Vocabulary Treemap",
  "Sentiment Analysis",
  "Sentence-Level Sentiment",
  "Emotion Radar (8 emotions)",
  "AI Extractive Summarizer",
  "Topic Detection",
  "Named Entity Recognition",
  "Document DNA Fingerprint",
  "Writing Style Classifier",
  "In-Document Search",
  "Quiz Generator (MCQ)",
  "Flashcard Generator",
  "Practice Mode + Grading",
  "Bias Detection",
  "AI Insight Generator",
];

export function CorePage() {
  return (
    <div className="p-8 max-w-5xl mx-auto">

      {/* Hero */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-14">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-600/20 border border-brand-500/30 text-brand-300 text-sm mb-6">
          <Brain size={14} /> Core of the Project
        </div>
        <h1 className="text-5xl font-bold gradient-text mb-4">LexiMind AI</h1>
        <p className="text-xl text-slate-300 mb-2">Transforming Documents into Actionable Intelligence</p>
        <p className="text-slate-500 max-w-2xl mx-auto">
          How a simple word frequency counter evolved into a production-grade AI document analytics platform —
          from file I/O to enterprise NLP.
        </p>
      </motion.div>

      {/* Evolution */}
      <h2 className="text-2xl font-bold text-white mb-2">The Evolution of Text Analytics</h2>
      <p className="text-slate-400 mb-8">7 stages from basic file reading to full AI platform</p>

      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-brand-500 to-purple-500 opacity-30" />
        <div className="space-y-7">
          {EVOLUTION_STAGES.map((stage, i) => {
            const Icon = stage.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="relative flex gap-6"
              >
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${stage.color} flex items-center justify-center shrink-0 z-10 shadow-lg`}>
                  <Icon size={18} className="text-white" />
                </div>
                <div className="flex-1 glass-card p-5">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs text-slate-500 font-mono">Stage {stage.stage}</span>
                    <ArrowRight size={11} className="text-slate-600" />
                    <h3 className="font-bold text-white">{stage.title}</h3>
                  </div>
                  <p className="text-sm text-slate-400 mb-4">{stage.description}</p>
                  <pre className="bg-black/40 rounded-xl p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                    {stage.code}
                  </pre>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Tech stack */}
      <div className="mt-14 mb-10">
        <h2 className="text-2xl font-bold text-white mb-2">Technology Stack</h2>
        <p className="text-slate-400 mb-6">Every library and framework powering LexiMind AI</p>
        <div className="flex flex-wrap gap-3">
          {TECH_STACK.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              className="glass-card px-4 py-2.5 flex items-center gap-2"
            >
              <div className="w-2 h-2 rounded-full" style={{ background: t.color }} />
              <span className="font-medium text-white text-sm">{t.name}</span>
              <span className="text-xs text-slate-500">{t.category}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* 20 Modules */}
      <div className="mb-10">
        <h2 className="text-2xl font-bold text-white mb-2">20 Analytical Modules</h2>
        <p className="text-slate-400 mb-5">Every feature built into this platform</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {MODULES.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.025 }}
              className="glass-card p-3 flex items-center gap-2"
            >
              <span className="text-brand-400 text-xs font-bold shrink-0">M{i + 1}</span>
              <span className="text-xs text-slate-300 leading-snug">{m}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Real-world applications */}
      <div className="glass-card p-8 bg-gradient-to-br from-brand-500/10 to-purple-500/10 border border-brand-500/20">
        <h2 className="text-2xl font-bold text-white mb-5">Real-World Applications</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { icon: "🎓", title: "Academic Research",      desc: "Paper analysis, citation studies, literature review" },
            { icon: "📰", title: "Media & Journalism",     desc: "Bias detection, sentiment tracking, topic modeling"  },
            { icon: "💼", title: "Enterprise Intelligence",desc: "Contract analysis, document processing, reports"     },
            { icon: "⚖️", title: "Legal Tech",             desc: "Clause extraction, compliance, contract review"      },
            { icon: "🏥", title: "Healthcare",             desc: "Clinical note analysis, medical literature mining"   },
            { icon: "📚", title: "Education & Study",      desc: "Quiz generation, flashcards, reading comprehension"  },
          ].map(({ icon, title, desc }, i) => (
            <div key={i} className="p-4 rounded-xl bg-white/5">
              <div className="text-2xl mb-2">{icon}</div>
              <div className="font-semibold text-white text-sm">{title}</div>
              <div className="text-xs text-slate-400 mt-1">{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
