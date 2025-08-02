#!/usr/bin/env python3
"""
Batch evaluation script to run all parameter combinations automatically.
"""

import subprocess
import sys
import time

# Parameter combinations
n_sentences_list = [20, 16, 12, 8, 4]
n_overlap_list = [0, 2, 4]

def run_batch_evaluation():
    # Calculate total evaluations excluding skipped ones
    total_evaluations = 0
    for n_sentences in n_sentences_list:
        for n_overlap in n_overlap_list:
            if n_sentences != n_overlap:  # Count only non-skipped evaluations
                total_evaluations += 1
    
    current_evaluation = 0
    
    print(f"🚀 Starting batch evaluation with {total_evaluations} parameter combinations")
    print("=" * 60)
    
    for n_sentences in n_sentences_list:
        for n_overlap in n_overlap_list:
            # Skip when n_sentences equals n_overlap
            if n_sentences == n_overlap:
                print(f"\n⏭️  Skipping: n_sentences={n_sentences}, n_overlap={n_overlap} (equal values)")
                continue
                
            current_evaluation += 1
            print(f"\n📊 Evaluation {current_evaluation}/{total_evaluations}: n_sentences={n_sentences}, n_overlap={n_overlap}")
            print("-" * 40)
            
            # Run the evaluation
            cmd = [sys.executable, "run_evaluation.py", str(n_sentences), str(n_overlap)]
            try:
                subprocess.run(cmd, check=True)
                print(f"✅ Evaluation {current_evaluation} completed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Evaluation {current_evaluation} failed with error: {e}")
            
            # Small delay between evaluations
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 Batch evaluation completed!")
    print("📈 Check 'evaluation/evaluation_results.jsonl' for all results")

if __name__ == "__main__":
    run_batch_evaluation() 