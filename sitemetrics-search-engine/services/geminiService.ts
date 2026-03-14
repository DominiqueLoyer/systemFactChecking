
import { GoogleGenAI, Type } from "@google/genai";
import { AnalysisResponse } from "../types";

export class GeminiService {
  private ai: GoogleGenAI;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
  }

  async searchAndAnalyze(query: string): Promise<AnalysisResponse> {
    const prompt = `
      Perform a deep search analysis for the query: "${query}".
      
      Tasks:
      1. Use the Google Search tool to find relevant web results.
      2. For each major website found, calculate or estimate the following metrics:
         - Relevance Score (0 to 1 based on query alignment).
         - Precision at its rank (simulated as the proportion of relevant results up to this point).
         - Recall estimate (simulated as the proportion of total relevant information covered).
         - A simplified TF-IDF proxy: Extract 3 key terms and give them relative weight scores.
         - Domain Age: Estimate based on known site history or common knowledge.
         - Authoritativeness: A score from 0 to 1 based on domain reputation.
      3. Return the response as a valid JSON object matching this schema:
         {
           "summary": "Short overview of findings",
           "results": [
             {
               "title": "Page Title",
               "url": "https://example.com",
               "snippet": "Brief summary",
               "metrics": {
                 "relevanceScore": 0.95,
                 "precision": 0.9,
                 "recall": 0.4,
                 "tfidf": [{"term": "keyword", "score": 0.8}],
                 "domainAgeYears": 15,
                 "authoritativeness": 0.9
               }
             }
           ]
         }
    `;

    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
        config: {
          tools: [{ googleSearch: {} }],
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              summary: { type: Type.STRING },
              results: {
                type: Type.ARRAY,
                items: {
                  type: Type.OBJECT,
                  properties: {
                    title: { type: Type.STRING },
                    url: { type: Type.STRING },
                    snippet: { type: Type.STRING },
                    metrics: {
                      type: Type.OBJECT,
                      properties: {
                        relevanceScore: { type: Type.NUMBER },
                        precision: { type: Type.NUMBER },
                        recall: { type: Type.NUMBER },
                        tfidf: {
                          type: Type.ARRAY,
                          items: {
                            type: Type.OBJECT,
                            properties: {
                              term: { type: Type.STRING },
                              score: { type: Type.NUMBER }
                            }
                          }
                        },
                        domainAgeYears: { type: Type.STRING },
                        authoritativeness: { type: Type.NUMBER }
                      },
                      required: ["relevanceScore", "precision", "recall", "tfidf", "domainAgeYears", "authoritativeness"]
                    }
                  },
                  required: ["title", "url", "snippet", "metrics"]
                }
              }
            },
            required: ["summary", "results"]
          }
        }
      });

      const text = response.text || '{}';
      const parsed: AnalysisResponse = JSON.parse(text);
      
      // Optionally extract actual URLs from grounding chunks to verify
      const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks || [];
      console.log("Grounding Chunks:", chunks);

      return parsed;
    } catch (error) {
      console.error("Gemini Search Error:", error);
      throw error;
    }
  }
}
