#!/usr/bin/env python3
"""
Standalone evaluation script that processes a transcript without the Streamlit UI.
Usage: python run_evaluation.py [n_sentences] [n_overlap] [survey_path]

Examples:
    python run_evaluation.py                    # Uses defaults: n_sentences=10, n_overlap=2
    python run_evaluation.py 15                 # Uses n_sentences=15, n_overlap=2
    python run_evaluation.py 15 3               # Uses n_sentences=15, n_overlap=3
    python run_evaluation.py 15 3 "C:\\path\\to\\survey.xlsx"   # Uses custom survey file
"""

import sys
import os
import json
import shutil
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the modules but we'll override their config values
import app.config
from app.survey import process_survey_excel
from app.audio import chunk_transcription_by_sentences
from app.main_workflow import prepare_survey, process_single_chunk
from app.evaluation import evaluate_ai_answers, summarize_all_chunks

def run_evaluation(transcript_path, survey_path, n_sentences=10, n_overlap=2):
    """
    Run the complete evaluation pipeline on a transcript.
    
    Args:
        transcript_path: Path to the transcript text file
        survey_path: Full path to the survey Excel file
        n_sentences: Number of sentences per chunk
        n_overlap: Number of overlapping sentences between chunks
    """
    # Override the config values for this run
    app.config.n_sentences = n_sentences
    app.config.n_overlap = n_overlap
    
    print(f"🚀 Starting evaluation with parameters:")
    print(f"   - Transcript: {transcript_path}")
    print(f"   - Survey: {survey_path}")
    print(f"   - Sentences per chunk: {n_sentences}")
    print(f"   - Overlap sentences: {n_overlap}")
    print()
    
    # Copy survey file to data/surveys directory if it's not already there
    survey_filename = os.path.basename(survey_path)
    survey_name = os.path.splitext(survey_filename)[0]
    target_path = os.path.join("data", "surveys", survey_filename)
    
    if survey_path != target_path:
        print(f"📂 Copying survey file to data/surveys/...")
        os.makedirs("data/surveys", exist_ok=True)
        shutil.copy2(survey_path, target_path)
        print(f"✅ Survey copied to {target_path}")
    
    # Step 1: Prepare the survey
    print("\n📋 Step 1: Preparing survey...")
    survey_data, df = prepare_survey(survey_name)
    if not survey_data:
        print("❌ Failed to prepare survey")
        return
    print(f"✅ Survey loaded: {len(df)} questions")
    
    # Step 2: Load the transcript
    print("\n📄 Step 2: Loading transcript...")
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        print(f"✅ Transcript loaded: {len(transcript)} characters")
    except Exception as e:
        print(f"❌ Failed to load transcript: {e}")
        return
    
    # Step 3: Chunk the transcript
    print(f"\n✂️  Step 3: Chunking transcript (n_sentences={n_sentences}, n_overlap={n_overlap})...")
    chunks = chunk_transcription_by_sentences(transcript, n_sentences, n_overlap)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Step 4: Clear previous files
    print("\n🗑️  Clearing previous evaluation files...")
    if os.path.exists("data/answers.json"):
        os.remove("data/answers.json")
        print("   - Removed data/answers.json")
    if os.path.exists("evaluation/log_chunks.jsonl"):
        os.remove("evaluation/log_chunks.jsonl") 
        print("   - Removed evaluation/log_chunks.jsonl")
    
    # Step 5: Process each chunk
    print("\n🤖 Step 4: Processing chunks through AI...")
    for i, chunk in enumerate(chunks):
        print(f"\n   Processing chunk {i+1}/{len(chunks)}...")
        df = process_single_chunk(
            chunk_text=chunk,
            chunk_number=i + 1,
            total_chunks=len(chunks),
            df=df,
            survey_data=survey_data
        )
        print(f"   ✅ Chunk {i+1} completed")
    
    # Step 6: Summarize chunks performance
    print("\n📊 Step 5: Summarizing chunk performance...")
    try:
        summarize_all_chunks(n_sentences, n_overlap, len(chunks))
        print("✅ Chunk performance summarized")
    except Exception as e:
        print(f"⚠️  Warning: Failed to summarize chunk performance: {e}")
        print("   Continuing with evaluation...")
    
    # Step 7: Evaluate AI answers
    print("\n🎯 Step 6: Evaluating AI answers...")
    evaluate_ai_answers(n_sentences, n_overlap)
    print("✅ Evaluation completed")
    
    # Step 8: Display results
    print("\n📈 Results:")
    if os.path.exists("evaluation/evaluation_results.jsonl"):
        with open("evaluation/evaluation_results.jsonl", "r") as f:
            # Get the last line (most recent result)
            lines = f.readlines()
            if lines:
                last_result = json.loads(lines[-1])
                print(f"   - Total chunks: {last_result.get('total_chunks', 'N/A')}")
                print(f"   - AI Right: {last_result.get('AI_right', 'N/A')}")
                print(f"   - AI Wrong: {last_result.get('AI_wrong', 'N/A')}")
                print(f"   - Accuracy: {last_result.get('Accuracy', 'N/A')}")
                print(f"   - RTT trimmed mean: {last_result.get('rtt_trimmed_mean', 'N/A')}s")
                print(f"   - Total retries: {last_result.get('total_retries', 'N/A')}")
    
    print("\n✅ Evaluation complete! Check 'evaluation/evaluation_results.jsonl' for full results.")

def main():
    # Default values
    transcript_path = r"C:\LocalFiles\surveytool\data\recordings\transcripts\recording_20250719_2342.txt"
    survey_path = r"C:\LocalFiles\surveytool\test_files\survey_2_evalution.xlsx"
    
    # Parse command line arguments
    if len(sys.argv) >= 2:
        n_sentences = int(sys.argv[1])
    else:
        n_sentences = 10  # Default
    
    if len(sys.argv) >= 3:
        n_overlap = int(sys.argv[2])
    else:
        n_overlap = 2  # Default
    
    if len(sys.argv) >= 4:
        survey_path = sys.argv[3]
    
    # Run the evaluation
    run_evaluation(transcript_path, survey_path, n_sentences, n_overlap)

if __name__ == "__main__":
    main() 