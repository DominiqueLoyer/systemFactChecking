"""
SysCRED Storage Module - SQLite + Supabase
==========================================
Stocke les triplets RDF et résultats d'analyse.
Utilise SQLite localement, avec option de sync vers Supabase.
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
from pathlib import Path

# Chemins
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "syscred_local.db"

class SysCREDStore:
    """
    Gestionnaire de stockage pour SysCRED.
    SQLite local avec option Supabase.
    """
    
    def __init__(self, db_path: str = None, supabase_url: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.supabase_url = supabase_url or os.getenv("DATABASE_URL")
        self.conn = None
        self._init_local_db()
        
    def _init_local_db(self):
        """Initialise la base SQLite locale."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Créer les tables
        self.conn.executescript("""
            -- Résultats d'analyse
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                credibility_score REAL NOT NULL,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_reputation TEXT,
                fact_check_count INTEGER DEFAULT 0,
                score_details TEXT,
                domain TEXT
            );
            
            -- Triplets RDF
            CREATE TABLE IF NOT EXISTS rdf_triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                object_type TEXT DEFAULT 'uri',
                graph_name TEXT DEFAULT 'data',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(subject, predicate, object, graph_name)
            );
            
            -- Sources
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                reputation_score REAL,
                domain_age_years REAL,
                is_fact_checker INTEGER DEFAULT 0,
                analysis_count INTEGER DEFAULT 0,
                last_analyzed TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Claims
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_text TEXT NOT NULL,
                claim_hash TEXT UNIQUE,
                source_url TEXT,
                extracted_entities TEXT,
                credibility_score REAL,
                verification_status TEXT DEFAULT 'unverified',
                evidence_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Evidence
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id INTEGER,
                doc_id TEXT,
                doc_text TEXT,
                relevance_score REAL,
                retrieval_method TEXT DEFAULT 'bm25',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (claim_id) REFERENCES claims(id)
            );
            
            -- Index
            CREATE INDEX IF NOT EXISTS idx_analysis_url ON analysis_results(url);
            CREATE INDEX IF NOT EXISTS idx_triple_subject ON rdf_triples(subject);
            CREATE INDEX IF NOT EXISTS idx_triple_graph ON rdf_triples(graph_name);
            CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
        """)
        self.conn.commit()
        print(f"[SysCREDStore] SQLite initialisé: {self.db_path}")
    
    # =========================================================================
    # ONTOLOGY / RDF TRIPLES
    # =========================================================================
    
    def sync_ontology(self, ontology_manager) -> Dict[str, int]:
        """
        Synchronise les graphes RDFLib vers SQLite.
        
        Args:
            ontology_manager: Instance avec base_graph et data_graph
        """
        result = {'base_synced': 0, 'data_synced': 0}
        
        try:
            # Sync base ontology
            if hasattr(ontology_manager, 'base_graph') and ontology_manager.base_graph:
                result['base_synced'] = self._sync_graph(
                    ontology_manager.base_graph, 
                    graph_name='base'
                )
            
            # Sync data graph
            if hasattr(ontology_manager, 'data_graph') and ontology_manager.data_graph:
                result['data_synced'] = self._sync_graph(
                    ontology_manager.data_graph,
                    graph_name='data'
                )
            
            self.conn.commit()
            print(f"[SysCREDStore] Synced {result['base_synced']} base + {result['data_synced']} data triples")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"[SysCREDStore] Sync error: {e}")
        
        return result
    
    def _sync_graph(self, graph, graph_name: str) -> int:
        """Sync un graphe RDFLib vers SQLite."""
        from rdflib import Literal
        
        count = 0
        cursor = self.conn.cursor()
        
        for s, p, o in graph:
            subject = str(s)
            predicate = str(p)
            obj_value = str(o)
            obj_type = 'literal' if isinstance(o, Literal) else 'uri'
            
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO rdf_triples 
                    (subject, predicate, object, object_type, graph_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (subject, predicate, obj_value, obj_type, graph_name))
                count += 1
            except:
                pass
        
        return count
    
    def get_triple_stats(self) -> Dict[str, int]:
        """Statistiques des triplets."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM rdf_triples WHERE graph_name = 'base'")
        base = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM rdf_triples WHERE graph_name = 'data'")
        data = cursor.fetchone()[0]
        
        return {
            'base_triples': base,
            'data_triples': data,
            'total_triples': base + data
        }
    
    # =========================================================================
    # ANALYSIS RESULTS
    # =========================================================================
    
    def save_analysis(self, url: str, credibility_score: float,
                      summary: str = None, score_details: Dict = None,
                      source_reputation: str = None, fact_check_count: int = 0) -> int:
        """Sauvegarde un résultat d'analyse."""
        domain = urlparse(url).netloc
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_results 
            (url, credibility_score, summary, score_details, source_reputation, 
             fact_check_count, domain)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            url, credibility_score, summary,
            json.dumps(score_details) if score_details else None,
            source_reputation, fact_check_count, domain
        ))
        self.conn.commit()
        
        result_id = cursor.lastrowid
        print(f"[SysCREDStore] Saved analysis #{result_id} for {domain}")
        
        # Update source stats
        self._update_source(domain, credibility_score)
        
        return result_id
    
    def get_history(self, url: str = None, limit: int = 50) -> List[Dict]:
        """Récupère l'historique des analyses."""
        cursor = self.conn.cursor()
        
        if url:
            cursor.execute("""
                SELECT * FROM analysis_results
                WHERE url = ? ORDER BY created_at DESC LIMIT ?
            """, (url, limit))
        else:
            cursor.execute("""
                SELECT * FROM analysis_results
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # SOURCES
    # =========================================================================
    
    def _update_source(self, domain: str, score: float = None):
        """Met à jour les stats d'une source."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id, analysis_count FROM sources WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("""
                UPDATE sources SET 
                    analysis_count = analysis_count + 1,
                    last_analyzed = CURRENT_TIMESTAMP,
                    reputation_score = COALESCE(?, reputation_score)
                WHERE domain = ?
            """, (score, domain))
        else:
            cursor.execute("""
                INSERT INTO sources (domain, reputation_score, analysis_count, last_analyzed)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            """, (domain, score))
        
        self.conn.commit()
    
    def get_source(self, domain: str) -> Optional[Dict]:
        """Récupère les infos d'une source."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE domain = ?", (domain,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # =========================================================================
    # GLOBAL STATS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques globales."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        total_analyses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sources")
        unique_domains = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(credibility_score) FROM analysis_results")
        avg_score = cursor.fetchone()[0]
        
        triple_stats = self.get_triple_stats()
        
        return {
            'total_analyses': total_analyses,
            'unique_domains': unique_domains,
            'avg_credibility': round(avg_score, 2) if avg_score else None,
            **triple_stats
        }
    
    def close(self):
        """Ferme la connexion."""
        if self.conn:
            self.conn.close()


# ============================================================================
# INTEGRATION
# ============================================================================

def sync_ontology_to_db():
    """Synchronise l'ontologie vers la base de données."""
    import sys
    sys.path.insert(0, str(BASE_DIR))
    
    try:
        from ontology_manager import OntologyManager
        from config import Config
        
        # Init ontology
        onto = OntologyManager(
            base_ontology_path=str(Config.ONTOLOGY_BASE_PATH),
            data_path=str(Config.ONTOLOGY_DATA_PATH)
        )
        
        # Init store
        store = SysCREDStore()
        
        # Sync
        result = store.sync_ontology(onto)
        print(f"\n✅ Sync complete: {result}")
        
        # Stats
        stats = store.get_stats()
        print(f"📊 Stats: {stats}")
        
        return store
        
    except ImportError as e:
        print(f"Import error: {e}")
        return None


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED Storage - Synchronisation des triplets")
    print("=" * 60)
    
    store = sync_ontology_to_db()
    
    if store:
        print("\n✅ Base de données prête!")
        print(f"   Fichier: {store.db_path}")
