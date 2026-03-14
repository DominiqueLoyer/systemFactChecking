
import React, { useState, useEffect } from 'react';
import { GeminiService } from './services/geminiService';
import { AnalysisResponse, SearchResult } from './types';
import MetricCard from './components/MetricCard';
import TFIDFChart from './components/TFIDFChart';

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [gemini, setGemini] = useState<GeminiService | null>(null);

  useEffect(() => {
    setGemini(new GeminiService());
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !gemini) return;

    setLoading(true);
    setError(null);
    try {
      const result = await gemini.searchAndAnalyze(query);
      setAnalysis(result);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch search metrics. Please check your API configuration.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen pb-20">
      {/* Header */}
      <nav className="sticky top-0 z-50 glass border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <i className="fa-solid fa-microscope text-white"></i>
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
            SiteMetrics AI
          </h1>
        </div>
        <div className="hidden md:flex gap-4 text-sm text-slate-400 font-medium">
          <span className="hover:text-blue-400 cursor-pointer">Documentation</span>
          <span className="hover:text-blue-400 cursor-pointer">API Keys</span>
          <span className="hover:text-blue-400 cursor-pointer">Benchmarks</span>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="max-w-5xl mx-auto mt-16 px-6 text-center">
        <h2 className="text-4xl md:text-5xl font-extrabold mb-6">
          Analyze Google Results <span className="text-blue-500">at Scale</span>
        </h2>
        <p className="text-slate-400 text-lg mb-8 max-w-2xl mx-auto">
          Deep crawl into Google Search data. Get real-time metrics for Precision, Recall, Domain Age, and TF-IDF proxies using Gemini 3's advanced reasoning.
        </p>

        <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto group">
          <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-25 group-focus-within:opacity-50 transition duration-1000"></div>
          <div className="relative flex items-center">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for any topic or competitor..."
              className="w-full bg-slate-900 border border-slate-700 rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-100"
            />
            <i className="fa-solid fa-magnifying-glass absolute left-4 text-slate-500"></i>
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold rounded-lg transition-colors"
            >
              {loading ? <i className="fa-solid fa-circle-notch animate-spin"></i> : "Analyze"}
            </button>
          </div>
        </form>
      </header>

      {/* Error Message */}
      {error && (
        <div className="max-w-4xl mx-auto mt-8 px-6">
          <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl flex items-center gap-3">
            <i className="fa-solid fa-triangle-exclamation"></i>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <main className="max-w-7xl mx-auto mt-12 px-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Summary Section */}
          <section className="lg:col-span-12">
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <i className="fa-solid fa-chart-line text-blue-500"></i>
                Search Engine Performance Summary
              </h3>
              <p className="text-slate-300 leading-relaxed italic">
                "{analysis.summary}"
              </p>
            </div>
          </section>

          {/* Result Cards */}
          {analysis.results.map((result, idx) => (
            <section key={idx} className="lg:col-span-6 xl:col-span-4 h-full">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 h-full flex flex-col hover:border-blue-500/50 transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-bold text-lg text-slate-100 truncate group-hover:text-blue-400 transition-colors">
                      {result.title}
                    </h4>
                    <a 
                      href={result.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-xs text-blue-500 truncate block hover:underline"
                    >
                      {result.url}
                    </a>
                  </div>
                  <span className="bg-slate-800 text-slate-400 text-[10px] uppercase font-bold px-2 py-1 rounded">
                    Rank #{idx + 1}
                  </span>
                </div>

                <p className="text-slate-400 text-sm mb-6 line-clamp-3">
                  {result.snippet}
                </p>

                <div className="space-y-4 mb-6">
                  <MetricCard label="Relevance Score" value={result.metrics.relevanceScore} color="bg-blue-500" />
                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard label="Precision @k" value={result.metrics.precision} color="bg-purple-500" />
                    <MetricCard label="Recall Est." value={result.metrics.recall} color="bg-pink-500" />
                  </div>
                </div>

                <div className="mt-auto pt-6 border-t border-slate-800">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">TF-IDF Importance</span>
                    <span className="text-xs text-slate-400">
                      Domain Age: <span className="text-white font-medium">{result.metrics.domainAgeYears} years</span>
                    </span>
                  </div>
                  <TFIDFChart data={result.metrics.tfidf} />
                </div>
              </div>
            </section>
          ))}
        </main>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="max-w-7xl mx-auto mt-12 px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse">
              <div className="h-4 w-3/4 bg-slate-800 rounded mb-4"></div>
              <div className="h-3 w-1/2 bg-slate-800 rounded mb-6"></div>
              <div className="h-20 bg-slate-800 rounded mb-6"></div>
              <div className="space-y-4">
                <div className="h-2 bg-slate-800 rounded"></div>
                <div className="h-2 bg-slate-800 rounded w-5/6"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!analysis && !loading && !error && (
        <div className="max-w-4xl mx-auto mt-24 text-center px-6">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-slate-900 border border-slate-800 rounded-3xl mb-6">
            <i className="fa-solid fa-magnifying-glass-chart text-3xl text-slate-600"></i>
          </div>
          <h3 className="text-xl font-bold mb-2">Ready for analysis</h3>
          <p className="text-slate-500">
            Enter a keyword to see detailed search engine metrics and content importance scores.
          </p>
        </div>
      )}
      
      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 glass border-t border-slate-800 p-4 text-center text-xs text-slate-500">
        Powered by Gemini 3 Flash & Google Search Grounding. No manual scrapers required.
      </footer>
    </div>
  );
};

export default App;
