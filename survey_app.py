import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Survey Processing Tool",
    layout="wide"
)

# Custom CSS for colored containers and styling
st.markdown("""
<style>
.high-certainty, .medium-certainty, .low-certainty, .unanswered {
    border-left: 3px solid;
    padding: 2px 4px;
    border-radius: 1px;
    margin: 0;
    font-size: 0.9em;
}
.high-certainty {
    background-color: #e8f5e9;
    border-left-color: #28a745;
}
.medium-certainty {
    background-color: #fff8e1;
    border-left-color: #ffc107;
}
.low-certainty {
    background-color: #ffebee;
    border-left-color: #dc3545;
}
.unanswered {
    background-color: #f5f5f5;
    border-left-color: #6c757d;
}
.question-header {
    margin: 0;
    padding: 0;
    line-height: 1.1;
}
.field-tag {
    color: #666;
    font-size: 0.8em;
    font-weight: normal;
}
.question-id {
    font-weight: bold;
    color: #333;
    font-size: 0.85em;
}
.question-text {
    font-size: 0.9em;
    margin: 1px 0;
}
.answer-text {
    margin: 2px 0 0 0;
    padding-left: 6px;
    border-left: 1px solid rgba(0,0,0,0.1);
    font-size: 0.85em;
    color: #2c3e50;
}
.selected-option, .unselected-option {
    white-space: nowrap;
}
.selected-option {
    font-weight: bold;
    color: #2c3e50;
}
.unselected-option {
    color: #666;
    font-style: italic;
}
.option-list {
    margin: 2px 0 0 6px;
    font-size: 0.85em;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.notes-text {
    margin: 1px 0 0 6px;
    font-size: 0.8em;
    color: #666;
    font-style: italic;
}
.streamlit-expanderHeader {
    padding: 0.1rem !important;
    font-size: 0.75em !important;
    min-height: 0 !important;
    line-height: 1 !important;
}
.streamlit-expanderHeader > span {
    padding: 0 !important;
    margin: 0 !important;
}
.streamlit-expanderHeader > div {
    margin: 0 !important;
    padding: 0 !important;
}
.streamlit-expanderHeader > div > span {
    margin: 0 !important;
    padding: 0 !important;
}
.streamlit-expanderHeader svg {
    width: 12px !important;
    height: 12px !important;
    margin: 0 4px 0 0 !important;
}
.streamlit-expanderContent {
    padding: 0.2rem !important;
}
.streamlit-expander {
    border-radius: 2px !important;
    border: none !important;
    box-shadow: none !important;
    margin: 0 !important;
}
.stTextInput, .stTextArea {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.8em !important;
}
.stTextInput > div {
    padding: 0 !important;
}
.stTextArea > div {
    padding: 0 !important;
}
.stTextInput input {
    padding: 0.2rem !important;
}
.stTextArea textarea {
    padding: 0.2rem !important;
    min-height: 50px !important;
}
.stRadio > label {
    margin: 0 !important;
    padding: 0 !important;
    height: auto !important;
    font-size: 0.8em !important;
}
.stRadio > div {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0.5rem !important;
}
.stRadio [role="radiogroup"] {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0.25rem !important;
}
.stMultiSelect > label {
    margin: 0 !important;
    padding: 0 !important;
    height: auto !important;
    font-size: 0.8em !important;
}
.stMultiSelect > div {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
}
.stMultiSelect [data-baseweb="select"] {
    font-size: 0.8em !important;
}
</style>
""", unsafe_allow_html=True)

def load_survey_data():
    """Load survey questions and current answers"""
    try:
        with open('survey_1.json', 'r') as f:
            survey = json.load(f)
        
        try:
            with open('answers.json', 'r') as f:
                answers = json.load(f)
        except FileNotFoundError:
            answers = {}
        
        return survey, answers
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def save_answers(answers):
    """Save updated answers to file"""
    try:
        with open('answers.json', 'w') as f:
            json.dump(answers, f, indent=2)
        
        # Also update the tracking DataFrame
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = pd.read_excel("survey_1.xlsx", engine="openpyxl")
        df.set_index('QuestionID', inplace=True)
        
        # Add answer columns if they don't exist
        answer_columns = ['answer', 'certainty', 'text_field', 'source', 'last_updated']
        for col in answer_columns:
            if col not in df.columns:
                df[col] = None
        
        # Update with new answers
        for qid, answer_data in answers.items():
            df.at[float(qid), 'answer'] = answer_data['answer']
            df.at[float(qid), 'certainty'] = answer_data['certainty']
            df.at[float(qid), 'text_field'] = answer_data.get('text field', '')
            df.at[float(qid), 'source'] = answer_data.get('source', 'human')
            df.at[float(qid), 'last_updated'] = answer_data.get('last_updated', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Save tracking DataFrame
        df.to_csv(f"survey_answers_tracking_{timestamp}.csv")
        
    except Exception as e:
        st.error(f"Error saving answers: {e}")

def display_progress_metrics(survey, answers):
    """Display progress metrics and bars"""
    total = len(survey)
    metrics = {
        'high': 0,
        'medium': 0,
        'low': 0,
        'unanswered': total
    }
    
    # Calculate metrics
    for q in survey:
        qid = q['id']
        if qid in answers:
            metrics['unanswered'] -= 1
            certainty = answers[qid]['certainty'].lower()
            metrics[certainty] += 1
    
    # Display metrics in columns
    cols = st.columns(4)
    with cols[0]:
        st.metric("High Certainty", metrics['high'], 
                 delta=f"{metrics['high']/total*100:.1f}%")
    with cols[1]:
        st.metric("Medium Certainty", metrics['medium'],
                 delta=f"{metrics['medium']/total*100:.1f}%")
    with cols[2]:
        st.metric("Low Certainty", metrics['low'],
                 delta=f"{metrics['low']/total*100:.1f}%")
    with cols[3]:
        st.metric("Unanswered", metrics['unanswered'],
                 delta=f"{metrics['unanswered']/total*100:.1f}%")
    
    # Display stacked progress bars
    st.write("Progress Overview:")
    col1, col2 = st.columns([3, 1])
    with col1:
        # Calculate percentages for each certainty level
        high_pct = metrics['high'] / total
        medium_pct = metrics['medium'] / total
        low_pct = metrics['low'] / total
        unanswered_pct = metrics['unanswered'] / total
        
        # Create a single stacked progress bar
        st.markdown(f"""
            <div style="width: 100%; height: 40px; background-color: #6c757d; border-radius: 5px; overflow: hidden;">
                <div style="width: {(high_pct + medium_pct + low_pct)*100}%; height: 100%; background-color: #28a745; float: left;">
                    <div style="width: {(medium_pct + low_pct)/(high_pct + medium_pct + low_pct)*100 if (high_pct + medium_pct + low_pct) > 0 else 0}%; height: 100%; background-color: #ffc107; float: right;">
                        <div style="width: {low_pct/(medium_pct + low_pct)*100 if (medium_pct + low_pct) > 0 else 0}%; height: 100%; background-color: #dc3545; float: right;"></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Calculate total progress as answered vs unanswered, regardless of certainty
        answered_count = metrics['high'] + metrics['medium'] + metrics['low']
        total_progress = answered_count / total
        st.write(f"Total Progress: {total_progress*100:.1f}%")

def main():
    st.title("Survey Processing Tool")
    
    # Add file upload section at the top
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Update Survey")
        uploaded_survey = st.file_uploader("Upload new survey Excel file", type=['xlsx'])
        if uploaded_survey:
            try:
                # Save the uploaded file
                with open(f"survey_1.xlsx", "wb") as f:
                    f.write(uploaded_survey.getvalue())
                st.success("Survey Excel file updated successfully!")
            except Exception as e:
                st.error(f"Error saving survey file: {e}")
    
    with col2:
        st.subheader("Add Recording")
        uploaded_recording = st.file_uploader("Upload new recording", type=['m4a'])
        if uploaded_recording:
            try:
                # Save the uploaded file with next available number
                existing_recordings = [f for f in os.listdir() if f.startswith("recording") and f.endswith(".m4a")]
                next_num = len(existing_recordings) + 1
                filename = f"recording{next_num}.m4a"
                
                with open(filename, "wb") as f:
                    f.write(uploaded_recording.getvalue())
                
                # Process the new recording
                from survey_processor import process_recording, prepare_survey
                survey_questions, df = prepare_survey("survey_1")
                if survey_questions and df is not None:
                    df = process_recording(f"recording{next_num}", survey_questions, df)
                    st.success(f"Recording processed and saved as {filename}")
                else:
                    st.error("Failed to process recording due to survey data issues")
            except Exception as e:
                st.error(f"Error processing recording: {e}")
    
    st.divider()
    
    # Load data
    survey, answers = load_survey_data()
    if not survey or not answers:
        st.error("Failed to load survey data. Please check your files.")
        return
    
    # Display progress section
    st.header("Survey Progress")
    display_progress_metrics(survey, answers)
    
    # Split questions into answered and unanswered
    answered_questions = []
    unanswered_questions = []
    
    for question in survey:
        qid = question['id']
        if qid in answers and answers[qid].get('answer'):
            answered_questions.append(question)
        else:
            unanswered_questions.append(question)
    
    # Create two columns for questions
    st.header("Survey Questions and Answers")
    left_col, right_col = st.columns(2)
    
    # Store any changes to be saved
    changes_made = False
    
    # Left column - Answered Questions
    with left_col:
        st.subheader(f"Answered Questions ({len(answered_questions)})")
        for question in answered_questions:
            qid = question['id']
            current_answer = answers.get(qid, {})
            certainty = current_answer.get('certainty', '').lower() if current_answer else ''
            container_class = f"{certainty}-certainty" if certainty else "unanswered"
            
            # Display question and current answer
            display_question_and_answer(question, current_answer, container_class)
            
            # Handle editing
            if handle_question_edit(question, current_answer, qid):
                changes_made = True
    
    # Right column - Unanswered Questions
    with right_col:
        st.subheader(f"Unanswered Questions ({len(unanswered_questions)})")
        for question in unanswered_questions:
            qid = question['id']
            current_answer = answers.get(qid, {})
            container_class = "unanswered"
            
            # Display question and current answer
            display_question_and_answer(question, current_answer, container_class)
            
            # Handle editing
            if handle_question_edit(question, current_answer, qid):
                changes_made = True
    
    # Save changes if any were made
    if changes_made:
        save_answers(answers)
        st.success("Changes saved successfully!")

def display_question_and_answer(question, current_answer, container_class):
    """Helper function to display a question and its answer"""
    answer_display = ""
    notes_display = ""
    
    if current_answer.get('answer'):
        if question['type'] in ['single choice', 'multiple choice']:
            current_selections = current_answer['answer']
            if isinstance(current_selections, str):
                current_selections = [current_selections]
            
            options_display = []
            for opt in question['options']:
                if opt in current_selections:
                    options_display.append(f'<span class="selected-option">✓ {opt}</span>')
                else:
                    options_display.append(f'<span class="unselected-option">○ {opt}</span>')
            answer_display = f'<div class="option-list">' + ' '.join(options_display) + '</div>'
        else:
            answer_display = f"<div class='answer-text'>{current_answer['answer']}</div>"
        
        if current_answer.get('text field'):
            notes_display = f"<div class='notes-text'>{current_answer['text field']}</div>"

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

def handle_question_edit(question, current_answer, qid):
    """Helper function to handle question editing"""
    # Initialize variables
    new_answer = current_answer.get('answer', '')
    new_text_field = current_answer.get('text field', '')
    changes_made = False
    
    # Add edit button
    if st.button("✎", key=f"edit_{qid}", help="Edit this answer", type="secondary"):
        # Show edit form based on question type
        if question['type'] == 'text':
            new_answer = st.text_area(
                "Answer",
                value=current_answer.get('answer', ''),
                key=f"answer_{qid}",
                label_visibility="collapsed"
            )
        elif question['type'] == 'number':
            new_answer = st.text_input(
                "Answer",
                value=current_answer.get('answer', ''),
                key=f"answer_{qid}",
                label_visibility="collapsed"
            )
        elif question['type'] == 'single choice':
            selected_answer = current_answer.get('answer', question['options'][0])
            new_answer = st.radio(
                "Answer",
                options=question['options'],
                index=question['options'].index(selected_answer) if selected_answer in question['options'] else 0,
                key=f"answer_{qid}",
                label_visibility="collapsed"
            )
        elif question['type'] == 'multiple choice':
            current_selections = current_answer.get('answer', [])
            if isinstance(current_selections, str):
                current_selections = [current_selections]
            
            new_answer = st.multiselect(
                "Answer",
                options=question['options'],
                default=current_selections,
                key=f"answer_{qid}",
                label_visibility="collapsed"
            )
        
        # Add text field for additional notes
        if question['type'] != 'text':
            new_text_field = st.text_area(
                "Additional notes",
                value=current_answer.get('text field', ''),
                key=f"notes_{qid}",
                label_visibility="collapsed",
                placeholder="Add notes here..."
            )
        
        # Check if changes were made
        if (new_answer != current_answer.get('answer', '') or 
            new_text_field != current_answer.get('text field', '')):
            
            answers[qid] = {
                'answer': new_answer,
                'certainty': current_answer.get('certainty', 'medium'),
                'text field': new_text_field,
                'source': 'human',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            changes_made = True
    
    return changes_made

if __name__ == "__main__":
    main() 