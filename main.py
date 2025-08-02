import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st
from ui.survey_app import save_uploaded_survey, save_uploaded_audio, divide_and_sort_questions, extract_question_object, extract_answer_data, display_edit_window, create_excel_download, calculate_progress_data, create_progress_bar
from app.main_workflow import prepare_survey, process_single_chunk
from app.audio import process_audio_file, chunk_transcription_by_sentences
from app.config import n_sentences, n_overlap
from app.evaluation import evaluate_ai_answers, log_chunk, summarize_all_chunks



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
    if "list_human_edit" not in st.session_state:
        st.session_state["list_human_edit"] = []
    # Chunked processing session state
    if "chunked_processing" not in st.session_state:
        st.session_state["chunked_processing"] = False
    if "current_chunks" not in st.session_state:
        st.session_state["current_chunks"] = []
    if "current_chunk_index" not in st.session_state:
        st.session_state["current_chunk_index"] = 0
    if "processing_audio_name" not in st.session_state:
        st.session_state["processing_audio_name"] = ""
    if "processing_file_extension" not in st.session_state:
        st.session_state["processing_file_extension"] = ""
    if "should_auto_continue" not in st.session_state:
        st.session_state["should_auto_continue"] = False
        

        
    # Handle chunked processing
    if st.session_state["chunked_processing"]:
        chunks = st.session_state["current_chunks"]
        current_index = st.session_state["current_chunk_index"]
        
        if current_index < len(chunks):
            # Process current chunk
            with st.spinner(f"Processing chunk {current_index + 1}/{len(chunks)}..."):
                st.session_state["df"] = process_single_chunk(
                    chunks[current_index],
                    current_index + 1,
                    len(chunks),
                    st.session_state["df"],
                    st.session_state["survey_data"]
                )
                
            # Move to next chunk
            st.session_state["current_chunk_index"] += 1
            
            # Show progress
            st.success(f'✅ Chunk {current_index + 1}/{len(chunks)} completed!')
            
            # Check if more chunks to process
            if st.session_state["current_chunk_index"] < len(chunks):
                st.info(f"🔄 Ready to process chunk {st.session_state['current_chunk_index'] + 1}/{len(chunks)}")
            else:
                # All chunks processed
                st.success(f'🎉 All {len(chunks)} chunks processed successfully!')
                st.session_state["chunked_processing"] = False
                st.session_state["should_auto_continue"] = False  # Explicitly stop auto-continue
                summarize_all_chunks(n_sentences, n_overlap, len(chunks))
                evaluate_ai_answers(n_sentences, n_overlap)
                # Mark this audio file as processed
                if st.session_state.get('original_audio_id'):
                    st.session_state["processed_audio_files"].add(st.session_state['original_audio_id'])
        
    # Auto-continue processing marker (will be handled at the bottom after showing survey)
    chunks_len = len(st.session_state.get("current_chunks", []))
    current_idx = st.session_state.get("current_chunk_index", 0)
    is_chunking = st.session_state.get("chunked_processing", False)
    
    st.session_state["should_auto_continue"] = (
        is_chunking and current_idx < chunks_len
    )
    


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
        if uploaded_audio and "df" in st.session_state:
            # Create a unique identifier for this audio file
            audio_id = f"{uploaded_audio.name}_{uploaded_audio.size}"
            
            # Check if we should process this audio file
            already_processed = audio_id in st.session_state["processed_audio_files"]
            currently_processing = st.session_state["chunked_processing"]
            
            if not already_processed and not currently_processing:
                audio_name, file_extension = save_uploaded_audio(uploaded_audio)
                
                # Start chunked processing
                with st.spinner("Transcribing audio and preparing chunks..."):
                    # Transcribe audio
                    transcript = process_audio_file(audio_name, file_extension)
                    if transcript:
                        
                        # Create chunks
                        chunks = chunk_transcription_by_sentences(transcript, n_sentences, n_overlap)
                        
                        # Set up session state for chunked processing
                        st.session_state["current_chunks"] = chunks
                        st.session_state["current_chunk_index"] = 0
                        st.session_state["processing_audio_name"] = audio_name
                        st.session_state["processing_file_extension"] = file_extension
                        st.session_state["original_audio_id"] = audio_id  # Store original ID for tracking
                        st.session_state["chunked_processing"] = True
                        
                        st.success(f"🎵 Audio transcribed! Created {len(chunks)} chunks. Starting processing...")
                        st.rerun()
                    else:
                        st.error("Failed to transcribe audio")
            elif audio_id in st.session_state["processed_audio_files"]:
                st.write("This audio file has already been processed.")
            elif st.session_state["chunked_processing"]:
                st.info("Currently processing chunks. Please wait...")
        elif uploaded_audio and "df" not in st.session_state:
            st.error("Please upload a survey file first!")

    # Add a reset button
    if st.button("Reset Survey"):
        if os.path.exists("data/answers.json"):
            os.remove("data/answers.json")
        for key in ["survey_processed", "processed_audio_files", "df", "survey_data", "current_survey_name", "excel_data", "list_human_edit", "chunked_processing", "current_chunks", "current_chunk_index", "processing_audio_name", "processing_file_extension", "should_auto_continue", "original_audio_id"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Download Excel button (only show when data exists)
    if "df" in st.session_state and not st.session_state["df"].empty:
        survey_name = st.session_state.get("current_survey_name", "survey")
        filename = f"{survey_name}_answers.xlsx"
        
        # Create Excel data once per session (cached until data changes)
        if "excel_data" not in st.session_state or st.session_state["excel_data"] is None:
            st.session_state["excel_data"] = create_excel_download(st.session_state["df"], survey_name)
        
        # Single download button
        st.download_button(
            label="📊 Download Excel", 
            data=st.session_state["excel_data"],
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if "df" not in st.session_state:
        st.write("No survey loaded yet. Please upload a survey file and then an audio file.")
        return
    else:
        # Calculate and display progress bar
        progress_data = calculate_progress_data(st.session_state["df"])
        progress_html = create_progress_bar(progress_data)
        st.markdown(progress_html, unsafe_allow_html=True)
        
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
                
                # Check if human-edited first, otherwise use certainty-based coloring
                if row['source'] == "human":
                    container_class = "human-edited"
                else:
                    container_class = f"{row['certainty']}-certainty"
                
                display_edit_window(question, answer_data, container_class, idx)

        # Display unanswered questions
        with right_col:
            st.subheader("Unanswered:")
            for idx, row in unanswered_questions.iterrows():
                question = extract_question_object(idx, row)
                answer_data = extract_answer_data(row)

                display_edit_window(question, answer_data, 'unanswered', idx)

    # Handle auto-continue processing at the end (after showing survey results)
    should_continue = st.session_state.get("should_auto_continue", False)
    
    if should_continue:
        st.write("🔄 Auto-continuing to next chunk...")
        st.session_state["should_auto_continue"] = False  # Reset flag
        import time
        time.sleep(2)  # Give user time to see the results
        st.rerun()
    else:
        st.write("⏹️ Processing complete or stopped.")

if __name__ == "__main__":
    main() 