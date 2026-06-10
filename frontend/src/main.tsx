import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import { Layout }          from "./components/Layout";
import { Dashboard }       from "./pages/Dashboard";
import { Upload }          from "./pages/Upload";
import { AnalysisPage }    from "./pages/AnalysisPage";
import { TopicsPage }      from "./pages/TopicsPage";
import { DNAPage }         from "./pages/DNAPage";
import { SearchPage }      from "./pages/SearchPage";
import { QuizPage }        from "./pages/QuizPage";
import { ReportsPage }     from "./pages/ReportsPage";
import { CorePage }        from "./pages/CorePage";

import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1 },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index          element={<Dashboard />}    />
            <Route path="upload"  element={<Upload />}       />
            <Route path="analysis"element={<AnalysisPage />} />
            <Route path="topics"  element={<TopicsPage />}   />
            <Route path="dna"     element={<DNAPage />}      />
            <Route path="search"  element={<SearchPage />}   />
            <Route path="quiz"    element={<QuizPage />}     />
            <Route path="reports" element={<ReportsPage />}  />
            <Route path="core"    element={<CorePage />}     />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1a1a2e",
            color: "#fff",
            border: "1px solid rgba(255,255,255,0.1)",
          },
        }}
      />
    </QueryClientProvider>
  </React.StrictMode>
);
