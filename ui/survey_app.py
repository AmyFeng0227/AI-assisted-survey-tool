import json
from datetime import datetime
import pandas as pd
import os
import streamlit as st
from io import BytesIO
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
        
        # Add to human edit list only if not already there (keep unique)
        if question_id not in st.session_state["list_human_edit"]:
            st.session_state["list_human_edit"].append(question_id)

        # Update the DataFrame in session state
        st.session_state["df"] = update_answers_dataframe(st.session_state["df"], [new_answer], "human")
        
        # Clear cached Excel data so it gets regenerated with new data
        if "excel_data" in st.session_state:
            st.session_state["excel_data"] = None
        
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

# === Download function ===
def create_excel_download(df, survey_name="survey"):
    """
    Create an Excel file from the DataFrame for download.
    
    Args:
        df (pd.DataFrame): The survey DataFrame to export
        survey_name (str): Name of the survey for the filename
        
    Returns:
        bytes: Excel file data as bytes
    """
    try:
        # Create a BytesIO buffer to hold the Excel data
        buffer = BytesIO()
        
        # Create Excel writer object
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Write the main data
            df.to_excel(writer, sheet_name='Survey_Results', index=True)
        
        # Return the Excel data as bytes
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error creating Excel file: {e}")
        return None


def calculate_progress_data(df):
    """
    Calculate the distribution of questions by certainty level.
    
    Args:
        df (pd.DataFrame): The survey DataFrame
        
    Returns:
        dict: Dictionary with counts and percentages for each certainty level
    """
    total_questions = len(df)
    
    # Count questions by certainty level
    high_count = len(df[df['certainty'] == 'high'])
    medium_count = len(df[df['certainty'] == 'medium'])
    low_count = len(df[df['certainty'] == 'low'])
    unanswered_count = len(df[df['certainty'].isna()])
    
    # Calculate percentages
    high_pct = (high_count / total_questions) * 100 if total_questions > 0 else 0
    medium_pct = (medium_count / total_questions) * 100 if total_questions > 0 else 0
    low_pct = (low_count / total_questions) * 100 if total_questions > 0 else 0
    unanswered_pct = (unanswered_count / total_questions) * 100 if total_questions > 0 else 0
    
    return {
        'total': total_questions,
        'high': {'count': high_count, 'percentage': high_pct},
        'medium': {'count': medium_count, 'percentage': medium_pct},
        'low': {'count': low_count, 'percentage': low_pct},
        'unanswered': {'count': unanswered_count, 'percentage': unanswered_pct}
    }


def create_progress_bar(progress_data):
    """
    Create HTML for a progress bar showing question completion status.
    
    Args:
        progress_data (dict): Dictionary with counts and percentages for each certainty level
        
    Returns:
        str: HTML string for the progress bar
    """
    total = progress_data['total']
    high = progress_data['high']
    medium = progress_data['medium']
    low = progress_data['low']
    unanswered = progress_data['unanswered']
    
    # Calculate completion percentage
    answered_count = high['count'] + medium['count'] + low['count']
    completion_pct = (answered_count / total) * 100 if total > 0 else 0
    
    # Ensure minimum width for visibility (at least 3% if there are any questions in that category)
    high_width = max(high['percentage'], 3.0) if high['count'] > 0 else 0
    medium_width = max(medium['percentage'], 3.0) if medium['count'] > 0 else 0
    low_width = max(low['percentage'], 3.0) if low['count'] > 0 else 0
    unanswered_width = max(unanswered['percentage'], 3.0) if unanswered['count'] > 0 else 0
    
    # Normalize if total width exceeds 100%
    total_width = high_width + medium_width + low_width + unanswered_width
    if total_width > 100:
        high_width = (high_width / total_width) * 100
        medium_width = (medium_width / total_width) * 100
        low_width = (low_width / total_width) * 100
        unanswered_width = (unanswered_width / total_width) * 100
    
    # Build progress segments
    segments = []
    if high['count'] > 0:
        segments.append(f'<div class="progress-segment high-progress" style="width: {high_width:.1f}%;" title="High certainty: {high["count"]} questions">{high["count"]}</div>')
    if medium['count'] > 0:
        segments.append(f'<div class="progress-segment medium-progress" style="width: {medium_width:.1f}%;" title="Medium certainty: {medium["count"]} questions">{medium["count"]}</div>')
    if low['count'] > 0:
        segments.append(f'<div class="progress-segment low-progress" style="width: {low_width:.1f}%;" title="Low certainty: {low["count"]} questions">{low["count"]}</div>')
    if unanswered['count'] > 0:
        segments.append(f'<div class="progress-segment unanswered-progress" style="width: {unanswered_width:.1f}%;" title="Unanswered: {unanswered["count"]} questions">{unanswered["count"]}</div>')
    
    segments_html = '\n            '.join(segments)
    
    progress_html = f"""
    <div class="progress-container">
        <div class="progress-header">
            <h3>Survey Progress: {answered_count}/{total} questions answered ({completion_pct:.1f}%)</h3>
        </div>
        <div class="progress-bar">
            {segments_html}
        </div>
        <div class="progress-legend">
            <span class="legend-item high-legend">High ({high['count']})</span>
            <span class="legend-item medium-legend">Medium ({medium['count']})</span>
            <span class="legend-item low-legend">Low ({low['count']})</span>
            <span class="legend-item unanswered-legend">Unanswered ({unanswered['count']})</span>
        </div>
    </div>
    """
    
    return progress_html

