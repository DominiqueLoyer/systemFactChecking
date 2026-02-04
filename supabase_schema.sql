-- SysCRED Supabase Schema v2.0
-- Copiez et exécutez ce SQL dans l'éditeur SQL de votre dashboard Supabase
-- https://supabase.com/dashboard/project/zmluirvqfkmfazqitqgi/sql

-- =====================================================
-- 1. TABLE: Résultats d'analyse (existante)
-- =====================================================
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    credibility_score FLOAT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    source_reputation VARCHAR(50),
    fact_check_count INTEGER DEFAULT 0,
    -- NEW: Détails complets du scoring
    score_details JSONB,
    domain VARCHAR(255),
    analysis_version VARCHAR(20) DEFAULT 'v2.1'
);

CREATE INDEX IF NOT EXISTS idx_analysis_url ON analysis_results(url);
CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_results(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_domain ON analysis_results(domain);

-- =====================================================
-- 2. TABLE: Triplets RDF (Ontologie)
-- =====================================================
-- Stocke les triplets RDF de l'ontologie SysCRED
CREATE TABLE IF NOT EXISTS rdf_triples (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(500) NOT NULL,       -- URI du sujet (ex: syscred:Evaluation_123)
    predicate VARCHAR(500) NOT NULL,     -- URI du prédicat (ex: syscred:hasScore)
    object TEXT NOT NULL,                -- Valeur ou URI de l'objet
    object_type VARCHAR(20) DEFAULT 'uri', -- 'uri', 'literal', 'typed_literal'
    object_datatype VARCHAR(100),        -- ex: xsd:float, xsd:dateTime
    object_lang VARCHAR(10),             -- ex: 'en', 'fr' pour littéraux
    graph_name VARCHAR(100) DEFAULT 'data', -- 'base' pour ontologie, 'data' pour instances
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(subject, predicate, object, graph_name) -- Évite les doublons
);

-- Index pour requêtes SPARQL-like
CREATE INDEX IF NOT EXISTS idx_triple_subject ON rdf_triples(subject);
CREATE INDEX IF NOT EXISTS idx_triple_predicate ON rdf_triples(predicate);
CREATE INDEX IF NOT EXISTS idx_triple_object ON rdf_triples(object) WHERE object_type = 'uri';
CREATE INDEX IF NOT EXISTS idx_triple_graph ON rdf_triples(graph_name);

-- =====================================================
-- 3. TABLE: Sources (Domaines analysés)
-- =====================================================
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    reputation_score FLOAT,
    domain_age_years FLOAT,
    is_fact_checker BOOLEAN DEFAULT FALSE,
    analysis_count INTEGER DEFAULT 0,
    last_analyzed TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_reputation ON sources(reputation_score);

-- =====================================================
-- 4. TABLE: Claims (Affirmations extraites)
-- =====================================================
CREATE TABLE IF NOT EXISTS claims (
    id SERIAL PRIMARY KEY,
    claim_text TEXT NOT NULL,
    claim_hash VARCHAR(64) UNIQUE,  -- SHA256 du texte pour déduplication
    source_url VARCHAR(500),
    extracted_entities JSONB,        -- Entités NER
    credibility_score FLOAT,
    verification_status VARCHAR(50), -- 'unverified', 'verified_true', 'verified_false', 'disputed'
    evidence_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claims_hash ON claims(claim_hash);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(verification_status);

-- =====================================================
-- 5. TABLE: Evidence (Preuves TREC)
-- =====================================================
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER REFERENCES claims(id) ON DELETE CASCADE,
    doc_id VARCHAR(100),          -- ID document TREC (ex: AP880101-0001)
    doc_text TEXT,
    relevance_score FLOAT,
    retrieval_method VARCHAR(50), -- 'bm25', 'bm25_prf', 'neural'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_doc ON evidence(doc_id);

-- =====================================================
-- 6. VUE: Statistiques globales
-- =====================================================
CREATE OR REPLACE VIEW syscred_stats AS
SELECT 
    (SELECT COUNT(*) FROM analysis_results) as total_analyses,
    (SELECT COUNT(*) FROM sources) as unique_domains,
    (SELECT COUNT(*) FROM rdf_triples WHERE graph_name = 'base') as base_triples,
    (SELECT COUNT(*) FROM rdf_triples WHERE graph_name = 'data') as data_triples,
    (SELECT COUNT(*) FROM claims) as total_claims,
    (SELECT AVG(credibility_score) FROM analysis_results) as avg_credibility;

-- =====================================================
-- 7. FONCTION: Importer triplets depuis TTL
-- =====================================================
-- Utilisée par le backend Python pour sync bidirectionnelle
CREATE OR REPLACE FUNCTION upsert_triple(
    p_subject VARCHAR,
    p_predicate VARCHAR,
    p_object TEXT,
    p_object_type VARCHAR DEFAULT 'uri',
    p_graph_name VARCHAR DEFAULT 'data'
) RETURNS void AS $$
BEGIN
    INSERT INTO rdf_triples (subject, predicate, object, object_type, graph_name)
    VALUES (p_subject, p_predicate, p_object, p_object_type, p_graph_name)
    ON CONFLICT (subject, predicate, object, graph_name) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. RLS (Row Level Security) - Optionnel
-- =====================================================
-- Activer si vous utilisez l'authentification Supabase
-- ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE rdf_triples ENABLE ROW LEVEL SECURITY;

-- Note: La connexion se fait via DATABASE_URL dans les variables d'environnement
-- DATABASE_URL=postgresql://postgres:FactCheckingSystem2026_test@db.zmluirvqfkmfazqitqgi.supabase.co:5432/postgres
