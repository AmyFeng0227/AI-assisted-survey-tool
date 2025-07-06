import pandas as pd
import json
from pathlib import Path
import streamlit as st

# === Survey Processing ===
def process_survey_excel(excel_name):
    """
    Process Excel survey file into JSON and DataFrame.
    
    Args:
        excel_name (str): Name of the Excel file (without extension)
        
    Returns:
        tuple: (list of survey questions in JSON format, DataFrame with survey and answer columns)
    """
    try:
        # Read Excel file
        df = pd.read_excel("data/surveys/"+excel_name+".xlsx", engine="openpyxl")
        
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
        output_path = Path("data/surveys/"+excel_name).with_suffix('.json')
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
        # Only include questions that haven't been human-edited
        # Convert question ID to float to match the data type in list_human_edit
        question_id_float = float(question['id'])
        if question_id_float not in st.session_state["list_human_edit"]:
            questions_text += f"{question['id']}: [{question['field']}] {question['question']} ({question['type']}"
            if question['options'] != ['']:
                questions_text += f": {', '.join(question['options'])})\n"
            else:
                questions_text += ")\n"
    
    return questions_text

