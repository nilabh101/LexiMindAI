import axios from "axios";

const BASE_URL =
  (import.meta as any).env?.VITE_API_URL ||
  "http://localhost:8000/api";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

/** Identity for every request: the backend scopes user data by this header. */
function storedUserId(): string | null {
  try {
    const raw = localStorage.getItem("leximind_user");
    return raw ? (JSON.parse(raw)?.id ?? null) : null;
  } catch {
    return null;
  }
}

api.interceptors.request.use((config) => {
  const id = storedUserId();
  if (id) config.headers.set?.("X-User-Id", id);
  return config;
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
  const uid = storedUserId();
  if (uid) fd.append("user_id", uid);

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

// =====================
// PHASE 2 ACADEMIC
// =====================

export function mapDocStatus(status?: string): "uploaded" | "processing" | "ready" | "failed" | "needs_review" {
  const s = (status || "").toUpperCase();
  if (s === "UPLOADED") return "uploaded";
  if (s === "PROCESSING") return "processing";
  if (s === "READY") return "ready";
  if (s === "FAILED") return "failed";
  if (s === "NEEDS_REVIEW") return "needs_review";
  return (status as any) || "uploaded";
}

export const uploadLibraryDocument = (file: File, meta: Record<string, string>) => {
  const fd = new FormData();
  fd.append("file", file);
  Object.entries(meta).forEach(([k, v]) => {
    if (v) fd.append(k, v);
  });
  fd.append("process", "true");
  const uid = storedUserId();
  if (uid && !meta.user_id) fd.append("user_id", uid);
  return api.post("/documents/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const retryDocument = (id: number) => api.post(`/documents/${id}/retry`);

export const getDocumentDetail = (id: number) => api.get(`/documents/${id}/detail`);

export const searchAcademic = (q: string) => api.get("/search", { params: { q } });

export const listAcademicNotes = (params?: { subject_id?: string; concept_id?: string }) =>
  api.get("/notes", { params });

export const getAcademicNote = (id: number) => api.get(`/notes/${id}`);

export const listQuestions = (params?: { subject_id?: string; concept_id?: string; pyq_only?: boolean; source?: string }) =>
  api.get("/questions", { params });

export const generateQuiz = (body: {
  subject_id?: string;
  chapter_id?: string;
  concept_id?: string;
  difficulty?: string;
  question_count?: number;
  question_type?: string;
}) => api.post("/quizzes/generate", body);

export const completeQuiz = (body: {
  user_id: string;
  quiz_id: string;
  subject_id?: string;
  answers: Array<{
    question_id: number | string;
    selected_answer?: string;
    correct?: boolean;
    time_taken?: number;
    concept_id?: string;
  }>;
}) => api.post("/quizzes/complete", body);

export const getLearningPathApi = (userId: string, subjectId: string) =>
  api.get(`/learning/learning-path/${userId}/${subjectId}`);

export const getProgressApi = (userId: string) => api.get(`/learning/progress/${userId}`);

export const getMasteryApi = (userId: string) => api.get(`/learning/mastery/${userId}`);

export const getAiStatus = () => api.get("/ai/status");

export const sendTutorMessage = (
  message: string,
  extra: {
    docId?: number | null;
    history?: ChatMessage[];
    userId?: string;
    subjectId?: string;
    chapterId?: string;
    conceptId?: string;
    educationLevel?: string;
    course?: string;
    action?: string;
  } = {}
) =>
  api.post("/ai/tutor", {
    message,
    doc_id: extra.docId ?? null,
    history: extra.history ?? [],
    user_id: extra.userId,
    subject_id: extra.subjectId,
    chapter_id: extra.chapterId,
    concept_id: extra.conceptId,
    education_level: extra.educationLevel,
    course: extra.course,
    action: extra.action,
  });

// =====================
// PHASE 3 ADAPTIVE LEARNING
// =====================

export const getWeakConceptsApi = (userId: string, subjectId?: string) =>
  api.get(`/learning/weak-concepts/${userId}`, { params: { subject_id: subjectId } });

export const getRecommendationsApi = (userId: string, subjectId?: string, limit = 5) =>
  api.get(`/learning/recommendations/${userId}`, { params: { subject_id: subjectId, limit } });

export const getNextRecommendationApi = (userId: string, subjectId?: string) =>
  api.get(`/learning/recommendations/${userId}/next`, { params: { subject_id: subjectId } });

export const getDailyPlanApi = (userId: string, subjectId?: string, studyMinutes?: number) =>
  api.get(`/learning/daily-plan/${userId}`, {
    params: { subject_id: subjectId, study_minutes: studyMinutes },
  });

export const getReviewScheduleApi = (userId: string) =>
  api.get(`/learning/review-schedule/${userId}`);

export const getQuizHistoryApi = (userId: string, limit = 50) =>
  api.get(`/learning/history/${userId}`, { params: { limit } });

export const getMistakesApi = (userId: string, conceptId?: string) =>
  api.get(`/learning/mistakes/${userId}`, { params: { concept_id: conceptId } });

export const getPrerequisitesApi = (conceptId: string, userId?: string) =>
  api.get(`/learning/prerequisites/${conceptId}`, { params: { user_id: userId } });

export const getAdaptiveConfigApi = () => api.get("/learning/config");

export const generateAdaptiveQuiz = (body: {
  user_id: string;
  subject_id?: string;
  chapter_id?: string;
  concept_id?: string;
  question_count?: number;
  include_recent?: boolean;
}) => api.post("/quizzes/adaptive", body);
