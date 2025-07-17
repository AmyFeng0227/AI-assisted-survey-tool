from pathlib import Path
import os
from .config import client
import re

# === Recording Processing ===
def process_audio_file(file_name, file_extension):
    """
    Process a single audio file and return its transcription.
    Also saves the transcription to a text file.
    
    Args:
        file_name (str): Name of the audio file (without extension)
        file_extension (str): File extension (m4a, mp4, etc.)
        
    Returns:
        str: Transcribed text
    """
    try:
        file_path = f"data/recordings/{file_name}.{file_extension}"
        
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file
            )
            # Save transcription to text file
            txt_path = "data/recordings/transcripts/"+file_name+'.txt'
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(transcription.text)

            return transcription.text
    except Exception as e:
        print(f"Error processing audio file {file_name}.{file_extension}: {e}")
        return None


def chunk_transcription_by_sentences(transcript, sentences_per_chunk=10, overlap_sentences=2):
    """
    Split a transcript into chunks with a specified number of sentences each.
    Preserves original line breaks from the transcript.
    
    Args:
        transcript (str): The transcribed text to chunk
        sentences_per_chunk (int): Number of sentences per chunk 
        overlap_sentences (int): Number of sentences to overlap between chunks (default: 0)
        
    Returns:
        list: List of text chunks
    """
    # Find sentence endings but keep the original text structure
    sentence_pattern = r'([.!?]+)'
    parts = re.split(sentence_pattern, transcript)
    
    # Reconstruct sentences with their punctuation and original spacing
    sentences = []
    for i in range(0, len(parts)-1, 2):
        if i+1 < len(parts):
            sentence = parts[i] + parts[i+1]  # text + punctuation
            if sentence.strip():  # Only add non-empty sentences
                sentences.append(sentence)
    
    # Add any remaining text
    if len(parts) % 2 == 1 and parts[-1].strip():
        sentences.append(parts[-1])
    
    # Group sentences into chunks with overlap
    chunks = []
    step_size = max(1, sentences_per_chunk - overlap_sentences)
    
    for i in range(0, len(sentences), step_size):
        chunk_sentences = sentences[i:i + sentences_per_chunk]
        if chunk_sentences:
            # Join without adding extra punctuation to preserve original formatting
            chunk_text = ''.join(chunk_sentences)
            chunks.append(chunk_text)
        
        # Stop if we've reached the end
        if i + sentences_per_chunk >= len(sentences):
            break
    
    return chunks
