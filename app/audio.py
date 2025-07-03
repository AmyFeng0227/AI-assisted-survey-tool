from pathlib import Path
from .config import client

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
        with open("data/recordings/"+file_name+".m4a", "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file
            )
            # Save transcription to text file
            txt_path = Path("data/transcripts/"+file_name).with_suffix('.txt')
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(transcription.text)

            return transcription.text
    except Exception as e:
        print(f"Error processing audio file {file_name}.m4a: {e}")
        return None
