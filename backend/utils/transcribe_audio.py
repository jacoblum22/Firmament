import os
import shutil
import whisper
import threading
import uuid
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed
from faster_whisper import WhisperModel
import torch
from .clean_text import clean_chunk_text
from .rnnoise_process import denoise_with_rnnoise
from .preprocess_audio import preprocess_audio

TEMP_CHUNKS_DIR = "temp_chunks"


def _ensure_temp_dir():
    """Ensure the TEMP_CHUNKS_DIR directory exists."""
    os.makedirs(TEMP_CHUNKS_DIR, exist_ok=True)


def get_device():
    """Determine the best available device for transcription."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_compute_type(device):
    """Determine the best compute type for the device."""
    if device == "cuda":
        return "float16"  # Better accuracy with minimal speed impact on GPU
    return "int8"  # Best for CPU


from typing import Tuple


def prepare_audio_for_whisper(audio_path: str) -> Tuple[str, str]:
    """
    Prepare audio for Whisper by applying the full processing pipeline:
    1. RNNoise denoising
    2. Preprocessing (mono, 16kHz, normalization)

    Args:
        audio_path: Path to the input audio file

    Returns:
        Tuple containing the path to the processed audio file and the denoised file

    Raises:
        RuntimeError: If preprocessing fails
    """
    try:  # Step 1: Denoise with RNNoise
        print("Step 1/2: Denoising audio with RNNoise...")
        denoised_path = denoise_with_rnnoise(audio_path)
        if not os.path.exists(denoised_path):
            print(
                "Warning: Denoising failed or returned invalid output, proceeding with original audio"
            )
            denoised_path = audio_path  # Verify we have a valid audio file to work with
        if not os.path.exists(denoised_path):
            raise RuntimeError(f"No valid audio file available: {denoised_path}")

        # Step 2: Preprocess for Whisper
        print("Step 2/2: Preprocessing audio for Whisper...")
        # Create unique filename to prevent race conditions in concurrent processing
        _ensure_temp_dir()  # Ensure directory exists lazily
        unique_id = str(uuid.uuid4()).replace("-", "")[:12]
        preprocessed_path = os.path.join(
            TEMP_CHUNKS_DIR, f"preprocessed_{unique_id}.wav"
        )
        try:
            if os.path.exists(denoised_path) and os.access(denoised_path, os.R_OK):
                preprocess_audio(denoised_path, preprocessed_path)
            else:
                raise RuntimeError(
                    f"Denoised file '{denoised_path}' is not accessible"
                )  # Validate output file was created successfully
            if not os.path.exists(preprocessed_path):
                raise RuntimeError("Preprocessing failed: output file not created")

            # Check if file has valid content with context-aware validation
            file_size = os.path.getsize(preprocessed_path)
            if file_size == 0:
                raise RuntimeError("Preprocessing failed: output file is empty")

            # Calculate minimum expected file size based on WAV format
            # WAV header = 44 bytes + minimum audio data for meaningful transcription
            # For 16kHz mono 16-bit: ~0.1 seconds = 3200 samples = 6400 bytes + 44 header = 6444 bytes
            min_meaningful_size = 44 + (16000 * 0.1 * 2)  # 44 + 3200 = 3244 bytes

            if file_size < 44:
                raise RuntimeError(
                    "Preprocessing failed: file too small to contain valid WAV header"
                )
            elif file_size < min_meaningful_size:
                # Allow small files but warn - they might still be processable
                print(
                    f"Warning: Preprocessed file is small ({file_size} bytes). "
                    f"Audio duration may be very short and transcription quality could be affected."
                )  # Validate it's actually a readable audio file by checking WAV header
            try:
                with open(preprocessed_path, "rb") as f:
                    header = f.read(12)
                    if (
                        len(header) < 12
                        or header[:4] != b"RIFF"
                        or header[8:12] != b"WAVE"
                    ):
                        raise ValueError("Output file is not a valid WAV file")
            except (OSError, IOError) as file_error:
                raise RuntimeError(
                    f"Preprocessing failed: unable to read output file - {file_error}"
                )
            except ValueError as format_error:
                raise RuntimeError(f"Preprocessing failed: {format_error}")

        except Exception as e:
            # Clean up invalid output file if it exists
            if os.path.exists(preprocessed_path):
                try:
                    os.remove(preprocessed_path)
                except Exception as cleanup_error:
                    print(
                        f"Warning: Failed to cleanup invalid preprocessed file {preprocessed_path}: {cleanup_error}"
                    )
            raise RuntimeError(f"Preprocessing failed: {str(e)}")

        return preprocessed_path, denoised_path
    except Exception as e:
        raise RuntimeError(f"Audio preparation failed: {str(e)}")


def transcribe_audio_in_chunks(
    audio_path, model_size="tiny.en", chunk_ms=90_000, progress_callback=None
):
    """
    Transcribe audio in chunks with optimized settings and clean text in real-time.
    Applies the full audio processing pipeline:
    1. RNNoise denoising
    2. Preprocessing (mono, 16kHz, normalization)
    3. Whisper transcription

    Args:
        audio_path: Path to the audio file
        model_size: Whisper model size (tiny.en, base.en, small.en, medium.en)
        chunk_ms: Chunk size in milliseconds (default: 90 seconds)

    Returns:
        Transcribed and cleaned text

    Raises:
        RuntimeError: If audio processing or transcription fails
    """
    try:
        # Apply the full audio processing pipeline
        print("Starting audio processing pipeline...")
        processed_path, denoised_path = prepare_audio_for_whisper(audio_path)
        print("Audio processing completed successfully")

        # Load the processed audio
        audio = AudioSegment.from_file(processed_path)
        duration_ms = len(audio)

        # Determine best device and compute type
        device = get_device()
        compute_type = get_compute_type(device)
        print(f"Using device: {device} with compute type: {compute_type}")

        # Initialize model with optimized settings
        print(f"Loading Whisper model ({model_size})...")
        model = WhisperModel(
            model_size,
            compute_type=compute_type,
            device=device,
            download_root="./models",  # Cache models locally
        )
        print("Model loaded successfully")

        total_chunks = (duration_ms + chunk_ms - 1) // chunk_ms
        completed_chunks = 0
        lock = threading.Lock()  # Prepare chunks with overlap for better context
        print(f"Preparing {total_chunks} chunks for transcription...")
        _ensure_temp_dir()  # Ensure directory exists lazily
        chunk_paths = []
        for i in range(total_chunks):
            start = max(0, i * chunk_ms - 5000)  # 5 second overlap
            end = min(duration_ms, (i + 1) * chunk_ms + 5000)
            chunk = audio[start:end]
            chunk_filename = os.path.join(TEMP_CHUNKS_DIR, f"chunk_{i}.wav")
            chunk.export(
                chunk_filename, format="wav"
            )  # Export as WAV since it's already processed
            chunk_paths.append((i, chunk_filename))
        print("Chunk preparation completed")

        if progress_callback:
            progress_callback(0, total_chunks)

        transcript_chunks = [None] * total_chunks  # Ensure this is a list, not a tuple
        failed_chunks = []

        def transcribe_and_clean_chunk(idx, chunk_path):
            nonlocal completed_chunks
            try:
                # Use beam search for better accuracy
                segments, _ = model.transcribe(
                    chunk_path,
                    beam_size=5,
                    vad_filter=True,  # Voice activity detection
                    vad_parameters=dict(min_silence_duration_ms=500),
                )
                # Get raw text from segments
                raw_text = " ".join(segment.text for segment in segments)

                # Clean the text immediately
                cleaned_result = clean_chunk_text(raw_text)
                cleaned_text = cleaned_result["cleaned_text"]

                with lock:
                    completed_chunks += 1
                    print(
                        f"Progress: {completed_chunks}/{total_chunks} chunks completed"
                    )
                    if progress_callback:
                        progress_callback(completed_chunks, total_chunks)
                return idx, cleaned_text
            except Exception as e:
                print(f"Error in chunk {idx}: {e}")
                with lock:
                    failed_chunks.append((idx, chunk_path))
                return idx, None

        # Optimize thread count based on device and chunk size
        if device == "cpu":
            cpu_count = os.cpu_count() or 2  # Default to 2 if None
            max_workers = max(cpu_count // 2, 1)
        else:
            cpu_count = os.cpu_count() or 2  # Default to 2 if None
            max_workers = min(
                4, cpu_count
            )  # Limit GPU workers to prevent memory issues
        print(f"Using {max_workers} workers for transcription")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(transcribe_and_clean_chunk, idx, path): idx
                for idx, path in chunk_paths
            }

            for future in as_completed(futures):
                idx, text = future.result()
                if text is not None:
                    transcript_chunks[idx] = text

        # Retry failed chunks with more conservative settings
        if failed_chunks:
            print(
                f"\nRetrying {len(failed_chunks)} failed chunks with conservative settings..."
            )
            # Reuse the same model but with different settings
            model = WhisperModel(
                model_size,
                compute_type="int8",  # Use int8 for retries to ensure compatibility
                device="cpu",  # Use CPU for retries to ensure stability
            )

            for idx, path in failed_chunks:
                try:
                    segments, _ = model.transcribe(
                        path,
                        beam_size=3,  # Reduced beam size for faster retry
                        vad_filter=True,
                    )
                    # Clean the text for retried chunks as well
                    raw_text = " ".join(segment.text for segment in segments)
                    cleaned_result = clean_chunk_text(raw_text)
                    transcript_chunks[idx] = cleaned_result["cleaned_text"]
                    print(f"Successfully retried chunk {idx}")
                except Exception as e:
                    print(f"Failed to retry chunk {idx}: {e}")
                    transcript_chunks = [
                        None
                    ] * total_chunks  # Ensure this is a list, not a tuple

        # Cleanup
        print("\nCleaning up temporary files...")
        shutil.rmtree(TEMP_CHUNKS_DIR, ignore_errors=True)

        # Clean up processed file if it was created
        if processed_path != audio_path:
            try:
                os.remove(processed_path)
            except Exception as e:
                print(f"Warning: Failed to remove processed file {processed_path}: {e}")

        # Join chunks and do final cleanup to handle any cross-chunk issues
        print("Performing final text cleanup...")
        if progress_callback:
            # Ensure the frontend gets a final 100% progress update
            progress_callback(total_chunks, total_chunks)
        final_text = " ".join([t or "" for t in transcript_chunks]).strip()
        final_cleaned = clean_chunk_text(final_text)
        print("Transcription completed successfully")
        return final_cleaned["cleaned_text"], denoised_path

    except Exception as e:  # Cleanup on error
        shutil.rmtree(TEMP_CHUNKS_DIR, ignore_errors=True)
        if "processed_path" in locals() and processed_path != audio_path:
            try:
                os.remove(processed_path)
            except Exception as cleanup_error:
                print(
                    f"Warning: Failed to cleanup processed file {processed_path}: {cleanup_error}"
                )
        raise RuntimeError(f"Transcription failed: {str(e)}")
