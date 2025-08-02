from .config import client, model
from .survey import process_survey_excel, format_survey_questions
from .prompt import create_prompt_without_answers, create_prompt_with_answers
from .answer import process_ai_response, update_answers_file, update_answers_dataframe, get_ai_response
from .evaluation import log_chunk
import json
import os
import time

def prepare_survey(excel_name):
    """
    Prepare a survey for use by processing Excel file and formatting questions for prompts.
    This is the main entry point for survey preparation.
    
    Args:
        excel_name (str): Name of the Excel file (without extension)
        
    Returns:
        tuple: (raw survey data as list of question objects, DataFrame ready for answers)
    """
    try:
        # Step 1: Process Excel into structured formats
        survey_data, df = process_survey_excel(excel_name)
        if not survey_data:
            print("Failed to process Excel file")
            return None, None
        
        print(f"Successfully prepared survey from {excel_name}.xlsx")
        return survey_data, df
        
    except Exception as e:
        print(f"Error preparing survey: {e}")
        return None, None


def process_single_chunk(chunk_text, chunk_number, total_chunks, df, survey_data):
    """
    Process a single chunk of transcript text.
    
    Args:
        chunk_text (str): The transcript chunk to process
        chunk_number (int): Current chunk number (1-indexed)
        total_chunks (int): Total number of chunks
        df (pd.DataFrame): DataFrame with survey questions and answer columns
        survey_data: Survey data for formatting questions
        
    Returns:
        pd.DataFrame: Updated DataFrame with new answers from this chunk
    """
    # Import here to get the current dynamic values
    from .config import n_sentences, n_overlap

    print(f"\n📄 Processing chunk {chunk_number}/{total_chunks}")


    # Format survey questions
    survey_questions = format_survey_questions(survey_data)
    if not survey_questions:
        print("Failed to format questions")
        return df
    
    # Check for existing answers and create prompt for this chunk
    if os.path.exists("data/answers.json"):
        # Get previous answers as string
        with open("data/answers.json", "r") as f:
            previous_answers = json.load(f)
        previous_answers_str = ""
        for qid, answer_data in previous_answers.items():
            if answer_data['source'] == "ai":
                previous_answers_str += f"{qid}: {answer_data['answer']} (certainty: {answer_data['certainty']})"
                if answer_data['text field']:
                    previous_answers_str += f" - \"{answer_data['text field']}\"\n"

        # Generate follow-up prompt for this chunk
        prompt = create_prompt_with_answers(survey_questions, previous_answers_str, chunk_text)
    else:
        # Generate initial prompt for this chunk
        prompt = create_prompt_without_answers(survey_questions, chunk_text)
    
    # Get AI response for this chunk
    retry = 0
    ai_start = time.time()
    response_text, total_tokens = get_ai_response(prompt)
    ai_duration = time.time() - ai_start
    print(f"   🤖 Chunk {chunk_number} AI response received in {ai_duration:.2f}s")
    
    # Process response and update tracking for this chunk
    result = process_ai_response(response_text, prompt)
    if result is not None:
        new_answers, retry = result
        if new_answers:
            update_answers_file(new_answers, "ai")
            df = update_answers_dataframe(df, new_answers, "ai")
            print(f"   ✅ Chunk {chunk_number} added {len(new_answers)} new/updated answers")
        else:
            print(f"   ℹ️ Chunk {chunk_number} produced no new answers")
    else:
        print(f"   ❌ Chunk {chunk_number} failed to process after retries")
        new_answers = []
        retry = 3  # Max retries reached
    
    run_id = f"S{n_sentences}_O{n_overlap}_{chunk_number}_{total_chunks}"

    row = {
        "run_id": run_id,
        "rtt": round(ai_duration, 1),
        "retry": retry}
    
    # Only add total_tokens if we have it
    if total_tokens is not None:
        row["total_tokens"] = total_tokens
    
    log_chunk(row)

    return df

# Example code to run the functions
# survey_questions, df = prepare_survey("survey_1")
# df = process_recording("recording3", survey_questions, df)