import os
import json
import statistics

def log_chunk(row: dict):
    file_path = "evaluation/log_chunks.jsonl"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Append the row to the JSONL file
    with open(file_path, "a", encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()  # Ensure data is written immediately

def summarize_all_chunks(n_sentences, n_overlap, total_chunks):
    """
    Calculate trimmed mean of rtt, trimmed mean * total_chunks, trimmed mean of retry,
    and sum of total_tokens from log_chunks.jsonl, and save to evaluation_results.jsonl.
    """
    file_path = "evaluation/log_chunks.jsonl"
    rtts = []
    retries = []
    total_tokens = []
    # Read all rows
    if os.path.exists(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            line_num = 0
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    row = json.loads(line)
                    # Only include rows for this total_chunks run
                    if row.get("run_id", "").startswith(f"S{n_sentences}_O{n_overlap}"):
                        rtts.append(row.get("rtt", 0))
                        retries.append(row.get("retry", 0))
                        # total_tokens may not be present in all rows
                        if "total_tokens" in row:
                            total_tokens.append(row["total_tokens"])
                except json.JSONDecodeError as e:
                    print(f"Warning: Line {line_num} - Skipping malformed JSON: {repr(line[:50])}... Error: {e}")
                    continue
    else:
        print(f"Warning: Log file {file_path} does not exist")
    if not rtts:
        print(f"Warning: No matching data found for S{n_sentences}_O{n_overlap} in log file")
        return  # nothing to summarize
    
    print(f"Found {len(rtts)} matching chunks for S{n_sentences}_O{n_overlap}")

    # Calculate trimmed mean (remove top and bottom 10%)
    def trimmed_mean(data, proportion=0.1):
        if not data:
            return 0
        n = len(data)
        trim = int(n * proportion)
        if n < 2 * trim + 1:
            # Not enough data to trim, just mean
            return statistics.mean(data)
        data_sorted = sorted(data)
        trimmed = data_sorted[trim: n - trim]
        return statistics.mean(trimmed)

    rtt_trimmed_mean = trimmed_mean(rtts)
    total_retries = sum(retries)
    total_tokens_sum = sum(total_tokens) if total_tokens else None

    result = { 
        "n_sentences": n_sentences,
        "n_overlap": n_overlap,
        "total_chunks": total_chunks,
        "rtt_trimmed_mean": round(rtt_trimmed_mean, 1),
        "rtt_trimmed_mean_times_total_chunks": round(rtt_trimmed_mean * total_chunks, 1),
        "total_retries": total_retries,
        "total_tokens_sum": total_tokens_sum
    }
    result_path = "evaluation/evaluation_results.jsonl"
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, "a") as f:
        f.write(json.dumps(result) + "\n")


def evaluate_ai_answers(n_sentences, n_overlap):
    # Inputs
    ai_path = "data/answers.json"
    human_path = "evaluation/answers_human.json"
    questions_ignore = ["7", "8", "13"]
    questions_blank = ["9", "19", "20", "24", "25"]
    qids_to_check = ["1", "2", "3", "4", "5", "6", "10", "11", "12", "14", "15", "16", "17", "18", "21", "22", "23"]
    
    with open(ai_path) as f:
        ai = json.load(f)
    with open(human_path, encoding='utf-8') as f:
        human = json.load(f)

    AI_right = 0
    AI_wrong = 0

    #human blank answers 
    for qid in questions_blank:
        ai_answer = ai.get(qid, {}).get("answer")
        if ai_answer is not None:
            AI_wrong += 1
        else:
            AI_right += 1

    for qid in qids_to_check:
        ai_answer   = ai.get(qid, {}).get("answer")
        human_answer = human.get(qid, {}).get("answer")
        # If AI answer matches human answer, then AI_right +=1, otherwise AI_wrong +=1
        if ai_answer is not None and str(ai_answer).strip() == str(human_answer).strip():
            AI_right += 1
        else:
            AI_wrong += 1

    # Read existing results to find the most recent row for this configuration
    result_path = "evaluation/evaluation_results.jsonl"
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    
    existing_data = None
    all_rows = []
    
    # Read all existing rows
    if os.path.exists(result_path):
        with open(result_path, "r") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    all_rows.append(row)
    
    # Find the most recent row with matching n_sentences and n_overlap
    print(f"Looking for existing row with S{n_sentences}_O{n_overlap} without AI data...")
    for i in range(len(all_rows) - 1, -1, -1):  # Search backwards
        row = all_rows[i]
        if (row.get("n_sentences") == n_sentences and 
            row.get("n_overlap") == n_overlap and
            "AI_right" not in row):  # Row doesn't have AI accuracy data yet
            print(f"Found matching row at index {i}")
            existing_data = row
            all_rows[i] = row  # Will be updated below
            break
    
    if existing_data:
        # Merge AI accuracy data into existing row
        existing_data.update({
            "AI_right": AI_right,
            "AI_wrong": AI_wrong,
            "Accuracy": round(AI_right / 22, 2)
        })
        
        # Rewrite the entire file with updated data
        with open(result_path, "w") as f:
            for row in all_rows:
                f.write(json.dumps(row) + "\n")
    else:
        # No existing row found, create a new one
        print(f"Creating new evaluation row for S{n_sentences}_O{n_overlap}")
        result = {
            "n_sentences": n_sentences,
            "n_overlap": n_overlap,
            "AI_right": AI_right,
            "AI_wrong": AI_wrong,
            "Accuracy": round(AI_right / 22, 2)
        }
        with open(result_path, "a") as f:
            f.write(json.dumps(result) + "\n")