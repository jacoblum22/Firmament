from pydub import AudioSegment
import os


def preprocess_audio(input_path: str, output_path: str):
    # Validate input file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if not input_path.lower().endswith(
        (".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")
    ):
        raise ValueError(f"Unsupported audio format for file: {input_path}")

    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio = audio.apply_gain(-audio.max_dBFS)
        audio.export(output_path, format="wav")
    except Exception as e:
        raise RuntimeError(f"Error processing audio file {input_path}: {e}")
