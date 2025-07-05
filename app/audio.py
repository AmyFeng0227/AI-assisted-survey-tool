from pathlib import Path
import os
from .config import client

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
