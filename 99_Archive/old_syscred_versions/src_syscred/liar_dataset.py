# -*- coding: utf-8 -*-
"""
LIAR Dataset Module - SysCRED
==============================
Loader for the LIAR benchmark dataset (Wang, 2017).
Standard benchmark for fake news detection with 12,800+ political statements.

Dataset: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip
Paper: "Liar, Liar Pants on Fire" (ACL 2017)

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class LiarLabel(Enum):
    """Six-way truthfulness labels from PolitiFact."""
    PANTS_FIRE = 0
    FALSE = 1
    BARELY_TRUE = 2
    HALF_TRUE = 3
    MOSTLY_TRUE = 4
    TRUE = 5
    
    @classmethod
    def from_string(cls, label: str) -> 'LiarLabel':
        """Convert string label to enum."""
        mapping = {
            'pants-fire': cls.PANTS_FIRE,
            'false': cls.FALSE,
            'barely-true': cls.BARELY_TRUE,
            'half-true': cls.HALF_TRUE,
            'mostly-true': cls.MOSTLY_TRUE,
            'true': cls.TRUE
        }
        return mapping.get(label.lower().strip(), cls.HALF_TRUE)
    
    def to_binary(self) -> str:
        """Convert to binary label (Fake/Real)."""
        if self.value <= 2:  # pants-fire, false, barely-true
            return "Fake"
        else:  # half-true, mostly-true, true
            return "Real"
    
    def to_ternary(self) -> str:
        """Convert to ternary label (False/Mixed/True)."""
        if self.value <= 1:  # pants-fire, false
            return "False"
        elif self.value <= 3:  # barely-true, half-true
            return "Mixed"
        else:  # mostly-true, true
            return "True"


@dataclass
class LiarStatement:
    """A single statement from the LIAR dataset."""
    id: str
    label: LiarLabel
    statement: str
    subject: str = ""
    speaker: str = ""
    job_title: str = ""
    state: str = ""
    party: str = ""
    barely_true_count: int = 0
    false_count: int = 0
    half_true_count: int = 0
    mostly_true_count: int = 0
    pants_fire_count: int = 0
    context: str = ""
    
    @property
    def binary_label(self) -> str:
        """Get binary label (Fake/Real)."""
        return self.label.to_binary()
    
    @property
    def ternary_label(self) -> str:
        """Get ternary label (False/Mixed/True)."""
        return self.label.to_ternary()
    
    @property
    def numeric_label(self) -> int:
        """Get numeric label (0-5)."""
        return self.label.value
    
    @property
    def speaker_credit_history(self) -> Dict[str, int]:
        """Get speaker's historical credibility as a dictionary."""
        return {
            'barely_true': self.barely_true_count,
            'false': self.false_count,
            'half_true': self.half_true_count,
            'mostly_true': self.mostly_true_count,
            'pants_fire': self.pants_fire_count
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'label': self.label.name,
            'binary_label': self.binary_label,
            'ternary_label': self.ternary_label,
            'statement': self.statement,
            'subject': self.subject,
            'speaker': self.speaker,
            'job_title': self.job_title,
            'state': self.state,
            'party': self.party,
            'context': self.context,
            'speaker_credit_history': self.speaker_credit_history
        }


class LIARDataset:
    """
    Loader for LIAR benchmark dataset.
    
    The LIAR dataset contains 12,836 short statements labeled with
    six fine-grained truthfulness ratings from PolitiFact.
    
    Files expected:
        - train.tsv (10,269 statements)
        - valid.tsv (1,284 statements)
        - test.tsv (1,283 statements)
    
    Usage:
        dataset = LIARDataset("/path/to/liar_dataset")
        train_data = dataset.load_split("train")
        
        for statement in train_data:
            print(f"{statement.statement} -> {statement.label.name}")
    """
    
    # TSV column indices
    COL_ID = 0
    COL_LABEL = 1
    COL_STATEMENT = 2
    COL_SUBJECT = 3
    COL_SPEAKER = 4
    COL_JOB = 5
    COL_STATE = 6
    COL_PARTY = 7
    COL_BARELY_TRUE = 8
    COL_FALSE = 9
    COL_HALF_TRUE = 10
    COL_MOSTLY_TRUE = 11
    COL_PANTS_FIRE = 12
    COL_CONTEXT = 13
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize LIAR dataset loader.
        
        Args:
            data_dir: Path to directory containing train.tsv, valid.tsv, test.tsv
                     If None, uses default location: syscred/datasets/liar/
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default: relative to this file
            self.data_dir = Path(__file__).parent / "datasets" / "liar"
        
        self._cache: Dict[str, List[LiarStatement]] = {}
        
        print(f"[LIAR] Dataset directory: {self.data_dir}")
    
    def _parse_int_safe(self, value: str) -> int:
        """Safely parse int, returning 0 on failure."""
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return 0
    
    def _parse_row(self, row: List[str]) -> Optional[LiarStatement]:
        """Parse a single TSV row into a LiarStatement."""
        try:
            # Ensure we have enough columns
            if len(row) < 3:
                return None
            
            # Pad row if needed
            while len(row) < 14:
                row.append("")
            
            return LiarStatement(
                id=row[self.COL_ID].strip(),
                label=LiarLabel.from_string(row[self.COL_LABEL]),
                statement=row[self.COL_STATEMENT].strip(),
                subject=row[self.COL_SUBJECT].strip() if len(row) > self.COL_SUBJECT else "",
                speaker=row[self.COL_SPEAKER].strip() if len(row) > self.COL_SPEAKER else "",
                job_title=row[self.COL_JOB].strip() if len(row) > self.COL_JOB else "",
                state=row[self.COL_STATE].strip() if len(row) > self.COL_STATE else "",
                party=row[self.COL_PARTY].strip() if len(row) > self.COL_PARTY else "",
                barely_true_count=self._parse_int_safe(row[self.COL_BARELY_TRUE]) if len(row) > self.COL_BARELY_TRUE else 0,
                false_count=self._parse_int_safe(row[self.COL_FALSE]) if len(row) > self.COL_FALSE else 0,
                half_true_count=self._parse_int_safe(row[self.COL_HALF_TRUE]) if len(row) > self.COL_HALF_TRUE else 0,
                mostly_true_count=self._parse_int_safe(row[self.COL_MOSTLY_TRUE]) if len(row) > self.COL_MOSTLY_TRUE else 0,
                pants_fire_count=self._parse_int_safe(row[self.COL_PANTS_FIRE]) if len(row) > self.COL_PANTS_FIRE else 0,
                context=row[self.COL_CONTEXT].strip() if len(row) > self.COL_CONTEXT else ""
            )
        except Exception as e:
            print(f"[LIAR] Parse error: {e}")
            return None
    
    def load_split(self, split: str = "test") -> List[LiarStatement]:
        """
        Load a dataset split.
        
        Args:
            split: One of 'train', 'valid', 'test'
            
        Returns:
            List of LiarStatement objects
        """
        if split in self._cache:
            return self._cache[split]
        
        file_path = self.data_dir / f"{split}.tsv"
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"LIAR dataset file not found: {file_path}\n"
                f"Download from: https://www.cs.ucsb.edu/~william/data/liar_dataset.zip"
            )
        
        statements = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                stmt = self._parse_row(row)
                if stmt:
                    statements.append(stmt)
        
        self._cache[split] = statements
        print(f"[LIAR] Loaded {len(statements)} statements from {split}.tsv")
        
        return statements
    
    def get_statements(self, split: str = "test") -> List[str]:
        """Get just the statement texts."""
        return [s.statement for s in self.load_split(split)]
    
    def get_labels(self, split: str = "test", label_type: str = "binary") -> List[str]:
        """
        Get labels for a split.
        
        Args:
            split: Dataset split
            label_type: 'binary' (Fake/Real), 'ternary' (False/Mixed/True), 
                       'six' (original 6-way), 'numeric' (0-5)
        """
        statements = self.load_split(split)
        
        if label_type == "binary":
            return [s.binary_label for s in statements]
        elif label_type == "ternary":
            return [s.ternary_label for s in statements]
        elif label_type == "numeric":
            return [s.numeric_label for s in statements]
        else:  # six / original
            return [s.label.name for s in statements]
    
    def get_label_distribution(self, split: str = "test") -> Dict[str, int]:
        """Get count of each label in a split."""
        statements = self.load_split(split)
        distribution = {}
        
        for stmt in statements:
            label = stmt.label.name
            distribution[label] = distribution.get(label, 0) + 1
        
        return distribution
    
    def get_sample(self, split: str = "test", n: int = 10) -> List[LiarStatement]:
        """Get a random sample of statements."""
        import random
        statements = self.load_split(split)
        return random.sample(statements, min(n, len(statements)))
    
    def get_by_party(self, split: str, party: str) -> List[LiarStatement]:
        """Filter statements by political party."""
        statements = self.load_split(split)
        return [s for s in statements if s.party.lower() == party.lower()]
    
    def get_by_speaker(self, split: str, speaker: str) -> List[LiarStatement]:
        """Filter statements by speaker name."""
        statements = self.load_split(split)
        return [s for s in statements if speaker.lower() in s.speaker.lower()]
    
    def iter_batches(self, split: str, batch_size: int = 32):
        """Iterate over statements in batches."""
        statements = self.load_split(split)
        
        for i in range(0, len(statements), batch_size):
            yield statements[i:i + batch_size]
    
    def stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        stats = {}
        
        for split in ['train', 'valid', 'test']:
            try:
                statements = self.load_split(split)
                stats[split] = {
                    'count': len(statements),
                    'label_distribution': self.get_label_distribution(split),
                    'unique_speakers': len(set(s.speaker for s in statements)),
                    'unique_parties': list(set(s.party for s in statements if s.party))
                }
            except FileNotFoundError:
                stats[split] = {'error': 'File not found'}
        
        return stats


# Convenience function
def load_liar(split: str = "test", data_dir: Optional[str] = None) -> List[LiarStatement]:
    """Quick loader for LIAR dataset."""
    dataset = LIARDataset(data_dir)
    return dataset.load_split(split)


if __name__ == "__main__":
    print("=" * 60)
    print("LIAR Dataset Loader - Test")
    print("=" * 60)
    
    # Test with default path
    try:
        dataset = LIARDataset()
        
        print("\n📊 Dataset Statistics:")
        stats = dataset.stats()
        for split, info in stats.items():
            print(f"\n{split.upper()}:")
            if 'error' in info:
                print(f"  ❌ {info['error']}")
            else:
                print(f"  Total: {info['count']}")
                print(f"  Speakers: {info['unique_speakers']}")
                print(f"  Parties: {info['unique_parties']}")
                print(f"  Labels: {info['label_distribution']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTo use this module, download the LIAR dataset:")
        print("  wget https://www.cs.ucsb.edu/~william/data/liar_dataset.zip")
        print("  unzip liar_dataset.zip -d src/syscred/datasets/liar/")
