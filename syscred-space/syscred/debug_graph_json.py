import sys
from pathlib import Path
import json

# Add project root to path (one level up from this script)
sys.path.append(str(Path(__file__).parent.parent))

from syscred.ontology_manager import OntologyManager
from syscred.config import config

def debug_graph():
    print("=== Debugging Ontology Graph Extraction ===")
    
    # Initialize manager
    base_path = str(config.ONTOLOGY_BASE_PATH)
    data_path = str(config.ONTOLOGY_DATA_PATH)
    
    print(f"Loading data from: {data_path}")
    manager = OntologyManager(base_ontology_path=base_path, data_path=data_path)
    
    # Get Stats
    stats = manager.get_statistics()
    print(f"Total Triples: {stats['total_triples']}")
    print(f"Evaluations: {stats.get('total_evaluations', 'N/A')}")
    
    # Try getting graph JSON
    print("\nExtracting Graph JSON...")
    graph_data = manager.get_graph_json()
    
    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])
    
    print(f"Nodes found: {len(nodes)}")
    print(f"Links found: {len(links)}")
    
    if len(nodes) > 0:
        print("\n--- Sample Nodes ---")
        for n in nodes[:3]:
            print(json.dumps(n, indent=2))
    else:
        print("\n❌ No nodes found! Checking latest report query...")
        # Manually run the query to see what's wrong
        query = """
        PREFIX cred: <http://www.dic9335.uqam.ca/ontologies/credibility-verification#>
        SELECT ?report ?timestamp WHERE {
            ?report a cred:RapportEvaluation .
            ?report cred:completionTimestamp ?timestamp .
        }
        ORDER BY DESC(?timestamp)
        LIMIT 5
        """
        print(f"Running SPARQL:\n{query}")
        results = manager.data_graph.query(query)
        for row in results:
            print(f"Found Report: {row.report} at {row.timestamp}")

if __name__ == "__main__":
    debug_graph()
