import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
from ui.survey_app import save_uploaded_survey, save_uploaded_audio, divide_and_sort_questions, extract_question_object, extract_answer_data, display_edit_window
from app.main_workflow import prepare_survey, process_recording



# Set page config
st.set_page_config(
    page_title="AI-assisted survey",
    layout="wide"
)

# Load custom CSS from a separate file
with open('ui/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def main():
    st.title("AI-assisted survey")
    
    # Debug: Add manual cache clear button
    if st.button("🔄 Clear Cache & Reload"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    # Load custom CSS
    with open('ui/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # Initialize session state
    if "survey_processed" not in st.session_state:
        st.session_state["survey_processed"] = False
    if "processed_audio_files" not in st.session_state:
        st.session_state["processed_audio_files"] = set()

    # Create two columns for file uploaders
    col1, col2 = st.columns(2)

    # Survey file uploader
    with col1:
        uploaded_file = st.file_uploader("Upload a survey file", type=["xlsx"])
        if uploaded_file and not st.session_state["survey_processed"]:
            excel_name = save_uploaded_survey(uploaded_file)
            st.write("Survey uploaded successfully! Please proceed to upload an audio file.")
            st.session_state["survey_data"], st.session_state["df"] = prepare_survey(excel_name)
            st.session_state["survey_processed"] = True
            st.session_state["current_survey_name"] = excel_name
        elif uploaded_file and st.session_state["survey_processed"]:
            st.write("Survey already loaded. Upload audio files to add more answers.")

    # Audio file uploader
    with col2:
        uploaded_audio = st.file_uploader("Upload an audio file", type=["m4a", "mp4"])
        if uploaded_audio and "df" in st.session_state and "survey_data" in st.session_state:
            # Create a unique identifier for this audio file
            audio_id = f"{uploaded_audio.name}_{uploaded_audio.size}"
            
            if audio_id not in st.session_state["processed_audio_files"]:
                audio_name, file_extension = save_uploaded_audio(uploaded_audio)
                st.session_state["df"] = process_recording(
                    audio_name, 
                    st.session_state["survey_data"], 
                    st.session_state["df"],
                    file_extension
                )
                st.session_state["processed_audio_files"].add(audio_id)
                st.write(f'Survey answers successfully updated!')
            else:
                st.write("This audio file has already been processed.")
        elif uploaded_audio and "df" not in st.session_state:
            st.error("Please upload a survey file first!")

    # Add a reset button
    if st.button("Reset Survey"):
        if os.path.exists("data/answers.json"):
            os.remove("data/answers.json")
        for key in ["survey_processed", "processed_audio_files", "df", "survey_data", "current_survey_name"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if "df" not in st.session_state:
        st.write("No survey loaded yet. Please upload a survey file and then an audio file.")
        return
    else:
        st.header("Survey Questions")
        
        # Create two columns for questions
        left_col, right_col = st.columns(2)
        
        # Split and sort questions into answered and unanswered based on certainty
        answered_questions, unanswered_questions = divide_and_sort_questions(st.session_state["df"])
        
        # Display answered questions
        with left_col:
            st.subheader("Answered:")
            for idx, row in answered_questions.iterrows():
                question = extract_question_object(idx, row)
                answer_data = extract_answer_data(row)
                container_class = f"{row['certainty']}-certainty"
                
                display_edit_window(question, answer_data, container_class, idx)

        # Display unanswered questions
        with right_col:
            st.subheader("Unanswered:")
            for idx, row in unanswered_questions.iterrows():
                question = extract_question_object(idx, row)
                answer_data = extract_answer_data(row)

                display_edit_window(question, answer_data, 'unanswered', idx)

if __name__ == "__main__":
    main() 