#!/usr/bin/env python3
"""
TREC AP88-90 to JSONL Converter
Converts TREC AP88-90 gz files to JSONL format for IR engine.
"""

import os
import gzip
import json
import glob
from pathlib import Path

def extract_ap_documents(gz_path):
    """Extract documents from AP gz file."""
    documents = []
    doc_id = None
    doc_text = []
    in_text = False
    
    with gzip.open(gz_path, 'rt', encoding='latin-1') as f:
        for line in f:
            line = line.strip()
            
            if line.startswith('<DOC>'):
                doc_id = None
                doc_text = []
                in_text = False
            elif line.startswith('<DOCNO>'):
                doc_id = line.replace('<DOCNO>', '').replace('</DOCNO>', '').strip()
            elif line == '<TEXT>':
                in_text = True
            elif line == '</TEXT>':
                in_text = False
            elif line.startswith('</DOC>'):
                if doc_id and doc_text:
                    documents.append({
                        'id': doc_id,
                        'contents': ' '.join(doc_text),
                        'title': doc_text[0][:100] if doc_text else ''
                    })
            elif in_text and line:
                doc_text.append(line)
    
    return documents

def convert_trec_to_jsonl(trec_dir, output_path, max_docs=None):
    """Convert all TREC AP88-90 files to JSONL."""
    gz_files = sorted(glob.glob(os.path.join(trec_dir, '*.gz')))
    print(f"Found {len(gz_files)} TREC AP files")
    
    total_docs = 0
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for gz_file in gz_files:
            print(f"Processing: {os.path.basename(gz_file)}")
            docs = extract_ap_documents(gz_file)
            
            for doc in docs:
                outfile.write(json.dumps(doc, ensure_ascii=False) + '\n')
                total_docs += 1
                
                if max_docs and total_docs >= max_docs:
                    print(f"Reached max docs: {max_docs}")
                    return total_docs
    
    print(f"Total documents: {total_docs}")
    return total_docs

if __name__ == '__main__':
    import sys
    
    # Default paths
    trec_dir = '/app/trec_ap88_90'
    output_path = '/app/trec_corpus.jsonl'
    
    # Override with command line args
    if len(sys.argv) > 1:
        trec_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print(f"Converting TREC files from {trec_dir}")
    print(f"Output: {output_path}")
    
    count = convert_trec_to_jsonl(trec_dir, output_path)
    print(f"Done! Converted {count} documents")
