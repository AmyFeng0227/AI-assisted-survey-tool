import json
from datetime import datetime
from openai import OpenAI
from .config import client, model

def get_ai_response(prompt):
    """
    Get response from OpenAI API.
    
    Args:
        prompt (str): The prompt to send to the API
        
    Returns:
        str: The API response text
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content, response.usage.total_tokens

# === Answer processing ===

def process_ai_response(response_text, prompt):
    """
    Process AI's response and convert to proper format.
    
    Args:
        response_text (str): Raw response from AI
        prompt (str): Original prompt used to generate response
        
    Returns:
        tuple: (new_answers, retry_count) or None if failed
    """
    retry = 0
    max_retries = 3
    current_response = response_text
    while retry < max_retries:
        try:
            new_answers = json.loads(current_response)
            print(f"New answers: {new_answers}")
            return new_answers, retry
        except json.JSONDecodeError as e:
            if str(e) == "Expecting value: line 1 column 1 (char 0)":
                print(f"Invalid JSON response, retrying API call... (attempt {retry+1})")
                retry += 1
                if retry < max_retries:
                    current_response, _ = get_ai_response(prompt)
                else:
                    print(f"Error processing AI response after {max_retries} attempts: {e}")
                    return None
            else:
                print(f"Error processing AI response: {e}")
                return None



def update_answers_file(new_answers, source):
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
            if source == "ai":
                certainty = item["certainty"]
            else:
                certainty = "high"
            answers[qid] = {
                "answer": item["answer"],
                "certainty": certainty,
                "text field": item.get("text field", ""),
                "source": source,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Save updated answers
        with open("data/answers.json", "w") as f:
            json.dump(answers, f, indent=2)
            
    except Exception as e:
        print(f"Error updating answers file: {e}")

def update_answers_dataframe(df, new_answers, source):
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
        qid = float(answer["question_id"]) 
        if source == "ai":
            certainty = answer["certainty"]
        else:
            certainty = "high"
        if qid in df.index:
            df.at[qid, 'answer'] = answer["answer"]
            df.at[qid, 'certainty'] = certainty
            df.at[qid, 'text_field'] = answer.get("text field", "")
            df.at[qid, 'source'] = source
            df.at[qid, 'last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return df