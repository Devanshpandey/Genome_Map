"use client";

import { useState, useEffect } from "react";
import UploadCard from "@/components/UploadCard";
import ResultsView from "@/components/ResultsView";
import { Loader2 } from "lucide-react";

export default function Home() {
  const [status, setStatus] = useState<"idle" | "loading" | "results" | "error">("idle");
  const [backendReady, setBackendReady] = useState(false);
  const [resultsData, setResultsData] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/reference/status`)
      .then((res) => res.json())
      .then((data) => setBackendReady(data.ready))
      .catch((err) => console.error("Could not reach backend API", err));
  }, []);

  const handleUploadSubmit = async (formData: FormData, mode: "structured" | "genotype") => {
    setStatus("loading");
    try {
      let res;
      if (mode === "structured") {
        // Parse the JSON file
        const file = formData.get("file") as File;
        const text = await file.text();
        const payload = JSON.parse(text);
        
        res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/upload/structured`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/upload/genotype`, {
          method: "POST",
          body: formData,
        });
      }

      if (!res.ok) {
        throw new Error(await res.text());
      }
      
      const data = await res.json();
      setResultsData(data);
      setStatus("results");
    } catch (err: any) {
      setErrorMessage(err.message || "An error occurred during processing.");
      setStatus("error");
    }
  };

  const reset = () => {
    setStatus("idle");
    setResultsData(null);
  };

  return (
    <main className="min-h-screen p-8 flex flex-col items-center">
      <header className="mb-12 text-center mt-10">
        <h1 className="text-5xl font-extrabold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
          Genome Time Machine
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Explore your genetic similarity against the 1000 Genomes reference panel. 
          Discover probabilistic regional affinities and deep lineage patterns.
        </p>
      </header>

      {!backendReady && status === "idle" && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-200 p-4 rounded-lg mb-8 max-w-xl text-center">
          Warning: The backend does not have reference data loaded. Please run `make prepare-ref`.
        </div>
      )}

      {status === "idle" && <UploadCard onSubmit={handleUploadSubmit} disabled={!backendReady} />}
      
      {status === "loading" && (
        <div className="flex flex-col items-center justify-center space-y-4 py-20">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-500" />
          <p className="text-xl font-medium animate-pulse text-indigo-200">
            Projecting genome into reference PCA space...
          </p>
          <p className="text-sm text-slate-500">This may take 10-30 seconds.</p>
        </div>
      )}

      {status === "error" && (
        <div className="glass-panel p-8 rounded-2xl max-w-lg text-center">
          <div className="text-red-400 mb-4 text-xl font-bold">Processing Error</div>
          <p className="mb-6">{errorMessage}</p>
          <button 
            onClick={reset}
            className="px-6 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {status === "results" && resultsData && (
        <ResultsView data={resultsData} onReset={reset} />
      )}
      
      <footer className="mt-auto pt-24 pb-8 text-center text-slate-600 text-sm max-w-3xl">
        <p className="mb-2 uppercase tracking-wide text-xs">Scientific & Legal Disclaimer</p>
        <p>This experience is a visualization based on reference populations and probabilistic genetic similarity. It uses K-Nearest Neighbors in PCA space. It is for educational purposes only and is <strong>not medical advice</strong>.</p>
      </footer>
    </main>
  );
}
