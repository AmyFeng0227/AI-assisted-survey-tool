#!/usr/bin/env python3
"""Debug script to check evaluation files"""

import json
import os

def check_file(filepath, name):
    print(f"\n=== {name} ===")
    if not os.path.exists(filepath):
        print(f"File does not exist: {filepath}")
        return
    
    print(f"File exists: {filepath}")
    print(f"File size: {os.path.getsize(filepath)} bytes")
    
    if filepath.endswith('.jsonl'):
        print("\nContents (JSONL):")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                line_num = 0
                for line in f:
                    line_num += 1
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            print(f"Line {line_num}: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError as e:
                            print(f"Line {line_num} ERROR: {e}")
                            print(f"Raw line: {repr(line)}")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    elif filepath.endswith('.json'):
        print("\nContents (JSON):")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(json.dumps(data, indent=2)[:500] + "...")
        except Exception as e:
            print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_file("evaluation/log_chunks.jsonl", "Log Chunks")
    check_file("evaluation/evaluation_results.jsonl", "Evaluation Results") 
    check_file("data/answers.json", "Answers") 