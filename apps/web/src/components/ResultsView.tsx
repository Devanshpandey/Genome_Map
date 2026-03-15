import { useState } from "react";
import { motion } from "framer-motion";
import MapVisualization from "./MapVisualization";
import StoryCarousel from "./StoryCarousel";
import { Download, RefreshCw, AlertTriangle } from "lucide-react";

export default function ResultsView({ data, onReset }: { data: any, onReset: () => void }) {
  const [exporting, setExporting] = useState(false);
  const { inference, story } = data;

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/story/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const exportData = await res.json();
      
      // Since it's local MVP, we'll just download the generated file path as text 
      // or open it if we serve the exports folder. For now, trigger download.
      alert(`Exported HTML saved to: ${exportData.path}`);
    } catch (err) {
      console.error(err);
      alert("Failed to export.");
    }
    setExporting(false);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-6"
    >
      {/* Header Bar */}
      <div className="col-span-1 lg:col-span-12 flex justify-between items-center bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
        <div className="flex items-center gap-4">
          <button onClick={onReset} className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors">
            <RefreshCw size={16} /> New Upload
          </button>
        </div>
        <button 
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          <Download size={16} /> {exporting ? "Exporting..." : "Export Story HTML"}
        </button>
      </div>

      {inference.warnings && inference.warnings.length > 0 && (
        <div className="col-span-1 lg:col-span-12 bg-amber-500/10 border border-amber-500/20 text-amber-300 p-4 rounded-xl flex items-start gap-3">
          <AlertTriangle className="shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold mb-1">Low Confidence Results</h4>
            <ul className="list-disc pl-5 opacity-80 text-sm">
              {inference.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* Main Map Area */}
      <div className="col-span-1 lg:col-span-7 h-[500px] glass-panel rounded-3xl overflow-hidden relative">
        <MapVisualization topRegions={inference.top_regions} />
      </div>

      {/* Story Area */}
      <div className="col-span-1 lg:col-span-5 flex flex-col gap-6">
        <div className="glass-panel p-6 rounded-3xl flex-1 flex flex-col">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-indigo-300">
            Analysis Narrative
          </h3>
          <StoryCarousel chapters={story.chapters} />
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="glass-panel p-5 rounded-3xl flex flex-col justify-center text-center">
            <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Top Similarity</span>
            <span className="text-2xl font-black text-cyan-400">
              {inference.top_populations?.[0] ? `${(inference.top_populations[0].score * 100).toFixed(1)}%` : "N/A"}
            </span>
            <span className="text-sm font-medium mt-1 leading-tight text-slate-300">
              {inference.top_populations?.[0] ? inference.top_populations[0].name : "Unknown"}
            </span>
          </div>

          <div className="glass-panel p-5 rounded-3xl flex flex-col justify-center text-center">
            <span className="text-xs uppercase tracking-wider text-slate-500 mb-1">Maternal / Paternal</span>
            <span className="text-2xl font-black text-purple-400">
              {inference.mtDNA} / {inference.yDNA}
            </span>
            <span className="text-sm font-medium mt-1 leading-tight text-slate-300">
              Haplogroups
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
