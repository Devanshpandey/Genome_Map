import { useState } from "react";
import { UploadCloud, FileText, Database } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function UploadCard({ onSubmit, disabled }: { onSubmit: (data: FormData, mode: "structured" | "genotype") => void, disabled: boolean }) {
  const [mode, setMode] = useState<"genotype" | "structured">("genotype");
  const [file, setFile] = useState<File | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || disabled) return;
    const formData = new FormData();
    formData.append("file", file);
    onSubmit(formData, mode);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-8 rounded-3xl w-full max-w-xl relative overflow-hidden"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500" />
      
      <div className="flex space-x-2 bg-black/20 p-1 rounded-xl mb-8">
        <button
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${mode === "genotype" ? "bg-indigo-500/20 text-indigo-300 shadow-lg shadow-indigo-500/10" : "text-slate-400 hover:text-white"}`}
          onClick={() => setMode("genotype")}
        >
          <Database size={16} /> Raw Genotype
        </button>
        <button
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${mode === "structured" ? "bg-cyan-500/20 text-cyan-300 shadow-lg shadow-cyan-500/10" : "text-slate-400 hover:text-white"}`}
          onClick={() => setMode("structured")}
        >
          <FileText size={16} /> Structured JSON
        </button>
      </div>

      <AnimatePresence mode="wait">
        <motion.form
          key={mode}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 10 }}
          onSubmit={handleSubmit}
          className="flex flex-col gap-6"
        >
          <div className="border-2 border-dashed border-slate-700/50 rounded-2xl p-8 hover:bg-slate-800/30 hover:border-indigo-500/50 transition-all group relative">
            <input 
              type="file" 
              accept={mode === "genotype" ? ".txt,.csv,.tsv,.vcf,.gz" : ".json"}
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
            />
            <div className="flex flex-col justify-center items-center text-center pointer-events-none">
              <UploadCloud className="w-12 h-12 text-slate-500 mb-4 group-hover:text-indigo-400 transition-colors" />
              <p className="font-medium text-slate-200 mb-1">
                {file ? file.name : `Select ${mode === "genotype" ? "23andMe or VCF" : "Dataset JSON"} File`}
              </p>
              <p className="text-xs text-slate-500">
                {mode === "genotype" ? "Only Chromosome 22 variants will be utilized." : "Requires valid probabilities summing to 1.0."}
              </p>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={!file || disabled}
            className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 font-bold text-white shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {disabled ? "Backend Not Ready" : "Uncover Origins"}
          </button>
        </motion.form>
      </AnimatePresence>
    </motion.div>
  );
}
