import json
from datetime import datetime
import pandas as pd
import os
import streamlit as st

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
        # Create a timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        audio_name = f"recording_{timestamp}"
        
        # Save the file
        file_path = 'data/recordings/'+ audio_name+".m4a"
        with open(file_path, "wb") as f:
            f.write(uploaded_audio.getvalue())
        
        print(f"File saved as {audio_name}.m4a")
        return audio_name
    
def divide_and_sort_questions(df):
    """Divide questions into answered and unanswered"""
    answered_questions = df[df['certainty'].notna()].sort_values(by='last_updated', ascending=False)
    unanswered_questions = df[df['certainty'].isna()].sort_values(by='QuestionID')
    return answered_questions, unanswered_questions

def extract_question_object(idx, row):
    """Create a question object"""
    question = {
        'id': str(idx),
        'field': row['Field'],
        'question': row['Question'],
        'type': row['Type'].lower() if 'Type' in row else 'text',
        'options': row['Options'].split('; ') if pd.notna(row['Options']) else []
    }
    return question

def extract_answer_data(row):
    """Create an answer data object"""
    answer_data = {
        'answer': row['answer'],
        'certainty': row['certainty'],
        'text field': row['text_field'] if pd.notna(row['text_field']) else ''
    }
    return answer_data


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
            # Handle choice questions
            current_selections = answer_data['answer']

            options_display = []
            for opt in question['options']:
                if opt in current_selections:
                    options_display.append(f'<span class="selected-option">✓ {opt}</span>')
                else:
                    options_display.append(f'<span class="unselected-option">○ {opt}</span>')
            answer_display = f'<div class="option-list">' + ' '.join(options_display) + '</div>'
        else:
            # Handle text questions
            answer_display = f"<div class='answer-text'>{answer_data['answer']}</div>"
        
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



def save_answers(answers, survey_name=None):
    """Save updated answers to file"""
    try:
        with open('data/answers.json', 'w') as f:
            json.dump(answers, f, indent=2)
        
        # Also update the tracking DataFrame if survey_name is provided
        if survey_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            df = pd.read_excel(f"data/surveys/{survey_name}.xlsx", engine="openpyxl")
            df.set_index('QuestionID', inplace=True)
        
    except Exception as e:
        print(f"Error saving answers: {e}")


def display_progress_metrics(survey, answers):
    """Display progress metrics for the survey"""
    # Implementation of progress metrics
    pass




def handle_question_edit(question, current_answer, qid, answers):
    """Helper function to handle question editing"""
    # Initialize variables
    new_answer = current_answer.get('answer', '')
    new_text_field = current_answer.get('text field', '')
    changes_made = False
    
    # Logic for editing questions
    # This function should be called from the Streamlit app with the necessary UI components
    return changes_made

def display_question_with_edit(question, answer_data, container_class, qid):
    """
    Display a question with edit functionality using Streamlit widgets.
    
    Args:
        question (dict): Question object with id, field, question, type, and options
        answer_data (dict): Answer object with answer, certainty, and text field
        container_class (str): CSS class for styling
        qid: Question ID for unique widget keys
    
    Returns:
        dict: Updated answer data if changes were made, None if no changes
    """
    # Display question header
    st.markdown(f"""
    <div class="{container_class}">
        <div class="question-header">
            <span class="question-id">Q{question['id']}</span>
            <span class="field-tag">[{question['field']}]</span>
        </div>
        <div class="question-text">{question['question']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show current answer if exists
    if answer_data.get('answer'):
        if question['type'] in ['single choice', 'multiple choice']:
            current_selections = answer_data['answer'] if isinstance(answer_data['answer'], list) else [answer_data['answer']]
            options_display = []
            for opt in question['options']:
                if opt in current_selections:
                    options_display.append(f'✓ {opt}')
                else:
                    options_display.append(f'○ {opt}')
            st.markdown(f"**Current:** {' | '.join(options_display)}")
        else:
            st.markdown(f"**Current:** {answer_data['answer']}")
        
        if answer_data.get('certainty'):
            st.markdown(f"**Certainty:** {answer_data['certainty']}")
        
        if answer_data.get('text field'):
            st.markdown(f"**Notes:** {answer_data['text field']}")
    
    # Add edit section with expander
    with st.expander("✏️ Edit Answer", expanded=False):
        changes_made = False
        new_answer_data = answer_data.copy()
        
        # Handle different question types
        if question['type'] == 'single choice':
            current_answer = answer_data.get('answer', '')
            if isinstance(current_answer, list):
                current_answer = current_answer[0] if current_answer else ''
            
            selected_option = st.selectbox(
                "Select answer:",
                options=[''] + question['options'],
                index=question['options'].index(current_answer) + 1 if current_answer in question['options'] else 0,
                key=f"select_{qid}"
            )
            
            if selected_option != current_answer:
                new_answer_data['answer'] = [selected_option] if selected_option else ''
                changes_made = True
        
        elif question['type'] == 'multiple choice':
            current_answer = answer_data.get('answer', [])
            if not isinstance(current_answer, list):
                current_answer = [current_answer] if current_answer else []
            
            selected_options = st.multiselect(
                "Select answers:",
                options=question['options'],
                default=current_answer,
                key=f"multiselect_{qid}"
            )
            
            if set(selected_options) != set(current_answer):
                new_answer_data['answer'] = selected_options
                changes_made = True
        
        else:  # text question
            current_answer = answer_data.get('answer', '')
            new_answer = st.text_area(
                "Answer:",
                value=current_answer,
                key=f"text_{qid}"
            )
            
            if new_answer != current_answer:
                new_answer_data['answer'] = new_answer
                changes_made = True
        
        # Certainty level
        current_certainty = answer_data.get('certainty', '')
        new_certainty = st.selectbox(
            "Certainty level:",
            options=['', 'low', 'medium', 'high'],
            index=['', 'low', 'medium', 'high'].index(current_certainty) if current_certainty in ['', 'low', 'medium', 'high'] else 0,
            key=f"certainty_{qid}"
        )
        
        if new_certainty != current_certainty:
            new_answer_data['certainty'] = new_certainty
            changes_made = True
        
        # Text field/notes
        current_text_field = answer_data.get('text field', '')
        new_text_field = st.text_area(
            "Notes:",
            value=current_text_field,
            key=f"notes_{qid}"
        )
        
        if new_text_field != current_text_field:
            new_answer_data['text field'] = new_text_field
            changes_made = True
        
        # Save button
        if st.button("💾 Save Changes", key=f"save_{qid}"):
            if changes_made:
                new_answer_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_answer_data['source'] = 'manual'
                return new_answer_data
            else:
                st.info("No changes to save")
    
    return None

def update_question_answer(df, qid, new_answer_data):
    """
    Update DataFrame and answers.json with new answer data.
    
    Args:
        df (pd.DataFrame): The survey DataFrame
        qid: Question ID
        new_answer_data (dict): New answer data
    
    Returns:
        pd.DataFrame: Updated DataFrame
    """
    # Update DataFrame
    qid_float = float(qid)
    if qid_float in df.index:
        df.at[qid_float, 'answer'] = new_answer_data['answer']
        df.at[qid_float, 'certainty'] = new_answer_data['certainty']
        df.at[qid_float, 'text_field'] = new_answer_data['text field']
        df.at[qid_float, 'source'] = new_answer_data['source']
        df.at[qid_float, 'last_updated'] = new_answer_data['last_updated']
    
    # Update answers.json
    try:
        # Load existing answers
        if os.path.exists("data/answers.json"):
            with open("data/answers.json", "r") as f:
                answers = json.load(f)
        else:
            answers = {}
        
        # Update with new answer
        answers[str(qid)] = new_answer_data
        
        # Save back to file
        with open("data/answers.json", "w") as f:
            json.dump(answers, f, indent=2)
    
    except Exception as e:
        print(f"Error updating answers file: {e}")
    
    return df

def display_question_with_edit_visual(question, answer_data, container_class, qid):
    """
    Display a question with expandable edit section - VISUAL ONLY for now.
    
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
    
    # Add expandable edit section
    with st.expander("✏️ Edit Answer", expanded=False):
        
        # Show different input types based on question type
        if question['type'] == 'single choice':
            # Single choice answers are always lists with one element
            # Handle None values for unanswered questions
            answer_list = answer_data.get('answer') or ['']
            current_answer = answer_list[0]
            
            st.selectbox(
                "Select a single answer:",
                options=[''] + question['options'],
                index=question['options'].index(current_answer) + 1 if current_answer in question['options'] else 0,
                key=f"select_{qid}"
            )
        
        elif question['type'] == 'multiple choice':
            # Multiple choice answers are always lists
            # Handle None values for unanswered questions
            current_answer = answer_data.get('answer') or []
            
            st.multiselect(
                "Select multiple answers:",
                options=question['options'],
                default=current_answer,
                key=f"multiselect_{qid}"
            )
        
        else:  # text question
            # Handle None values for unanswered questions
            current_answer = answer_data.get('answer') or ''
            
            st.text_area(
                "Answer:",
                value=str(current_answer) if current_answer else '',
                key=f"text_{qid}",
                height=100
            )
        
        # Text field/notes - only show for choice questions, not text questions
        if question['type'] in ['single choice', 'multiple choice']:
            # Handle None values for unanswered questions
            current_text_field = answer_data.get('text field') or ''
            st.text_area(
                "Notes:",
                value=current_text_field,
                key=f"notes_{qid}",
                height=100
            )
        
        # Action buttons (just visual for now)
        if st.button("💾 Save Changes", key=f"save_{qid}"):
            st.info("Save functionality will be added next!")

