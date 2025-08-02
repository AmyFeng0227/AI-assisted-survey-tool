import json
import pandas as pd
from collections import defaultdict

def load_evaluation_data(filename):
    """Load evaluation data from a JSONL file."""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def summarize_evaluation_results():
    """Average evaluation results across all three rounds."""
    
    # Load data from all three rounds
    round1_data = load_evaluation_data('evaluation/evaluation_results_round1.jsonl')
    round2_data = load_evaluation_data('evaluation/evaluation_results_round2.jsonl')
    round3_data = load_evaluation_data('evaluation/evaluation_results_round3.jsonl')
    
    # Group data by configuration (n_sentences, n_overlap)
    grouped_data = defaultdict(list)
    
    for data_list in [round1_data, round2_data, round3_data]:
        for entry in data_list:
            key = (entry['n_sentences'], entry['n_overlap'])
            grouped_data[key].append(entry)
    
    # Calculate averages for each configuration
    summary_results = []
    
    for (n_sentences, n_overlap), entries in grouped_data.items():
        if len(entries) != 3:  # Should have exactly 3 entries (one from each round)
            print(f"Warning: Configuration ({n_sentences}, {n_overlap}) has {len(entries)} entries instead of 3")
            continue
        
        # Calculate averages
        avg_result = {
            'n_sentences': n_sentences,
            'n_overlap': n_overlap,
            'total_chunks': round(sum(e['total_chunks'] for e in entries) / 3, 2),
            'rtt_trimmed_mean': round(sum(e['rtt_trimmed_mean'] for e in entries) / 3, 2),
            'rtt_trimmed_mean_times_total_chunks': round(sum(e['rtt_trimmed_mean_times_total_chunks'] for e in entries) / 3, 2),
            'total_retries': round(sum(e['total_retries'] for e in entries) / 3, 2),
            'total_tokens_sum': round(sum(e['total_tokens_sum'] for e in entries) / 3, 2),
            'TP_TN': round(sum(e['TP_TN'] for e in entries) / 3, 2),
            'FP_W': round(sum(e['FP_W'] for e in entries) / 3, 2),
            'FP_U': round(sum(e['FP_U'] for e in entries) / 3, 2),
            'FN': round(sum(e['FN'] for e in entries) / 3, 2),
            'Accuracy': round(sum(e['Accuracy'] for e in entries) / 3, 2)
        }
        
        summary_results.append(avg_result)
    
    # Sort by n_sentences (descending) then by n_overlap
    summary_results.sort(key=lambda x: (-x['n_sentences'], x['n_overlap']))
    
    # Write summary to file
    with open('evaluation/evaluation_results_summary.jsonl', 'w') as f:
        for result in summary_results:
            f.write(json.dumps(result) + '\n')
    
    print(f"Summary created with {len(summary_results)} configurations")
    print("Summary saved to: evaluation/evaluation_results_summary.jsonl")
    
    # Also create a more readable CSV version
    df = pd.DataFrame(summary_results)
    df.to_csv('evaluation/evaluation_results_summary.csv', index=False)
    print("CSV version saved to: evaluation/evaluation_results_summary.csv")
    
    return summary_results

if __name__ == "__main__":
    summarize_evaluation_results() 