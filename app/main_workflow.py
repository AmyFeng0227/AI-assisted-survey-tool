from .survey import process_survey_excel, format_survey_questions
from .audio import process_audio_file
from .prompt import create_prompt_without_answers, create_prompt_with_answers
from .answer import process_ai_response, update_answers_file, update_answers_dataframe, get_ai_response
import json
import os
from datetime import datetime

def prepare_survey(excel_name):
    """
    Prepare a survey for use by processing Excel file and formatting questions for prompts.
    This is the main entry point for survey preparation.
    
    Args:
        excel_name (str): Name of the Excel file (without extension)
        
    Returns:
        tuple: (formatted questions string for prompts, DataFrame ready for answers)
    """
    try:
        # Step 1: Process Excel into structured formats
        survey_data, df = process_survey_excel(excel_name)
        if not survey_data:
            print("Failed to process Excel file")
            return None, None
            
        # Step 2: Format questions for prompts
        survey_questions = format_survey_questions(survey_data)
        if not survey_questions:
            print("Failed to format questions")
            return None, None
        
        print(f"Successfully prepared survey from {excel_name}.xlsx")
        return survey_questions, df
        
    except Exception as e:
        print(f"Error preparing survey: {e}")
        return None, None


def process_recording(recording_name, survey_questions, df):
    """
    Process a single recording using the prepared survey.
    
    Args:
        recording_name (str): Name of the recording file (without extension)
        survey_questions (str): Formatted survey questions for prompts
        df (pd.DataFrame): DataFrame with survey questions and answer columns
        
    Returns:
        pd.DataFrame: Updated DataFrame with new answers
    """
    # Process recording
    transcript = process_audio_file(recording_name)
    if not transcript:
        return df
    
    # Check if answers.json exists
    if os.path.exists("data/answers.json"):
        # Get previous answers as string
        print("answers.json found, generating follow-up prompt")
        with open("data/answers.json", "r") as f:
            previous_answers = json.load(f)
        previous_answers_str = "Previous answers (for reference): \n"
        for qid, answer_data in previous_answers.items():
            previous_answers_str += f"{qid}: {answer_data['answer']} (certainty: {answer_data['certainty']})"
            if answer_data['text field']:
                previous_answers_str += f" - \"{answer_data['text field']}\"\n"
            else:
                previous_answers_str += "\n"
        
        # Generate follow-up prompt and get AI response
        prompt = create_prompt_with_answers(survey_questions, previous_answers_str, transcript)
    else:
        # Generate initial prompt and get AI response
        print("answers.json not found, generating initial prompt")
        prompt = create_prompt_without_answers(survey_questions, transcript)
    
    response_text = get_ai_response(prompt)
    
    # Process response and update tracking
    new_answers = process_ai_response(response_text, prompt)
    if new_answers:
        update_answers_file(new_answers)
        df = update_answers_dataframe(df, new_answers)
        
        # Save current state of DataFrame with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f"survey_answers_tracking_{timestamp}.csv")
    
    return df

# Example code to run the functions
# survey_questions, df = prepare_survey("survey_1")
# df = process_recording("recording3", survey_questions, df)