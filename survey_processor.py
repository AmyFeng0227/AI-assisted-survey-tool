from dotenv import load_dotenv
import os
import pandas as pd
import json
from datetime import datetime
from openai import OpenAI
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_survey"))

# === Survey Processing ===
def process_survey_excel(excel_name):
    """
    Process Excel survey file into structured data formats.
    
    Args:
        excel_name (str): Name of the Excel file (without extension)
        
    Returns:
        tuple: (list of survey questions in JSON format, DataFrame with survey and answer columns)
    """
    try:
        # Read Excel file
        df = pd.read_excel(excel_name+".xlsx", engine="openpyxl")
        
        # Create JSON format
        survey = []
        for _, row in df.iterrows():
            id = str(row["QuestionID"]).strip()
            question = str(row["Question"]).strip()
            q_type = str(row["Type"]).strip().lower()
            field = str(row["Field"]).strip()
            options = str(row["Options"]).strip() if pd.notna(row["Options"]) else ""
            
            q_obj = {
                "field": field,
                "id": id,
                "question": question,
                "type": q_type,
                "options": [opt.strip() for opt in options.split(";")] if options else [""]
            }
            
            survey.append(q_obj)
        
        # Save survey to local JSON file
        output_path = Path(excel_name).with_suffix('.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(survey, f, indent=2, ensure_ascii=False)
        
        # Prepare DataFrame
        df.set_index('QuestionID', inplace=True)
        
        # Add answer-related columns
        answer_columns = ['answer', 'certainty', 'text_field', 'source', 'last_updated']
        for col in answer_columns:
            df[col] = None
            
        return survey, df
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        return None, None

def format_survey_questions(survey_data):
    """
    Format survey questions for use in prompts.
    
    Args:
        survey_data (list): List of survey questions
        
    Returns:
        str: Formatted survey questions
    """
    questions_text = ""
    for question in survey_data:
        questions_text += f"{question['id']}: [{question['field']}] {question['question']} ({question['type']}"
        if question['options'] != ['']:
            questions_text += f": {', '.join(question['options'])})\n"
        else:
            questions_text += ")\n"
    
    return questions_text

def prepare_survey(excel_name):
    """
    Prepare a survey for use by processing Excel file and formatting questions.
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

# === Recording Processing ===
def process_audio_file(file_name):
    """
    Process a single audio file and return its transcription.
    Also saves the transcription to a text file.
    
    Args:
        file_name (str): Name of the audio file (without extension)
        
    Returns:
        str: Transcribed text
    """
    try:
        with open(file_name+".m4a", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file
            )
            # Save transcription to text file
            txt_path = Path(file_name).with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(transcription.text)

            return transcription.text
    except Exception as e:
        print(f"Error processing audio file {file_name}.m4a: {e}")
        return None

# === Answer Processing ===
def create_prompt_without_answers(survey_questions, transcript):
    """
    Create the initial prompt for the first transcript.
    
    Args:
        survey_questions (str): Formatted survey questions
        transcript (str): Interview transcript
        
    Returns:
        str: Complete prompt
    """
    return f"""Based on the following interview transcript between one social worker and one youth participant interested in participating in leaving care program, please fill out this survey. For each question, provide:
1. Answer: Base the answer according to the guidance provided in the parentheses. For text questions, try to cover all the relavant information for this question.
2. Certainty (low, medium, high)
3. Text field: All single/multiple choice questions must have a concise text reasoning, but make sure you cover all the relevant information related to the question. If not choice-based, leave blank.

Notes:
Output only for the questions that are clearly addressed in the transcript. 
Do not make up information, follow the transcript.
Format your response as a JSON array, nothing else.

SURVEY QUESTIONS:
{survey_questions}

TRANSCRIPT:
{transcript}

output example:
[
  {{
    "question_id": "5",
    "answer": "yes",
    "certainty": "high",
    "text field": "support in finding an apartment is urgent. Prefer first-hand contract"
  }},
  {{
    "question_id": "10",
    "answer": "lonely and depressed, having trouble to sleep and hard to find time for friends",
    "certainty": "medium",
    "text field": ""
  }}
]
"""

def create_prompt_with_answers(survey_questions, previous_answers, transcript):
    """
    Create prompt for subsequent transcripts that includes previous answers.
    
    Args:
        survey_questions (str): Formatted survey questions
        previous_answers (str): Previous answers formatted as string
        transcript (str): New interview transcript
        
    Returns:
        str: Complete prompt
    """
    return f"""The following transcript is an interview between a social worker and a youth participant interested in participating in the leaving care program. You are provided with the survey (see SURVEY QUESTIONS) which have been partially answered before (see PREVIOUS ANSWERS) based on another transcript. You will update the answers to the survey based on the provided transcripts. 

Here is the structure to answer a question:
1. Answer: Base the answer according to the guidance provided in the parentheses. For text questions, try to cover all the relavant information for this question.
2. Certainty (low, medium, high)
3. Text field: All single/multiple choice questions must have a concise text reasoning, but make sure you cover all the relevant information related to the question. If not choice-based, leave blank.

First, you need to recheck the previous answers against the new transcript to detect any potential conflicts or new information.
- If the new transcript contains conflicting information, update the previous answer according to the current transcript. 
- If the new transcript contains additional/new information, update the previous answer by adding the new information while keeping the previous answer.
- If the new answer is similar to the previous answer, no need to update.

Second, find answers in the new transcript for questions not answered previously:
- Only fill out the answer if the transcript has clearly addressed the question.

important:
- Only answer the questions that are clearly addressed in the transcript.
- Output ONLY for the updated answers and newly answered questions. 
- Do not make up information, follow the transcript.
- Format your response as a JSON array, nothing else.

SURVEY QUESTIONS:
{survey_questions}

PREVIOUS ANSWERS:
{previous_answers}

NEW TRANSCRIPT:
{transcript}

output example:
[
  {{
    "question_id": "5",
    "answer": "yes",
    "certainty": "high",
    "text field": "support in finding an apartment is urgent. Prefer first-hand contract"
  }},
  {{
    "question_id": "10",
    "answer": "lonely and depressed, having trouble to sleep and hard to find time for friends",
    "certainty": "medium",
    "text field": ""
  }}
]
"""

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
    Update the answers.json file with new answers.
    
    Args:
        new_answers (list): List of new answers from AI
    """
    try:
        # Load existing answers or create new dict
        try:
            with open("answers.json", "r") as f:
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
        with open("answers.json", "w") as f:
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
    if os.path.exists("answers.json"):
        # Get previous answers as string
        with open("answers.json", "r") as f:
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
        prompt = create_prompt_without_answers(survey_questions, transcript)
    
    response = client.chat.completions.create(
        model="o4-mini-2025-04-16",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Process response and update tracking
    new_answers = process_ai_response(response.choices[0].message.content)
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