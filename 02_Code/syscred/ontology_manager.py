# -*- coding: utf-8 -*-
"""
Ontology Manager Module - SysCRED
==================================
Manages the RDF ontology for the credibility verification system.
Handles reading, writing, and querying of semantic triplets.

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerModelingHybridSystem2025
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import os

# RDFLib imports with fallback
try:
    from rdflib import Graph, Namespace, Literal, URIRef, BNode
    from rdflib.namespace import RDF, RDFS, OWL, XSD
    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False
    print("Warning: rdflib not installed. Run: pip install rdflib")


@dataclass
class EvaluationRecord:
    """Represents a stored evaluation from the ontology."""
    evaluation_id: str
    url_or_text: str
    score: float
    level: str
    timestamp: str
    fact_checks: List[str]


class OntologyManager:
    """
    Manages the credibility ontology using RDFLib.
    
    Handles:
    - Loading base ontology
    - Adding evaluation triplets
    - Querying historical data
    - Exporting enriched ontology
    """
    
    # Namespace for the credibility ontology
    CRED_NS = "https://github.com/DominiqueLoyer/systemFactChecking#"
    
    def __init__(self, base_ontology_path: Optional[str] = None, data_path: Optional[str] = None):
        """
        Initialize the ontology manager.
        
        Args:
            base_ontology_path: Path to the base ontology TTL file
            data_path: Path to store/load accumulated data triplets
        """
        if not HAS_RDFLIB:
            raise ImportError("rdflib is required. Install with: pip install rdflib")
        
        self.base_path = base_ontology_path
        self.data_path = data_path
        
        # Create namespace
        self.cred = Namespace(self.CRED_NS)
        
        # Initialize graphs
        self.base_graph = Graph()
        self.data_graph = Graph()
        
        # Bind prefixes for nicer serialization
        self._bind_prefixes(self.base_graph)
        self._bind_prefixes(self.data_graph)
        
        # Load ontology files if they exist
        if base_ontology_path and os.path.exists(base_ontology_path):
            self.load_base_ontology(base_ontology_path)
        
        if data_path and os.path.exists(data_path):
            self.load_data_graph(data_path)
        
        # Counter for generating unique IDs
        self._evaluation_counter = 0
    
    def _bind_prefixes(self, graph: Graph):
        """Bind common prefixes to a graph."""
        graph.bind("cred", self.cred)
        graph.bind("owl", OWL)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("xsd", XSD)
    
    def load_base_ontology(self, path: str) -> bool:
        """Load the base ontology from a TTL file."""
        try:
            self.base_graph.parse(path, format='turtle')
            print(f"[OntologyManager] Loaded base ontology: {len(self.base_graph)} triples")
            return True
        except Exception as e:
            print(f"[OntologyManager] Error loading base ontology: {e}")
            return False
    
    def load_data_graph(self, path: str) -> bool:
        """Load accumulated data triplets."""
        try:
            self.data_graph.parse(path, format='turtle')
            print(f"[OntologyManager] Loaded data graph: {len(self.data_graph)} triples")
            return True
        except Exception as e:
            print(f"[OntologyManager] Error loading data graph: {e}")
            return False
    
    def add_evaluation_triplets(self, report: Dict[str, Any]) -> str:
        """
        Add triplets for a new credibility evaluation.
        
        Args:
            report: The evaluation report dictionary from CredibilityVerificationSystem
            
        Returns:
            The URI of the created RapportEvaluation individual
        """
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        self._evaluation_counter += 1
        
        # Create URIs for new individuals
        report_uri = self.cred[f"Report_{timestamp_str}_{self._evaluation_counter}"]
        request_uri = self.cred[f"Request_{timestamp_str}_{self._evaluation_counter}"]
        info_uri = self.cred[f"Info_{timestamp_str}_{self._evaluation_counter}"]
        
        # Get data from report
        score = report.get('scoreCredibilite', 0.5)
        input_data = report.get('informationEntree', '')
        summary = report.get('resumeAnalyse', '')
        
        # Determine credibility level based on score
        if score >= 0.7:
            level_uri = self.cred.Niveau_Haut
            info_class = self.cred.InformationHauteCredibilite
        elif score >= 0.4:
            level_uri = self.cred.Niveau_Moyen
            info_class = self.cred.InformationMoyenneCredibilite
        else:
            level_uri = self.cred.Niveau_Bas
            info_class = self.cred.InformationFaibleCredibilite
        
        # Add Information triplets
        self.data_graph.add((info_uri, RDF.type, self.cred.InformationSoumise))
        self.data_graph.add((info_uri, RDF.type, info_class))
        self.data_graph.add((info_uri, self.cred.informationContent, 
                            Literal(input_data[:500], datatype=XSD.string)))
        
        # Check if it's a URL
        if input_data.startswith('http'):
            self.data_graph.add((info_uri, self.cred.informationURL, 
                                Literal(input_data, datatype=XSD.anyURI)))
        
        # Add Request triplets
        self.data_graph.add((request_uri, RDF.type, self.cred.RequeteEvaluation))
        self.data_graph.add((request_uri, self.cred.concernsInformation, info_uri))
        self.data_graph.add((request_uri, self.cred.submissionTimestamp, 
                            Literal(timestamp.isoformat(), datatype=XSD.dateTime)))
        self.data_graph.add((request_uri, self.cred.requestStatus, 
                            Literal("Completed", datatype=XSD.string)))
        
        # Add Report triplets
        self.data_graph.add((report_uri, RDF.type, self.cred.RapportEvaluation))
        self.data_graph.add((report_uri, self.cred.isReportOf, request_uri))
        self.data_graph.add((report_uri, self.cred.credibilityScoreValue, 
                            Literal(float(score), datatype=XSD.float)))
        self.data_graph.add((report_uri, self.cred.assignsCredibilityLevel, level_uri))
        self.data_graph.add((report_uri, self.cred.completionTimestamp, 
                            Literal(timestamp.isoformat(), datatype=XSD.dateTime)))
        self.data_graph.add((report_uri, self.cred.reportSummary, 
                            Literal(summary, datatype=XSD.string)))
        
        # Add NLP results if available
        nlp_results = report.get('analyseNLP', {})
        if nlp_results:
            nlp_result_uri = self.cred[f"NLPResult_{timestamp_str}_{self._evaluation_counter}"]
            self.data_graph.add((nlp_result_uri, RDF.type, self.cred.ResultatNLP))
            self.data_graph.add((report_uri, self.cred.includesNLPResult, nlp_result_uri))
            
            sentiment = nlp_results.get('sentiment', {})
            if sentiment:
                self.data_graph.add((nlp_result_uri, self.cred.sentimentScore, 
                                    Literal(float(sentiment.get('score', 0.5)), datatype=XSD.float)))
            
            coherence = nlp_results.get('coherence_score')
            if coherence is not None:
                self.data_graph.add((nlp_result_uri, self.cred.coherenceScore, 
                                    Literal(float(coherence), datatype=XSD.float)))
        
        # Add source analysis if available
        rules = report.get('reglesAppliquees', {})
        source_analysis = rules.get('source_analysis', {})
        if source_analysis:
            source_uri = self.cred[f"SourceAnalysis_{timestamp_str}_{self._evaluation_counter}"]
            self.data_graph.add((source_uri, RDF.type, self.cred.InfoSourceAnalyse))
            self.data_graph.add((report_uri, self.cred.includesSourceAnalysis, source_uri))
            
            reputation = source_analysis.get('reputation', 'Unknown')
            self.data_graph.add((source_uri, self.cred.sourceAnalyzedReputation, 
                                Literal(reputation, datatype=XSD.string)))
            
            domain_age = source_analysis.get('domain_age_days')
            if domain_age is not None:
                self.data_graph.add((source_uri, self.cred.sourceMentionsCount, 
                                    Literal(int(domain_age), datatype=XSD.integer)))
        
        # Add fact check results
        fact_checks = rules.get('fact_checking', [])
        for i, fc in enumerate(fact_checks):
            evidence_uri = self.cred[f"Evidence_{timestamp_str}_{self._evaluation_counter}_{i}"]
            self.data_graph.add((evidence_uri, RDF.type, self.cred.PreuveFactuelle))
            self.data_graph.add((report_uri, self.cred.basedOnEvidence, evidence_uri))
            
            self.data_graph.add((evidence_uri, self.cred.evidenceClaim, 
                                Literal(fc.get('claim', ''), datatype=XSD.string)))
            self.data_graph.add((evidence_uri, self.cred.evidenceVerdict, 
                                Literal(fc.get('rating', ''), datatype=XSD.string)))
            self.data_graph.add((evidence_uri, self.cred.evidenceSource, 
                                Literal(fc.get('publisher', ''), datatype=XSD.string)))
            if fc.get('url'):
                self.data_graph.add((evidence_uri, self.cred.evidenceURL, 
                                    Literal(fc.get('url', ''), datatype=XSD.anyURI)))
                                    
        # [NEW] Link similar claims found by GraphRAG
        similar_uris = report.get('similar_claims_uris', [])
        for sim_uri_str in similar_uris:
            try:
                sim_uri = URIRef(sim_uri_str)
                self.data_graph.add((report_uri, RDFS.seeAlso, sim_uri))
            except Exception as e:
                print(f"[Ontology] Error linking similar URI {sim_uri_str}: {e}")
                
        print(f"[OntologyManager] Added evaluation triplets. Report: {report_uri}")
        return str(report_uri)
    
    def query_source_history(self, url: str) -> List[EvaluationRecord]:
        """
        Query all previous evaluations for a URL/domain.
        
        Args:
            url: URL to search for
            
        Returns:
            List of EvaluationRecord for this source
        """
        results = []
        
        # SPARQL query to find all evaluations for this URL
        query = """
        PREFIX cred: <http://www.dic9335.uqam.ca/ontologies/credibility-verification#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        
        SELECT ?report ?score ?level ?timestamp ?content
        WHERE {
            ?info cred:informationURL ?url .
            ?request cred:concernsInformation ?info .
            ?report cred:isReportOf ?request .
            ?report cred:credibilityScoreValue ?score .
            ?report cred:assignsCredibilityLevel ?level .
            ?report cred:completionTimestamp ?timestamp .
            ?info cred:informationContent ?content .
            FILTER(CONTAINS(STR(?url), "%s"))
        }
        ORDER BY DESC(?timestamp)
        """ % url
        
        try:
            # Query combined graph (base + data)
            combined = self.base_graph + self.data_graph
            for row in combined.query(query):
                results.append(EvaluationRecord(
                    evaluation_id=str(row.report),
                    url_or_text=str(row.content) if row.content else url,
                    score=float(row.score),
                    level=str(row.level).split('#')[-1],
                    timestamp=str(row.timestamp),
                    fact_checks=[]
                ))
        except Exception as e:
            print(f"[OntologyManager] Query error: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the ontology data."""
        stats = {
            'base_triples': len(self.base_graph),
            'data_triples': len(self.data_graph),
            'total_triples': len(self.base_graph) + len(self.data_graph),
        }
        
        # Count evaluations
        query = """
        PREFIX cred: <http://www.dic9335.uqam.ca/ontologies/credibility-verification#>
        SELECT (COUNT(?report) as ?count) WHERE {
            ?report a cred:RapportEvaluation .
        }
        """
        try:
            for row in self.data_graph.query(query):
                stats['total_evaluations'] = int(row.count)
        except:
            stats['total_evaluations'] = 0
        
        return stats
    
    def get_graph_json(self) -> Dict[str, List]:
        """
        Convert ontology data into D3.js JSON format (Nodes & Links).
        """
        nodes = []
        links = []
        added_nodes = set()
        
        # Get the latest report ID
        latest_query = """
        PREFIX cred: <https://github.com/DominiqueLoyer/systemFactChecking#>
        SELECT ?report ?timestamp WHERE {
            ?report a cred:RapportEvaluation .
            ?report cred:completionTimestamp ?timestamp .
        }
        ORDER BY DESC(?timestamp)
        LIMIT 1
        """
        latest_report = None
        try:
            for row in self.data_graph.query(latest_query):
                latest_report = row.report
        except:
            pass
            
        if not latest_report:
            return {'nodes': [], 'links': []}
            
        # Helper to add node if unique
        def add_node(uri, label, type_class, group):
            if str(uri) not in added_nodes:
                nodes.append({
                    'id': str(uri),
                    'name': str(label),
                    'group': group,
                    'type': str(type_class).split('#')[-1]
                })
                added_nodes.add(str(uri))
        
        # Add Central Node (Report)
        add_node(latest_report, "Latest Report", "cred:RapportEvaluation", 1)
        
        # Query triples related to this report (Level 1)
        related_query = """
        PREFIX cred: <https://github.com/DominiqueLoyer/systemFactChecking#>
        SELECT ?p ?o ?oType ?oLabel WHERE {
            <%s> ?p ?o .
            OPTIONAL { ?o a ?oType } .
            OPTIONAL { ?o cred:evidenceSnippet ?oLabel } .
            OPTIONAL { ?o cred:sourceAnalyzedReputation ?oLabel } .
        }
        """ % str(latest_report)
        
        try:
            # Level 1: Report -> Components
            for row in self.data_graph.query(related_query):
                p = row.p
                o = row.o
                
                # Skip generic system triples like rdf:type, but allow rdfs:seeAlso
                if str(p) == str(RDF.type): continue
                if 'Literal' in str(type(o)): continue # Skip basic literals
                
                # Determine Group/Color
                o_type = str(row.oType) if row.oType else "Unknown"
                group = 2 # Default gray
                if 'High' in o_type or 'Supporting' in o_type: group = 3 # Green (Positive)
                if 'Low' in o_type or 'Refuting' in o_type: group = 4 # Red (Negative)
                if 'Rapport' in o_type: group = 1 # Purple (Hub)
                if 'SourceAnalysis' in o_type: group = 5 # Blue (Source)
                if str(p) == str(RDFS.seeAlso): group = 7 # Orange for similar claims
                
                # Add Target Node (Level 1)
                o_label = row.oLabel if row.oLabel else str(o).split('#')[-1]
                add_node(o, o_label, o_type, group)
                
                # Add Link L1
                link_type = 'primary'
                if str(p) == str(RDFS.seeAlso):
                     link_type = 'similar' # Special dash style for similar claims?
                
                links.append({
                    'source': str(latest_report),
                    'target': str(o),
                    'value': 2,
                    'type': link_type
                })
                
                # Level 2: Component -> Details (Recursive enrich)
                # Specifically for SourceAnalysis and Evidence
                l2_query = """
                SELECT ?p2 ?o2 ?o2Type WHERE {
                    <%s> ?p2 ?o2 .
                    OPTIONAL { ?o2 a ?o2Type } .
                    FILTER(isURI(?o2))
                }""" % str(o)
                
                for row2 in self.data_graph.query(l2_query):
                     o2 = row2.o2
                     if str(row2.p2) == str(RDF.type): continue
                     
                     o2_label = str(o2).split('#')[-1]
                     add_node(o2, o2_label, "Detail", 6) # Group 6 for leaf nodes
                     
                     links.append({
                        'source': str(o),
                        'target': str(o2),
                        'value': 1,
                        'type': 'secondary'
                     })

        except Exception as e:
            print(f"Graph query error: {e}")
            
        return {'nodes': nodes, 'links': links}
    
    def export_to_ttl(self, output_path: str, include_base: bool = False) -> bool:
        """
        Export the ontology to a TTL file.
        
        Args:
            output_path: Path to write the TTL file
            include_base: If True, include base ontology in export
            
        Returns:
            True if successful
        """
        try:
            if include_base:
                combined = self.base_graph + self.data_graph
                combined.serialize(destination=output_path, format='turtle')
            else:
                self.data_graph.serialize(destination=output_path, format='turtle')
            
            print(f"[OntologyManager] Exported to: {output_path}")
            return True
        except Exception as e:
            print(f"[OntologyManager] Export error: {e}")
            return False
    
    def save_data(self) -> bool:
        """Save the data graph to its configured path."""
        if self.data_path:
            return self.export_to_ttl(self.data_path, include_base=False)
        return False


# --- Testing ---
if __name__ == "__main__":
    print("=== Testing OntologyManager ===\n")
    
    # Test with base ontology
    base_path = "/Users/bk280625/documents041025/MonCode/sysCRED_onto26avrtil.ttl"
    data_path = "/Users/bk280625/documents041025/MonCode/ontology/sysCRED_data.ttl"
    
    manager = OntologyManager(base_ontology_path=base_path, data_path=None)
    
    # Test adding evaluation
    sample_report = {
        'scoreCredibilite': 0.72,
        'informationEntree': 'https://www.lemonde.fr/article/test',
        'resumeAnalyse': "L'analyse suggère une crédibilité MOYENNE à ÉLEVÉE.",
        'analyseNLP': {
            'sentiment': {'label': 'POSITIVE', 'score': 0.85},
            'coherence_score': 0.78
        },
        'reglesAppliquees': {
            'source_analysis': {
                'reputation': 'High',
                'domain_age_days': 9000
            },
            'fact_checking': [
                {'claim': 'Article verified by fact-checkers', 'rating': 'True'}
            ]
        }
    }
    
    print("Test 1: Adding evaluation triplets...")
    report_uri = manager.add_evaluation_triplets(sample_report)
    print(f"  Created: {report_uri}")
    print()
    
    # Test statistics
    print("Test 2: Getting statistics...")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Export test
    print("Test 3: Exporting data graph...")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    manager.export_to_ttl(data_path)
    print(f"  Exported to: {data_path}")
    
    print("\n=== Tests Complete ===")
