import json
from datetime import datetime
import pandas as pd
import os
import streamlit as st
from app.answer import update_answers_file, update_answers_dataframe

# === Survey file uploader ===
def save_uploaded_survey(uploaded_file):
    """Save an uploaded Excel file to the data/surveys directory with a timestamped name."""
    if uploaded_file is not None:
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        excel_name = f"survey_{timestamp}"
        
        # Save the file
        file_path = 'data/surveys/'+ excel_name+".xlsx"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        print(f"File saved as {excel_name}.xlsx")
        return excel_name
    else:
        print("Please upload a survey file")
        return None 

# === Audio file uploader ===
def save_uploaded_audio(uploaded_audio):
    """Save an uploaded audio file to the data/recordings directory with a timestamped name."""
    if uploaded_audio is not None:
        # Get the original file extension
        original_extension = uploaded_audio.name.split('.')[-1].lower()
        
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        audio_name = f"recording_{timestamp}"
        
        # Save the file with original extension
        file_path = f'data/recordings/{audio_name}.{original_extension}'
        with open(file_path, "wb") as f:
            f.write(uploaded_audio.getvalue())
        
        print(f"File saved as {audio_name}.{original_extension}")
        return audio_name, original_extension

# === Divide and sort questions ===
def divide_and_sort_questions(df):
    """Divide questions into answered and unanswered"""
    answered_questions = df[df['certainty'].notna()].sort_values(by='QuestionID')
    unanswered_questions = df[df['certainty'].isna()].sort_values(by='QuestionID')
    return answered_questions, unanswered_questions


# === sub-function for displaying questions ===
def extract_question_object(idx, row):
    """Create a question object"""
    question = {
        'id': idx, 
        'field': row['Field'],
        'question': row['Question'],
        'type': row['Type'].lower() if 'Type' in row else 'text',
        'options': row['Options'].split('; ') if pd.notna(row['Options']) else []
    }
    return question

# === sub-function for displaying answers ===
def extract_answer_data(row):
    """Create an answer data object"""
    answer_data = {
        'answer': row['answer'],
        'certainty': row['certainty'],
        'text field': row['text_field'] if pd.notna(row['text_field']) else ''
    }
    return answer_data


# === main function for displaying questions and answers ===
def display_question_and_answer(question, answer_data, container_class):
    """
    Format a question and its answer with proper styling.
    
    Args:
        question (dict): Question object with id, field, question, type, and options
        answer_data (dict): Answer object with answer, certainty, and text field
        container_class (str): CSS class for styling (high/medium/low-certainty or unanswered)
    
    Returns:
        str: HTML formatted string for displaying the question and answer
    """
    answer_display = ""
    notes_display = ""
    
    if answer_data.get('answer'):
        if question['type'] in ['single choice', 'multiple choice']:
            # Handle choice questions - answers are always lists
            current_selections = answer_data.get('answer')

            options_display = []
            for opt in question['options']:
                if opt in current_selections:
                    options_display.append(f'<span class="selected-option">✓ {opt}</span>')
                else:
                    options_display.append(f'<span class="unselected-option">○ {opt}</span>')
            answer_display = f'<div class="option-list">' + ' '.join(options_display) + '</div>'
        else:
            # Handle text questions
            answer_display = f"<div class='answer-text'>{answer_data.get('answer')}</div>"
        
        # Add notes if present
        if answer_data.get('text field'):
            notes_display = f"<div class='notes-text'>{answer_data['text field']}</div>"
    elif container_class == 'unanswered' and question['type'] in ['single choice', 'multiple choice']:
        # Display empty options for unanswered choice questions
        options_display = [f'<span class="unselected-option">○ {opt}</span>' for opt in question['options']]
        answer_display = f'<div class="option-list">' + ' '.join(options_display) + '</div>'

    return f"""
    <div class="{container_class}">
        <div class="question-header">
            <div>
                <span class="question-id">Q{question['id']}</span>
                <span class="field-tag">[{question['field']}]</span>
            </div>
        </div>
        <div class="question-text">{question['question']}</div>
        {answer_display}
        {notes_display}
    </div>
    """


# === sub-function for Save changes button ===
def save_changes(question_id, question_type):
    """
    Save user changes to both the answers file and DataFrame.
    
    Args:
        question_id: The question ID
        question_type (str): Type of question ('single choice', 'multiple choice', 'text')
    """
    try:
        # Get the current values from the form inputs
        if question_type == 'single choice':
            answer_value = [st.session_state[f"select_{question_id}"]] if st.session_state[f"select_{question_id}"] else []
            notes_value = st.session_state.get(f"notes_{question_id}", "")
        elif question_type == 'multiple choice':
            answer_value = st.session_state[f"multiselect_{question_id}"]
            notes_value = st.session_state.get(f"notes_{question_id}", "")
        else:  # text question
            answer_value = st.session_state[f"text_{question_id}"]
            notes_value = ""  # Text questions don't have notes
        
        # Format the answer data for the update functions
        new_answer = {
            "question_id": question_id,
            "answer": answer_value,
            "text field": notes_value
        }
        
        # Update the answers file
        update_answers_file([new_answer], "human")
        
        # Update the DataFrame in session state
        st.session_state["df"] = update_answers_dataframe(st.session_state["df"], [new_answer], "human")
        
        # Collapse the expander after saving
        expander_key = f"expander_{question_id}"
        st.session_state[expander_key] = False
        
        return True
        
    except Exception as e:
        st.error(f"Error saving changes: {e}")
        return False

def display_edit_window(question, answer_data, container_class, qid):
    """
    Display a question with expandable edit section.
    
    Args:
        question (dict): Question object with id, field, question, type, and options
        answer_data (dict): Answer object with answer, certainty, and text field
        container_class (str): CSS class for styling
        qid: Question ID for unique widget keys
    """
    # Display the main question using existing function
    st.markdown(
        display_question_and_answer(question, answer_data, container_class),
        unsafe_allow_html=True
    )
    
    # Track expander state for each question
    expander_key = f"expander_{qid}"
    if expander_key not in st.session_state:
        st.session_state[expander_key] = False
    
    # Add expandable edit section
    with st.expander("✏️ Edit Answer", expanded=st.session_state[expander_key]):
        
        # Show different input types based on question type
        if question['type'] == 'single choice':
            # Single choice answers are lists, get first item or empty string
            current_answer = answer_data.get('answer', [''])[0] if answer_data.get('answer') else ''
            st.selectbox(
                "Select a single answer:",
                options=[''] + question['options'],
                index=question['options'].index(current_answer) + 1 if current_answer in question['options'] else 0,
                key=f"select_{qid}"
            )
        
        elif question['type'] == 'multiple choice':
            # Multiple choice answers are lists
            current_answer = answer_data.get('answer', [])
            st.multiselect(
                "Select multiple answers:",
                options=question['options'],
                default=current_answer,
                key=f"multiselect_{qid}"
            )
        
        else:  # text question
            current_answer = answer_data.get('answer') or ''
            st.text_area(
                "Answer:",
                value=current_answer,
                key=f"text_{qid}",
                height=100
            )
        
        # Text field/notes - only show for choice questions, not text questions
        if question['type'] in ['single choice', 'multiple choice']:
            current_text_field = answer_data.get('text field') or ''
            st.text_area(
                "Notes:",
                value=current_text_field,
                key=f"notes_{qid}",
                height=100
            )
        
        # Action buttons
        if st.button("💾 Save Changes", key=f"save_{qid}"):
            # Save the changes
            if save_changes(qid, question['type']):
                st.success("Changes saved successfully!")
                st.rerun()  # Force app to refresh and show updated data
            else:
                st.error("Failed to save changes!")

