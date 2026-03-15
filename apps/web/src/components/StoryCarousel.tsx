import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function StoryCarousel({ chapters }: { chapters: Array<{id: string, title: string, text: string}> }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const next = () => setCurrentIndex((prev) => (prev + 1) % chapters.length);
  const prev = () => setCurrentIndex((prev) => (prev - 1 + chapters.length) % chapters.length);

  if (!chapters || chapters.length === 0) return <div>No story data available.</div>;

  return (
    <div className="flex-1 flex flex-col relative">
      <div className="flex-1 relative overflow-hidden flex items-center px-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="absolute inset-x-0 mx-4"
          >
            <h4 className="text-lg font-bold text-white mb-2">{chapters[currentIndex].title}</h4>
            <p className="text-slate-300 leading-relaxed min-h-[140px]">
              {chapters[currentIndex].text}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
      
      <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-700/50">
        <button 
          onClick={prev}
          className="p-2 rounded-full hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
        >
          <ChevronLeft size={20} />
        </button>
        <div className="flex gap-2">
          {chapters.map((_, i) => (
            <div 
              key={i} 
              className={`w-2 h-2 rounded-full transition-all ${i === currentIndex ? "bg-indigo-400 w-6" : "bg-slate-700"}`}
            />
          ))}
        </div>
        <button 
          onClick={next}
          className="p-2 rounded-full hover:bg-slate-800 transition-colors text-slate-400 hover:text-white"
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}
