import axios from "axios";

const BASE_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Request failed";
    return Promise.reject(new Error(msg));
  }
);

// Documents
export const uploadDocument = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/documents/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const listDocuments = () => api.get("/documents/");
export const getDocument = (id: number) => api.get(`/documents/${id}`);
export const deleteDocument = (id: number) => api.delete(`/documents/${id}`);

// Analysis
export const getWordAnalysis = (id: number, topN = 50, useStemming = false) => {
  const useLemmatization = !useStemming;
  return api.get(`/analysis/${id}/words?top_n=${topN}&use_stemming=${useStemming}&use_lemmatization=${useLemmatization}`).then(r => r.data);
};
export const getWordCloud = (id: number) => api.get(`/analysis/${id}/wordcloud`);
export const getSentiment = (id: number) => api.get(`/analysis/${id}/sentiment`);
export const getLexicalDiversity = (id: number) =>
  api.get(`/analysis/${id}/lexical_diversity`).then(r => r.data);
export const getUniqueWords = (id: number) =>
  api.get(`/analysis/${id}/unique_words`).then(r => r.data);
export const getTopics = (id: number) =>
  api.get(`/analysis/${id}/topics`).then(r => r.data);
export const getEntities = (id: number) =>
  api.get(`/analysis/${id}/entities`).then(r => r.data);
// Duplicate export removed
// export const getTopics = (id: number) => api.get(`/analysis/${id}/topics`);
// export const getEntities = (id: number) => api.get(`/analysis/${id}/entities`);
export const getStyle = (id: number) => api.get(`/analysis/${id}/style`);
export const getDNA = (id: number) => api.get(`/analysis/${id}/dna`);
export const getSummary = (id: number) => api.get(`/analysis/${id}/summary`);
export const getQuestions = (id: number) => api.get(`/analysis/${id}/questions`);
export const getQuiz = (id: number) => api.get(`/analysis/${id}/quiz`);
export const getInsights = (id: number) => api.get(`/analysis/${id}/insights`);
export const getBias = (id: number) => api.get(`/analysis/${id}/bias`);
export const getFullAnalysis = (id: number) => api.get(`/analysis/${id}/full`);
export const compareDocuments = (ids: number[]) =>
  api.post("/analysis/compare", ids);

// Trends
export const getTrends = (ids: number[]) =>
  api.post("/trends/analyze", ids);

// Reports
export const downloadReport = (id: number) =>
  api.get(`/reports/${id}/pdf`, { responseType: "blob" });
