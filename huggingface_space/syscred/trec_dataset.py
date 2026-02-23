# -*- coding: utf-8 -*-
"""
TREC Dataset Module - SysCRED
==============================
Loader and utilities for TREC AP88-90 dataset.

Handles:
- Topic/Query parsing
- Qrels (relevance judgments) loading
- Document corpus loading
- TREC run file generation

Based on: TREC_AP88-90_5juin2025.py
(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerEvaluationModelesRecherche2025
"""

import os
import re
import json
import tarfile
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TRECTopic:
    """A TREC topic (query)."""
    topic_id: str
    title: str  # Short query
    description: str  # Long description
    narrative: str = ""  # Full narrative (optional)
    
    @property
    def short_query(self) -> str:
        return self.title
    
    @property
    def long_query(self) -> str:
        return f"{self.title} {self.description}".strip()


@dataclass
class TRECQrel:
    """A relevance judgment."""
    topic_id: str
    doc_id: str
    relevance: int  # 0=not relevant, 1=relevant, 2+=highly relevant


@dataclass
class TRECDocument:
    """A document from the corpus."""
    doc_id: str
    text: str
    title: str = ""
    date: str = ""
    source: str = ""


class TRECDataset:
    """
    TREC AP88-90 Dataset loader and manager.
    
    Provides utilities for:
    - Loading topics (queries)
    - Loading qrels (relevance judgments)
    - Loading document corpus
    - Creating TREC-format run files
    
    Usage:
        dataset = TRECDataset(base_path="/path/to/trec")
        topics = dataset.load_topics()
        qrels = dataset.load_qrels()
    """
    
    # Standard TREC file patterns
    TOPIC_PATTERN = r"topics\.\d+\.txt"
    QREL_PATTERN = r"qrels\.\d+\.txt"
    
    def __init__(
        self,
        base_path: Optional[str] = None,
        topics_dir: Optional[str] = None,
        qrels_dir: Optional[str] = None,
        corpus_path: Optional[str] = None
    ):
        """
        Initialize the dataset loader.
        
        Args:
            base_path: Base path containing TREC data
            topics_dir: Path to topics directory (overrides base_path)
            qrels_dir: Path to qrels directory (overrides base_path)
            corpus_path: Path to corpus file (AP.tar or JSONL)
        """
        self.base_path = Path(base_path) if base_path else None
        self.topics_dir = Path(topics_dir) if topics_dir else None
        self.qrels_dir = Path(qrels_dir) if qrels_dir else None
        self.corpus_path = Path(corpus_path) if corpus_path else None
        
        # Loaded data
        self.topics: Dict[str, TRECTopic] = {}
        self.qrels: Dict[str, Dict[str, int]] = {}  # topic_id -> {doc_id: relevance}
        self.documents: Dict[str, TRECDocument] = {}
        
        # Statistics
        self.stats = {
            "topics_loaded": 0,
            "qrels_loaded": 0,
            "docs_loaded": 0
        }
    
    def load_topics(self, topics_path: Optional[str] = None) -> Dict[str, TRECTopic]:
        """
        Load TREC topics from file(s).
        
        Supports standard TREC topic format with <top>, <num>, <title>, <desc>, <narr> tags.
        """
        search_path = Path(topics_path) if topics_path else self.topics_dir or self.base_path
        
        if not search_path or not search_path.exists():
            print(f"[TRECDataset] Topics path not found: {search_path}")
            return {}
        
        topic_files = []
        if search_path.is_file():
            topic_files = [search_path]
        else:
            topic_files = list(search_path.glob("topics*.txt"))
        
        for topic_file in topic_files:
            self._parse_topic_file(topic_file)
        
        self.stats["topics_loaded"] = len(self.topics)
        print(f"[TRECDataset] Loaded {len(self.topics)} topics from {len(topic_files)} files")
        
        return self.topics
    
    def _parse_topic_file(self, file_path: Path):
        """Parse a single TREC topic file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all <top>...</top> blocks
            for top_match in re.finditer(r"<top>(.*?)</top>", content, re.DOTALL):
                topic_content = top_match.group(1)
                
                # Extract fields
                num_match = re.search(r"<num>\s*(?:Number:)?\s*(\d+)", topic_content, re.IGNORECASE)
                if not num_match:
                    continue
                
                topic_id = num_match.group(1).strip()
                
                title_match = re.search(r"<title>\s*(.*?)\s*(?=<|$)", topic_content, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else ""
                
                desc_match = re.search(r"<desc>\s*(?:Description:)?\s*(.*?)\s*(?=<narr>|<|$)", topic_content, re.IGNORECASE | re.DOTALL)
                desc = desc_match.group(1).strip() if desc_match else ""
                
                narr_match = re.search(r"<narr>\s*(?:Narrative:)?\s*(.*?)\s*(?=<|$)", topic_content, re.IGNORECASE | re.DOTALL)
                narr = narr_match.group(1).strip() if narr_match else ""
                
                if topic_id and title:
                    self.topics[topic_id] = TRECTopic(
                        topic_id=topic_id,
                        title=title,
                        description=desc,
                        narrative=narr
                    )
        except Exception as e:
            print(f"[TRECDataset] Error parsing {file_path}: {e}")
    
    def load_qrels(self, qrels_path: Optional[str] = None) -> Dict[str, Dict[str, int]]:
        """
        Load TREC qrels (relevance judgments).
        
        Format: topic_id 0 doc_id relevance
        """
        search_path = Path(qrels_path) if qrels_path else self.qrels_dir or self.base_path
        
        if not search_path or not search_path.exists():
            print(f"[TRECDataset] Qrels path not found: {search_path}")
            return {}
        
        qrel_files = []
        if search_path.is_file():
            qrel_files = [search_path]
        else:
            qrel_files = list(search_path.glob("qrels*.txt")) + list(search_path.glob("*.qrels"))
        
        total_qrels = 0
        for qrel_file in qrel_files:
            count = self._parse_qrel_file(qrel_file)
            total_qrels += count
        
        self.stats["qrels_loaded"] = total_qrels
        print(f"[TRECDataset] Loaded {total_qrels} qrels from {len(qrel_files)} files")
        
        return self.qrels
    
    def _parse_qrel_file(self, file_path: Path) -> int:
        """Parse a single qrel file. Returns count of qrels loaded."""
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        topic_id = parts[0]
                        doc_id = parts[2]
                        relevance = int(parts[3])
                        
                        if topic_id not in self.qrels:
                            self.qrels[topic_id] = {}
                        
                        self.qrels[topic_id][doc_id] = relevance
                        count += 1
        except Exception as e:
            print(f"[TRECDataset] Error parsing {file_path}: {e}")
        
        return count
    
    def load_corpus_jsonl(self, jsonl_path: Optional[str] = None) -> Dict[str, TRECDocument]:
        """
        Load corpus from JSONL format.
        
        Expected format: {"id": "...", "contents": "...", "title": "..."}
        """
        path = Path(jsonl_path) if jsonl_path else self.corpus_path
        
        if not path or not path.exists():
            print(f"[TRECDataset] Corpus path not found: {path}")
            return {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    doc = json.loads(line.strip())
                    doc_id = doc.get('id', doc.get('docid', ''))
                    text = doc.get('contents', doc.get('text', ''))
                    title = doc.get('title', '')
                    
                    if doc_id:
                        self.documents[doc_id] = TRECDocument(
                            doc_id=doc_id,
                            text=text,
                            title=title
                        )
            
            self.stats["docs_loaded"] = len(self.documents)
            print(f"[TRECDataset] Loaded {len(self.documents)} documents")
            
        except Exception as e:
            print(f"[TRECDataset] Error loading corpus: {e}")
        
        return self.documents
    
    def get_relevant_docs(self, topic_id: str) -> Set[str]:
        """Get set of relevant document IDs for a topic."""
        if topic_id not in self.qrels:
            return set()
        
        return {
            doc_id for doc_id, rel in self.qrels[topic_id].items()
            if rel > 0
        }
    
    def get_topic_queries(self, query_type: str = "short") -> Dict[str, str]:
        """
        Get dictionary of topic_id -> query text.
        
        Args:
            query_type: "short" (title only) or "long" (title + description)
        """
        if query_type == "short":
            return {tid: t.short_query for tid, t in self.topics.items()}
        else:
            return {tid: t.long_query for tid, t in self.topics.items()}
    
    @staticmethod
    def format_trec_run(
        results: List[Tuple[str, str, float, int]],  # (topic_id, doc_id, score, rank)
        run_tag: str
    ) -> str:
        """
        Format results as TREC run file.
        
        Output format: topic_id Q0 doc_id rank score run_tag
        """
        lines = []
        for topic_id, doc_id, score, rank in results:
            lines.append(f"{topic_id} Q0 {doc_id} {rank} {score:.6f} {run_tag}")
        return "\n".join(lines)
    
    @staticmethod
    def save_trec_run(
        results: List[Tuple[str, str, float, int]],
        run_tag: str,
        output_path: str
    ):
        """Save results to TREC run file."""
        run_content = TRECDataset.format_trec_run(results, run_tag)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(run_content)
        print(f"[TRECDataset] Saved run file: {output_path}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Get dataset statistics."""
        return {
            "topics": len(self.topics),
            "qrels_topics": len(self.qrels),
            "total_qrels": sum(len(q) for q in self.qrels.values()),
            "documents": len(self.documents)
        }


# --- Sample Topics for Testing (AP88-90 subset) ---

SAMPLE_TOPICS = {
    "51": TRECTopic(
        topic_id="51",
        title="Airbus Subsidies",
        description="How much government money has been used to support Airbus aircraft manufacturing?",
        narrative="A relevant document will contain information on subsidies or other financial support from government sources to Airbus."
    ),
    "52": TRECTopic(
        topic_id="52", 
        title="Japanese Auto Sales",
        description="How have Japanese automobile sales fared in the U.S.?",
        narrative="A relevant document will report on sales figures, trends, or market share of Japanese automobile manufacturers in the United States."
    ),
    "53": TRECTopic(
        topic_id="53",
        title="Leveraged Buyouts",
        description="What are the effects of leveraged buyouts on companies and industries?",
        narrative="Relevant documents discuss the impact of LBOs on corporate structure, employment, or industry dynamics."
    ),
    "54": TRECTopic(
        topic_id="54",
        title="Satellite Launches",
        description="What are the commercial applications of satellite launches?",
        narrative="A relevant document will discuss commercial satellite launches and their business applications."
    ),
    "55": TRECTopic(
        topic_id="55",
        title="Insider Trading",
        description="What individuals or companies have been accused or convicted of insider trading?",
        narrative="A relevant document will identify specific cases of insider trading allegations or convictions."
    ),
}


def create_sample_dataset() -> TRECDataset:
    """Create a sample dataset for testing."""
    dataset = TRECDataset()
    dataset.topics = SAMPLE_TOPICS.copy()
    
    # Add sample qrels
    dataset.qrels = {
        "51": {"AP880212-0001": 1, "AP880215-0003": 1, "AP880301-0010": 0},
        "52": {"AP890102-0020": 1, "AP890115-0045": 1},
        "53": {"AP880325-0100": 1},
    }
    
    return dataset


# --- Testing ---

if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED TREC Dataset - Test Suite")
    print("=" * 60)
    
    # Create sample dataset
    dataset = create_sample_dataset()
    
    print(f"\n1. Sample Topics: {len(dataset.topics)}")
    for tid, topic in list(dataset.topics.items())[:3]:
        print(f"   {tid}: {topic.title}")
        print(f"      Short: {topic.short_query}")
        print(f"      Long: {topic.long_query[:80]}...")
    
    print(f"\n2. Sample Qrels:")
    for tid, docs in dataset.qrels.items():
        print(f"   Topic {tid}: {len(docs)} judgments")
    
    print(f"\n3. Query dictionaries:")
    short_queries = dataset.get_topic_queries("short")
    long_queries = dataset.get_topic_queries("long")
    print(f"   Short queries: {len(short_queries)}")
    print(f"   Long queries: {len(long_queries)}")
    
    print(f"\n4. Relevant docs for topic 51:")
    relevant = dataset.get_relevant_docs("51")
    print(f"   {relevant}")
    
    print(f"\n5. Statistics:")
    stats = dataset.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    print("=" * 60)
