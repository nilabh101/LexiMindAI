import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Upload } from "./pages/Upload";
import { WordAnalysis } from "./pages/WordAnalysis";
import { SentimentPage } from "./pages/SentimentPage";
import { TopicsPage } from "./pages/TopicsPage";
import { DNAPage } from "./pages/DNAPage";
import { SummaryPage } from "./pages/SummaryPage";
import { QuizPage } from "./pages/QuizPage";
import { ComparePage } from "./pages/ComparePage";
import { TrendsPage } from "./pages/TrendsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { PresentationPage } from "./pages/PresentationPage";

import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById("app")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="upload" element={<Upload />} />
            <Route path="words" element={<WordAnalysis />} />
            <Route path="sentiment" element={<SentimentPage />} />
            <Route path="topics" element={<TopicsPage />} />
            <Route path="dna" element={<DNAPage />} />
            <Route path="summary" element={<SummaryPage />} />
            <Route path="quiz" element={<QuizPage />} />
            <Route path="compare" element={<ComparePage />} />
            <Route path="trends" element={<TrendsPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="presentation" element={<PresentationPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: "#1a1a2e",
          color: "#fff",
          border: "1px solid rgba(255,255,255,0.1)",
        }
      }} />
    </QueryClientProvider>
  </React.StrictMode>
);
