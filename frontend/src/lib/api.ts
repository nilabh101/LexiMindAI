import axios from "axios";

const BASE_URL =
  (import.meta as any).env?.VITE_API_URL ||
  "http://localhost:8000/api";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail ||
      err.message ||
      "Request failed";

    return Promise.reject(new Error(msg));
  }
);

// =====================
// DOCUMENTS
// =====================

export const uploadDocument = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);

  return api.post("/documents/upload", fd, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const listDocuments = () =>
  api.get("/documents/");

export const getDocument = (id: number) =>
  api.get(`/documents/${id}`);

export const deleteDocument = (id: number) =>
  api.delete(`/documents/${id}`);

// =====================
// ANALYSIS
// =====================

export const getWordAnalysis = (
  id: number,
  topN = 50,
  useStemming = false
) => {
  const useLemmatization = !useStemming;

  return api
    .get(
      `/analysis/${id}/words?top_n=${topN}&use_stemming=${useStemming}&use_lemmatization=${useLemmatization}`
    )
    .then((r) => r.data);
};

export const getWordCloud = (id: number) =>
  api.get(`/analysis/${id}/wordcloud`);

export const getDocumentStats = (id: number) =>
  api.get(`/analysis/${id}/stats`);

export const getFlashcards = (id: number, numCards = 15) =>
  api.get(`/analysis/${id}/flashcards`, { params: { num_cards: numCards } });

export const searchInDocument = (id: number, query: string, caseSensitive = false) =>
  api.get(`/documents/${id}/search`, { params: { query, case_sensitive: caseSensitive } });

export const getSentiment = (id: number) =>
  api.get(`/analysis/${id}/sentiment`);

// ⭐ THIS WAS MISSING
export const getEmotions = (id: number) =>
  api.get(`/analysis/${id}/emotions`);

export const getLexicalDiversity = (id: number) =>
  api.get(`/analysis/${id}/lexical_diversity`).then(
    (r) => r.data
  );

export const getUniqueWords = (id: number) =>
  api.get(`/analysis/${id}/unique_words`).then(
    (r) => r.data
  );

export const getTopics = (id: number) =>
  api.get(`/analysis/${id}/topics`).then(
    (r) => r.data
  );

export const getEntities = (id: number) =>
  api.get(`/analysis/${id}/entities`).then(
    (r) => r.data
  );

export const getStyle = (id: number) =>
  api.get(`/analysis/${id}/style`);

export const getDNA = (id: number) =>
  api.get(`/analysis/${id}/dna`);

export const getSummary = (id: number) =>
  api.get(`/analysis/${id}/summary`);

export const getQuestions = (id: number) =>
  api.get(`/analysis/${id}/questions`);

export const getQuiz = (id: number, numQuestions = 10) =>
  api.get(`/analysis/${id}/quiz`, { params: { num_questions: numQuestions } });

export const multiDocumentQuiz = (docIds: number[], numQuestions = 20) =>
  api.post(`/analysis/multi-quiz`, docIds, { params: { num_questions: numQuestions } });

// (getFlashcards already declared above)

// =====================
// CHAT
// =====================

export interface ChatMessage { role: "user" | "assistant"; content: string; }

export const sendChatMessage = (
  message: string,
  docId?: number | null,
  history: ChatMessage[] = []
) =>
  api.post("/chat", { message, doc_id: docId ?? null, history });

export const getInsights = (id: number) =>
  api.get(`/analysis/${id}/insights`);

export const getBias = (id: number) =>
  api.get(`/analysis/${id}/bias`);

export const getFullAnalysis = (id: number) =>
  api.get(`/analysis/${id}/full`);

export const compareDocuments = (
  ids: number[]
) => api.post("/analysis/compare", ids);

// =====================
// TRENDS
// =====================

export const getTrends = (
  ids: number[]
) => api.post("/trends/analyze", ids);

// =====================
// REPORTS
// =====================

export const downloadReport = (id: number) =>
  api.get(`/reports/${id}/pdf`, {
    responseType: "blob",
  });