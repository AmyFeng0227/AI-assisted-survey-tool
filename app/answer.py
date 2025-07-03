import json
from datetime import datetime

# === Answer processing ===

def process_ai_response(response_text):
    """
    Process AI's response and convert to proper format.
    
    Args:
        response_text (str): Raw response from AI
        
    Returns:
        list: Processed answers
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error processing AI response: {e}")
        return None



def update_answers_file(new_answers):
    """
    Create or update the answers.json file with new answers.
    
    Args:
        new_answers (list): List of new answers from AI
    """
    try:
        # Load existing answers or create new dict
        try:
            with open("data/answers.json", "r") as f:
                answers = json.load(f)
        except FileNotFoundError:
            answers = {}
        
        # Update with new answers
        for item in new_answers:
            qid = item["question_id"]
            answers[qid] = {
                "answer": item["answer"],
                "certainty": item["certainty"],
                "text field": item.get("text field", ""),
                "source": "ai",
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Save updated answers
        with open("data/answers.json", "w") as f:
            json.dump(answers, f, indent=2)
            
    except Exception as e:
        print(f"Error updating answers file: {e}")

def update_answers_dataframe(df, new_answers):
    """
    Update tracking DataFrame with new answers.
    
    Args:
        df (pd.DataFrame): Existing DataFrame with survey questions and answer columns
        new_answers (list): List of new answers
        
    Returns:
        pd.DataFrame: Updated DataFrame
    """
    # Update the DataFrame with new answers
    for answer in new_answers:
        qid = float(answer["question_id"])  # Convert to float since QuestionID is float
        if qid in df.index:
            df.at[qid, 'answer'] = answer["answer"]
            df.at[qid, 'certainty'] = answer["certainty"]
            df.at[qid, 'text_field'] = answer.get("text field", "")
            df.at[qid, 'source'] = "ai"
            df.at[qid, 'last_updated'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    return df