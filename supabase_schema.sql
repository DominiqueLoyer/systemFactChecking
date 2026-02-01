-- SysCRED Supabase Schema
-- Copiez et exécutez ce SQL dans l'éditeur SQL de votre dashboard Supabase

-- 1. Table pour stocker les résultats d'analyse
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    credibility_score FLOAT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    source_reputation VARCHAR(50),
    fact_check_count INTEGER DEFAULT 0
);

-- 2. Index pour accélérer les recherches par URL
CREATE INDEX IF NOT EXISTS idx_analysis_url ON analysis_results(url);

-- 3. Index pour les tris par date
CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_results(created_at);

-- Note: La connexion se fait via DATABASE_URL dans les variables d'environnement Render
