import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

// ── Public pages ──────────────────────────────────────────────────────────────
import { LandingPage }      from "./pages/landing/LandingPage";
import { LoginPage }        from "./pages/auth/LoginPage";
import { RegisterPage }     from "./pages/auth/RegisterPage";
import { OnboardingPage }   from "./pages/onboarding/OnboardingPage";

// ── App shell ─────────────────────────────────────────────────────────────────
import { AppLayout }        from "./components/AppLayout";

// ── App pages ─────────────────────────────────────────────────────────────────
import { AppDashboard }     from "./pages/app/AppDashboard";
import { LearnPage }        from "./pages/app/LearnPage";
import { SubjectsPage }     from "./pages/app/SubjectsPage";
import { SubjectDetailPage }from "./pages/app/SubjectDetailPage";
import { ChapterPage }      from "./pages/app/ChapterPage";
import { ConceptPage }      from "./pages/app/ConceptPage";
import { LearningPathPage } from "./pages/app/LearningPathPage";
import { QuizzesPage }      from "./pages/app/QuizzesPage";
import { PYQsPage }         from "./pages/app/PYQsPage";
import { NotesPage, NoteDetailPage } from "./pages/app/NotesPage";
import { LibraryPage }      from "./pages/app/LibraryPage";
import { DocumentDetailPage } from "./pages/app/DocumentDetailPage";
import { TutorPage }        from "./pages/app/TutorPage";
import { ProgressPage }     from "./pages/app/ProgressPage";
import { ProfilePage }      from "./pages/app/ProfilePage";

import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/"            element={<LandingPage />} />
          <Route path="/login"       element={<LoginPage />} />
          <Route path="/register"    element={<RegisterPage />} />
          <Route path="/onboarding"  element={<OnboardingPage />} />

          {/* App — protected shell */}
          <Route path="/app" element={<AppLayout />}>
            <Route index                          element={<AppDashboard />} />
            <Route path="learn"                   element={<LearnPage />} />
            <Route path="subjects"                element={<SubjectsPage />} />
            <Route path="subjects/:subjectId"     element={<SubjectDetailPage />} />
            <Route path="chapters/:chapterId"     element={<ChapterPage />} />
            <Route path="concepts/:conceptId"     element={<ConceptPage />} />
            <Route path="learning-path"           element={<LearningPathPage />} />
            <Route path="quizzes"                 element={<QuizzesPage />} />
            <Route path="pyqs"                    element={<PYQsPage />} />
            <Route path="notes"                   element={<NotesPage />} />
            <Route path="notes/:noteId"           element={<NoteDetailPage />} />
            <Route path="library"                 element={<LibraryPage />} />
            <Route path="library/:docId"          element={<DocumentDetailPage />} />
            <Route path="tutor"                   element={<TutorPage />} />
            <Route path="progress"                element={<ProgressPage />} />
            <Route path="profile"                 element={<ProfilePage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>

      <Toaster position="top-right" toastOptions={{
        style: { background: "#0d0d1a", color: "#fff", border: "1px solid rgba(255,255,255,0.08)" },
      }} />
    </QueryClientProvider>
  </React.StrictMode>
);
