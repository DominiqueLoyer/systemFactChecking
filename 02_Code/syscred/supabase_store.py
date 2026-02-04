"""
SysCRED Supabase Storage Module
===============================
Synchronise les triplets RDF et résultats d'analyse avec Supabase PostgreSQL.

Usage:
    from supabase_store import SupabaseStore
    
    store = SupabaseStore()
    store.sync_ontology_to_db(ontology_manager)
    store.save_analysis_result(url, score, details)
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extras import execute_values, Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("[SupabaseStore] psycopg2 not installed. Run: pip install psycopg2-binary")

# Default DATABASE_URL for SysCRED Supabase
DEFAULT_DATABASE_URL = "postgresql://postgres:FactCheckingSystem2026_test@db.zmluirvqfkmfazqitqgi.supabase.co:5432/postgres"


class SupabaseStore:
    """
    Gestionnaire de stockage Supabase pour SysCRED.
    Gère la synchronisation bidirectionnelle entre RDFLib et PostgreSQL.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize connection to Supabase PostgreSQL.
        
        Args:
            database_url: PostgreSQL connection string. 
                          Falls back to DATABASE_URL env var or default.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        self.conn = None
        self._connected = False
        
        if not PSYCOPG2_AVAILABLE:
            print("[SupabaseStore] WARNING: psycopg2 not available, database disabled")
            return
            
        self._connect()
    
    def _connect(self) -> bool:
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            self._connected = True
            print(f"[SupabaseStore] Connected to Supabase PostgreSQL")
            return True
        except Exception as e:
            print(f"[SupabaseStore] Connection failed: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if database connection is active."""
        if not self._connected or not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except:
            self._connected = False
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self._connected = False
            print("[SupabaseStore] Connection closed")
    
    # =========================================================================
    # ONTOLOGY / RDF TRIPLES
    # =========================================================================
    
    def sync_ontology_to_db(self, ontology_manager) -> Dict[str, int]:
        """
        Synchronize RDFLib graphs to Supabase rdf_triples table.
        
        Args:
            ontology_manager: Instance of OntologyManager with base_graph and data_graph
            
        Returns:
            Dict with counts: {'base_synced': N, 'data_synced': M}
        """
        if not self.is_connected():
            return {'error': 'Not connected to database'}
        
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
            print(f"[SupabaseStore] Synced {result['base_synced']} base + {result['data_synced']} data triples")
            
        except Exception as e:
            self.conn.rollback()
            result['error'] = str(e)
            print(f"[SupabaseStore] Sync error: {e}")
        
        return result
    
    def _sync_graph(self, graph, graph_name: str) -> int:
        """Sync a single RDFLib graph to database."""
        from rdflib import Literal, URIRef
        
        triples_data = []
        
        for s, p, o in graph:
            subject = str(s)
            predicate = str(p)
            
            if isinstance(o, Literal):
                obj_value = str(o)
                obj_type = 'literal' if o.datatype is None else 'typed_literal'
                obj_datatype = str(o.datatype) if o.datatype else None
                obj_lang = o.language
            else:
                obj_value = str(o)
                obj_type = 'uri'
                obj_datatype = None
                obj_lang = None
            
            triples_data.append((
                subject, predicate, obj_value, 
                obj_type, obj_datatype, obj_lang, graph_name
            ))
        
        if not triples_data:
            return 0
        
        with self.conn.cursor() as cur:
            # Use ON CONFLICT to avoid duplicates
            execute_values(
                cur,
                """
                INSERT INTO rdf_triples 
                    (subject, predicate, object, object_type, object_datatype, object_lang, graph_name)
                VALUES %s
                ON CONFLICT (subject, predicate, object, graph_name) DO NOTHING
                """,
                triples_data
            )
        
        return len(triples_data)
    
    def load_triples_from_db(self, graph_name: str = 'data') -> List[Tuple[str, str, str]]:
        """
        Load triples from database back into RDFLib format.
        
        Args:
            graph_name: 'base' or 'data'
            
        Returns:
            List of (subject, predicate, object) tuples
        """
        if not self.is_connected():
            return []
        
        triples = []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT subject, predicate, object, object_type, object_datatype, object_lang
                    FROM rdf_triples
                    WHERE graph_name = %s
                """, (graph_name,))
                
                for row in cur.fetchall():
                    triples.append((row[0], row[1], row[2]))
                    
        except Exception as e:
            print(f"[SupabaseStore] Load error: {e}")
        
        return triples
    
    def get_triple_stats(self) -> Dict[str, int]:
        """Get statistics about stored triples."""
        if not self.is_connected():
            return {'error': 'Not connected'}
        
        stats = {}
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT graph_name, COUNT(*) 
                    FROM rdf_triples 
                    GROUP BY graph_name
                """)
                for row in cur.fetchall():
                    stats[f"{row[0]}_triples"] = row[1]
                
                cur.execute("SELECT COUNT(*) FROM rdf_triples")
                stats['total_triples'] = cur.fetchone()[0]
                
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    # =========================================================================
    # ANALYSIS RESULTS
    # =========================================================================
    
    def save_analysis_result(
        self, 
        url: str, 
        credibility_score: float,
        summary: str = None,
        score_details: Dict = None,
        source_reputation: str = None,
        fact_check_count: int = 0
    ) -> Optional[int]:
        """
        Save an analysis result to Supabase.
        
        Returns:
            The ID of the inserted row, or None on error
        """
        if not self.is_connected():
            return None
        
        try:
            domain = urlparse(url).netloc
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO analysis_results 
                        (url, credibility_score, summary, score_details, 
                         source_reputation, fact_check_count, domain)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    url, credibility_score, summary,
                    Json(score_details) if score_details else None,
                    source_reputation, fact_check_count, domain
                ))
                
                result_id = cur.fetchone()[0]
                self.conn.commit()
                
                print(f"[SupabaseStore] Saved analysis #{result_id} for {domain}")
                return result_id
                
        except Exception as e:
            self.conn.rollback()
            print(f"[SupabaseStore] Save error: {e}")
            return None
    
    def get_analysis_history(self, url: str = None, limit: int = 50) -> List[Dict]:
        """
        Retrieve analysis history, optionally filtered by URL.
        """
        if not self.is_connected():
            return []
        
        results = []
        try:
            with self.conn.cursor() as cur:
                if url:
                    cur.execute("""
                        SELECT id, url, credibility_score, summary, created_at, 
                               source_reputation, score_details
                        FROM analysis_results
                        WHERE url = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (url, limit))
                else:
                    cur.execute("""
                        SELECT id, url, credibility_score, summary, created_at,
                               source_reputation, score_details
                        FROM analysis_results
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                
                for row in cur.fetchall():
                    results.append({
                        'id': row[0],
                        'url': row[1],
                        'credibility_score': row[2],
                        'summary': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'source_reputation': row[5],
                        'score_details': row[6]
                    })
                    
        except Exception as e:
            print(f"[SupabaseStore] History error: {e}")
        
        return results
    
    # =========================================================================
    # SOURCES
    # =========================================================================
    
    def upsert_source(self, domain: str, reputation_score: float = None, 
                      domain_age: float = None, is_fact_checker: bool = False,
                      metadata: Dict = None) -> bool:
        """Insert or update a source domain."""
        if not self.is_connected():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sources (domain, reputation_score, domain_age_years, 
                                         is_fact_checker, metadata, last_analyzed, analysis_count)
                    VALUES (%s, %s, %s, %s, %s, NOW(), 1)
                    ON CONFLICT (domain) DO UPDATE SET
                        reputation_score = COALESCE(EXCLUDED.reputation_score, sources.reputation_score),
                        domain_age_years = COALESCE(EXCLUDED.domain_age_years, sources.domain_age_years),
                        is_fact_checker = COALESCE(EXCLUDED.is_fact_checker, sources.is_fact_checker),
                        last_analyzed = NOW(),
                        analysis_count = sources.analysis_count + 1
                """, (domain, reputation_score, domain_age, is_fact_checker, 
                      Json(metadata) if metadata else None))
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"[SupabaseStore] Source upsert error: {e}")
            return False
    
    def get_source(self, domain: str) -> Optional[Dict]:
        """Get source info by domain."""
        if not self.is_connected():
            return None
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT domain, reputation_score, domain_age_years, 
                           is_fact_checker, analysis_count, last_analyzed
                    FROM sources WHERE domain = %s
                """, (domain,))
                
                row = cur.fetchone()
                if row:
                    return {
                        'domain': row[0],
                        'reputation_score': row[1],
                        'domain_age_years': row[2],
                        'is_fact_checker': row[3],
                        'analysis_count': row[4],
                        'last_analyzed': row[5].isoformat() if row[5] else None
                    }
        except Exception as e:
            print(f"[SupabaseStore] Source get error: {e}")
        
        return None
    
    # =========================================================================
    # CLAIMS & EVIDENCE (for TREC integration)
    # =========================================================================
    
    def save_claim(self, claim_text: str, source_url: str = None,
                   entities: Dict = None, score: float = None) -> Optional[int]:
        """Save a claim for fact-checking."""
        if not self.is_connected():
            return None
        
        claim_hash = hashlib.sha256(claim_text.encode()).hexdigest()
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO claims (claim_text, claim_hash, source_url, 
                                       extracted_entities, credibility_score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (claim_hash) DO UPDATE SET
                        credibility_score = COALESCE(EXCLUDED.credibility_score, claims.credibility_score)
                    RETURNING id
                """, (claim_text, claim_hash, source_url, 
                      Json(entities) if entities else None, score))
                
                claim_id = cur.fetchone()[0]
                self.conn.commit()
                return claim_id
                
        except Exception as e:
            self.conn.rollback()
            print(f"[SupabaseStore] Claim save error: {e}")
            return None
    
    def save_evidence(self, claim_id: int, doc_id: str, doc_text: str,
                      relevance_score: float, method: str = 'bm25') -> bool:
        """Save evidence retrieved from TREC corpus."""
        if not self.is_connected():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO evidence (claim_id, doc_id, doc_text, 
                                         relevance_score, retrieval_method)
                    VALUES (%s, %s, %s, %s, %s)
                """, (claim_id, doc_id, doc_text, relevance_score, method))
                
                # Update evidence count on claim
                cur.execute("""
                    UPDATE claims SET evidence_count = evidence_count + 1
                    WHERE id = %s
                """, (claim_id,))
                
                self.conn.commit()
                return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"[SupabaseStore] Evidence save error: {e}")
            return False
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics from syscred_stats view."""
        if not self.is_connected():
            return {'error': 'Not connected'}
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM syscred_stats")
                row = cur.fetchone()
                if row:
                    return {
                        'total_analyses': row[0],
                        'unique_domains': row[1],
                        'base_triples': row[2],
                        'data_triples': row[3],
                        'total_claims': row[4],
                        'avg_credibility': round(row[5], 2) if row[5] else None
                    }
        except Exception as e:
            # View might not exist yet
            return {'error': str(e)}
        
        return {}


# ============================================================================
# INTEGRATION WITH ONTOLOGY MANAGER
# ============================================================================

def integrate_with_ontology_manager():
    """
    Example of how to integrate SupabaseStore with OntologyManager.
    Call this after initializing SysCRED.
    """
    from ontology_manager import OntologyManager
    
    # Initialize both
    onto = OntologyManager(
        base_ontology_path="sysCRED_onto26avrtil.ttl",
        data_path="ontology/sysCRED_data.ttl"
    )
    store = SupabaseStore()
    
    # Sync to database
    if store.is_connected():
        result = store.sync_ontology_to_db(onto)
        print(f"Sync result: {result}")
        
        # Get stats
        stats = store.get_global_stats()
        print(f"DB Stats: {stats}")
    
    return onto, store


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Supabase Connection...")
    print("=" * 60)
    
    store = SupabaseStore()
    
    if store.is_connected():
        print("\n✅ Connected to Supabase!")
        
        # Test save
        result_id = store.save_analysis_result(
            url="https://example.com/test",
            credibility_score=0.75,
            summary="Test analysis",
            score_details={'reputation': 0.8, 'coherence': 0.7}
        )
        print(f"Saved analysis with ID: {result_id}")
        
        # Get stats
        stats = store.get_triple_stats()
        print(f"Triple stats: {stats}")
        
        store.close()
    else:
        print("\n❌ Could not connect to Supabase")
        print("Check your DATABASE_URL environment variable")
