
export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  metrics: SiteMetrics;
}

export interface SiteMetrics {
  relevanceScore: number; // 0-1
  precision: number;     // 0-1
  recall: number;        // 0-1
  tfidf: { term: string; score: number }[];
  domainAgeYears: number | string;
  authoritativeness: number; // 0-1
}

export interface AnalysisResponse {
  summary: string;
  results: SearchResult[];
}

export interface GroundingChunk {
  web?: {
    uri: string;
    title: string;
  };
}
