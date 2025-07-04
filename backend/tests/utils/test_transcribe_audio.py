"""
Test suite for transcribe_audio.py module.

This module tests the audio transcription functionality including:
- Device and compute type detection
- Audio preparation pipeline (denoising and preprocessing)
- Chunk-based transcription with error handling
- File validation and cleanup
- Integration with Whisper models
"""

import os
import tempfile
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
import pytest

# Check for torch dependency
try:
    import torch
    from pydub import AudioSegment
    from utils.transcribe_audio import (
        get_device,
        get_compute_type,
        prepare_audio_for_whisper,
        transcribe_audio_in_chunks,
        TEMP_CHUNKS_DIR,
    )

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
class TestDeviceAndComputeType:
    """Test device detection and compute type selection."""

    @patch("torch.cuda.is_available")
    def test_get_device_cuda_available(self, mock_cuda):
        """Test device selection when CUDA is available."""
        mock_cuda.return_value = True
        assert get_device() == "cuda"

    @patch("torch.cuda.is_available")
    @patch("torch.backends.mps.is_available")
    def test_get_device_mps_available(self, mock_mps, mock_cuda):
        """Test device selection when MPS is available but CUDA is not."""
        mock_cuda.return_value = False
        mock_mps.return_value = True
        assert get_device() == "mps"

    @patch("torch.cuda.is_available")
    @patch("torch.backends.mps.is_available")
    def test_get_device_cpu_fallback(self, mock_mps, mock_cuda):
        """Test device selection falls back to CPU when neither CUDA nor MPS available."""
        mock_cuda.return_value = False
        mock_mps.return_value = False
        assert get_device() == "cpu"

    def test_get_compute_type_cuda(self):
        """Test compute type selection for CUDA device."""
        assert get_compute_type("cuda") == "float16"

    def test_get_compute_type_mps(self):
        """Test compute type selection for MPS device."""
        assert get_compute_type("mps") == "int8"

    def test_get_compute_type_cpu(self):
        """Test compute type selection for CPU device."""
        assert get_compute_type("cpu") == "int8"


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
class TestPrepareAudioForWhisper:
    """Test the audio preparation pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_audio_path = os.path.join(self.test_dir, "test_audio.wav")

        # Create a minimal WAV file for testing
        audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        audio.export(self.test_audio_path, format="wav")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up temp chunks directory
        if os.path.exists(TEMP_CHUNKS_DIR):
            shutil.rmtree(TEMP_CHUNKS_DIR, ignore_errors=True)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_successful_audio_preparation(self, mock_preprocess, mock_denoise):
        """Test successful audio preparation pipeline."""
        # Mock successful denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        with open(denoised_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 3244)  # Minimal WAV content
        mock_denoise.return_value = denoised_path

        # Mock successful preprocessing
        def mock_preprocess_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 3244)

        mock_preprocess.side_effect = mock_preprocess_side_effect

        processed_path, returned_denoised_path = prepare_audio_for_whisper(
            self.test_audio_path
        )

        # Verify function calls
        mock_denoise.assert_called_once_with(self.test_audio_path)
        mock_preprocess.assert_called_once()  # Verify output
        assert os.path.exists(processed_path)
        assert returned_denoised_path == denoised_path
        assert processed_path.endswith(".wav")
        assert "preprocessed_" in os.path.basename(processed_path)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_denoising_failure_fallback(self, mock_preprocess, mock_denoise):
        """Test fallback to original audio when denoising fails."""
        # Mock denoising failure (returns empty string or invalid path)
        mock_denoise.return_value = ""

        # Mock successful preprocessing of original audio
        def mock_preprocess_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 3244)

        mock_preprocess.side_effect = mock_preprocess_side_effect

        # Should succeed by falling back to original audio
        processed_path, denoised_path = prepare_audio_for_whisper(self.test_audio_path)

        # Verify fallback to original audio
        assert denoised_path == self.test_audio_path
        assert os.path.exists(processed_path)
        assert "preprocessed_" in os.path.basename(processed_path)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_preprocessing_failure(self, mock_preprocess, mock_denoise):
        """Test handling of preprocessing failures."""
        # Mock successful denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        with open(denoised_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100)
        mock_denoise.return_value = denoised_path

        # Mock preprocessing failure
        mock_preprocess.side_effect = Exception("Preprocessing failed")

        with pytest.raises(RuntimeError, match="Audio preparation failed"):
            prepare_audio_for_whisper(self.test_audio_path)

    def test_nonexistent_audio_file(self):
        """Test handling of nonexistent input audio file."""
        nonexistent_path = os.path.join(self.test_dir, "nonexistent.wav")

        with pytest.raises(RuntimeError, match="Audio preparation failed"):
            prepare_audio_for_whisper(nonexistent_path)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_empty_preprocessed_file_handling(self, mock_preprocess, mock_denoise):
        """Test handling when preprocessing creates an empty file."""
        # Mock successful denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        with open(denoised_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100)
        mock_denoise.return_value = denoised_path

        # Mock preprocessing that creates empty file
        def mock_preprocess_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                pass  # Create empty file

        mock_preprocess.side_effect = mock_preprocess_side_effect

        with pytest.raises(
            RuntimeError, match="Preprocessing failed: output file is empty"
        ):
            prepare_audio_for_whisper(self.test_audio_path)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_small_file_warning(self, mock_preprocess, mock_denoise):
        """Test warning for small but valid audio files."""
        # Mock successful denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        with open(denoised_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100)
        mock_denoise.return_value = denoised_path

        # Mock preprocessing that creates small but valid file
        def mock_preprocess_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100)  # Small but valid

        mock_preprocess.side_effect = mock_preprocess_side_effect

        # Should succeed but with warning (captured in logs)
        processed_path, _ = prepare_audio_for_whisper(self.test_audio_path)
        assert os.path.exists(processed_path)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    def test_invalid_wav_header_handling(self, mock_preprocess, mock_denoise):
        """Test handling of files with invalid WAV headers."""
        # Mock successful denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        with open(denoised_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * 100)
        mock_denoise.return_value = denoised_path

        # Mock preprocessing that creates file with invalid header
        def mock_preprocess_side_effect(input_path, output_path):
            with open(output_path, "wb") as f:
                f.write(b"INVALID_HEADER" + b"\x00" * 100)

        mock_preprocess.side_effect = mock_preprocess_side_effect

        with pytest.raises(
            RuntimeError,
            match="Preprocessing failed: Output file is not a valid WAV file",
        ):
            prepare_audio_for_whisper(self.test_audio_path)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
class TestTranscribeAudioInChunks:
    """Test the main transcription function with chunking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_audio_path = os.path.join(self.test_dir, "test_audio.wav")

        # Create a test audio file (5 seconds)
        audio = AudioSegment.silent(duration=5000)
        audio.export(self.test_audio_path, format="wav")

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Clean up temp chunks directory
        if os.path.exists(TEMP_CHUNKS_DIR):
            shutil.rmtree(TEMP_CHUNKS_DIR, ignore_errors=True)

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    @patch("utils.transcribe_audio.clean_chunk_text")
    def test_successful_transcription(
        self,
        mock_clean_text,
        mock_compute_type,
        mock_get_device,
        mock_whisper_model,
        mock_prepare_audio,
    ):
        """Test successful transcription of audio file."""
        # Mock audio preparation
        processed_path = os.path.join(self.test_dir, "processed.wav")
        denoised_path = os.path.join(self.test_dir, "denoised.wav")

        # Create processed audio file
        audio = AudioSegment.silent(duration=5000)
        audio.export(processed_path, format="wav")

        mock_prepare_audio.return_value = (processed_path, denoised_path)

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model
        mock_model = MagicMock()
        mock_segments = [MagicMock(text="This is test transcription.")]
        mock_model.transcribe.return_value = (mock_segments, None)
        mock_whisper_model.return_value = mock_model

        # Mock text cleaning
        mock_clean_text.return_value = {"cleaned_text": "This is test transcription."}

        # Run transcription
        result_text, result_denoised_path = transcribe_audio_in_chunks(
            self.test_audio_path,
            model_size="tiny.en",
            chunk_ms=10000,  # 10 seconds - larger than audio so only 1 chunk
        )

        # Verify results
        assert result_text == "This is test transcription."
        assert result_denoised_path == denoised_path

        # Verify function calls
        mock_prepare_audio.assert_called_once_with(self.test_audio_path)
        mock_whisper_model.assert_called_once()
        mock_model.transcribe.assert_called()

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    def test_audio_preparation_failure(self, mock_prepare_audio):
        """Test handling of audio preparation failures."""
        mock_prepare_audio.side_effect = RuntimeError("Audio preparation failed")

        with pytest.raises(
            RuntimeError, match="Transcription failed: Audio preparation failed"
        ):
            transcribe_audio_in_chunks(self.test_audio_path)

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    def test_whisper_model_loading_failure(
        self, mock_compute_type, mock_get_device, mock_whisper_model, mock_prepare_audio
    ):
        """Test handling of Whisper model loading failures."""
        # Mock successful audio preparation
        processed_path = os.path.join(self.test_dir, "processed.wav")
        audio = AudioSegment.silent(duration=1000)
        audio.export(processed_path, format="wav")
        mock_prepare_audio.return_value = (processed_path, "denoised.wav")

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model loading failure
        mock_whisper_model.side_effect = Exception("Model loading failed")

        with pytest.raises(
            RuntimeError, match="Transcription failed: Model loading failed"
        ):
            transcribe_audio_in_chunks(self.test_audio_path)

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    @patch("utils.transcribe_audio.clean_chunk_text")
    def test_multiple_chunks_processing(
        self,
        mock_clean_text,
        mock_compute_type,
        mock_get_device,
        mock_whisper_model,
        mock_prepare_audio,
    ):
        """Test processing of multiple audio chunks."""
        # Mock audio preparation - create longer audio to force multiple chunks
        processed_path = os.path.join(self.test_dir, "processed.wav")
        audio = AudioSegment.silent(duration=100000)  # 100 seconds
        audio.export(processed_path, format="wav")
        mock_prepare_audio.return_value = (processed_path, "denoised.wav")

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model
        mock_model = MagicMock()
        mock_segments = [MagicMock(text="Chunk text.")]
        mock_model.transcribe.return_value = (mock_segments, None)
        mock_whisper_model.return_value = mock_model

        # Mock text cleaning
        mock_clean_text.return_value = {"cleaned_text": "Chunk text."}

        # Run transcription with small chunks to force multiple chunks
        result_text, _ = transcribe_audio_in_chunks(
            self.test_audio_path,
            model_size="tiny.en",
            chunk_ms=30000,  # 30 seconds per chunk
        )

        # Should have multiple chunks worth of text
        assert "Chunk text." in result_text
        # Model should be called multiple times (once per chunk)
        assert mock_model.transcribe.call_count > 1

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    @patch("utils.transcribe_audio.clean_chunk_text")
    def test_chunk_transcription_failure_retry(
        self,
        mock_clean_text,
        mock_compute_type,
        mock_get_device,
        mock_whisper_model,
        mock_prepare_audio,
    ):
        """Test retry mechanism for failed chunk transcription."""
        # Mock audio preparation
        processed_path = os.path.join(self.test_dir, "processed.wav")
        audio = AudioSegment.silent(duration=10000)
        audio.export(processed_path, format="wav")
        mock_prepare_audio.return_value = (processed_path, "denoised.wav")

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model - first call fails, second succeeds
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = [
            Exception("Transcription failed"),  # First call fails
            ([MagicMock(text="Retry success.")], None),  # Retry succeeds
        ]
        mock_whisper_model.return_value = mock_model

        # Mock text cleaning
        mock_clean_text.return_value = {"cleaned_text": "Retry success."}

        # Run transcription
        result_text, _ = transcribe_audio_in_chunks(self.test_audio_path)

        # Should succeed with retry
        assert "Retry success." in result_text

    def test_progress_callback(self):
        """Test progress callback functionality."""
        progress_calls = []

        def mock_progress_callback(current, total):
            progress_calls.append((current, total))

        # Mock all dependencies to focus on progress callback
        with patch(
            "utils.transcribe_audio.prepare_audio_for_whisper"
        ) as mock_prepare, patch(
            "utils.transcribe_audio.WhisperModel"
        ) as mock_whisper, patch(
            "utils.transcribe_audio.get_device", return_value="cpu"
        ), patch(
            "utils.transcribe_audio.get_compute_type", return_value="int8"
        ), patch(
            "utils.transcribe_audio.clean_chunk_text",
            return_value={"cleaned_text": "Test"},
        ):

            # Setup mocks
            processed_path = os.path.join(self.test_dir, "processed.wav")
            audio = AudioSegment.silent(duration=1000)
            audio.export(processed_path, format="wav")
            mock_prepare.return_value = (processed_path, "denoised.wav")

            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text="Test")], None)
            mock_whisper.return_value = mock_model

            # Run with progress callback
            transcribe_audio_in_chunks(
                self.test_audio_path, progress_callback=mock_progress_callback
            )

            # Should have received progress updates
            assert len(progress_calls) > 0
            # Final call should be (total, total)
            final_call = progress_calls[-1]
            assert final_call[0] == final_call[1]

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    def test_cleanup_on_error(
        self, mock_compute_type, mock_get_device, mock_whisper_model, mock_prepare_audio
    ):
        """Test that temporary files are cleaned up on error."""
        # Mock audio preparation
        processed_path = os.path.join(self.test_dir, "processed.wav")
        audio = AudioSegment.silent(duration=1000)
        audio.export(processed_path, format="wav")
        mock_prepare_audio.return_value = (processed_path, "denoised.wav")

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model to raise exception
        mock_whisper_model.side_effect = Exception("Model error")

        # Ensure temp directory exists before test
        os.makedirs(TEMP_CHUNKS_DIR, exist_ok=True)

        with pytest.raises(RuntimeError):
            transcribe_audio_in_chunks(self.test_audio_path)

        # Temp directory should be cleaned up
        assert (
            not os.path.exists(TEMP_CHUNKS_DIR) or len(os.listdir(TEMP_CHUNKS_DIR)) == 0
        )


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_audio_file(self):
        """Test handling of empty audio files."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(RuntimeError):
                transcribe_audio_in_chunks(temp_path)
        finally:
            os.unlink(temp_path)

    def test_nonexistent_audio_file(self):
        """Test handling of nonexistent audio files."""
        nonexistent_path = "/path/to/nonexistent/file.wav"

        with pytest.raises(RuntimeError, match="Transcription failed"):
            transcribe_audio_in_chunks(nonexistent_path)

    @patch("utils.transcribe_audio.prepare_audio_for_whisper")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    @patch("utils.transcribe_audio.clean_chunk_text")
    def test_different_model_sizes(
        self,
        mock_clean_text,
        mock_compute_type,
        mock_get_device,
        mock_whisper_model,
        mock_prepare_audio,
    ):
        """Test transcription with different Whisper model sizes."""
        # Setup common mocks
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            audio = AudioSegment.silent(duration=1000)
            audio.export(temp_path, format="wav")

        try:
            mock_prepare_audio.return_value = (temp_path, "denoised.wav")
            mock_get_device.return_value = "cpu"
            mock_compute_type.return_value = "int8"

            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text="Test")], None)
            mock_whisper_model.return_value = mock_model
            mock_clean_text.return_value = {"cleaned_text": "Test"}

            # Test different model sizes
            for model_size in ["tiny.en", "base.en", "small.en", "medium.en"]:
                transcribe_audio_in_chunks(temp_path, model_size=model_size)

                # Verify model was initialized with correct size
                mock_whisper_model.assert_called_with(
                    model_size,
                    compute_type="int8",
                    device="cpu",
                    download_root="./models",
                )
        finally:
            os.unlink(temp_path)

    def test_invalid_chunk_size(self):
        """Test handling of invalid chunk sizes."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
            audio = AudioSegment.silent(duration=1000)
            audio.export(temp_path, format="wav")

        try:
            # Very small chunk size should still work (will be handled by the code)
            with patch(
                "utils.transcribe_audio.prepare_audio_for_whisper"
            ) as mock_prepare, patch(
                "utils.transcribe_audio.WhisperModel"
            ) as mock_whisper, patch(
                "utils.transcribe_audio.get_device", return_value="cpu"
            ), patch(
                "utils.transcribe_audio.get_compute_type", return_value="int8"
            ), patch(
                "utils.transcribe_audio.clean_chunk_text",
                return_value={"cleaned_text": "Test"},
            ):

                mock_prepare.return_value = (temp_path, "denoised.wav")
                mock_model = MagicMock()
                mock_model.transcribe.return_value = ([MagicMock(text="Test")], None)
                mock_whisper.return_value = mock_model

                # Test with very small chunk size
                transcribe_audio_in_chunks(temp_path, chunk_ms=100)  # 0.1 seconds

        finally:
            os.unlink(temp_path)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if os.path.exists(TEMP_CHUNKS_DIR):
            shutil.rmtree(TEMP_CHUNKS_DIR, ignore_errors=True)

    @patch("utils.transcribe_audio.denoise_with_rnnoise")
    @patch("utils.transcribe_audio.preprocess_audio")
    @patch("utils.transcribe_audio.WhisperModel")
    @patch("utils.transcribe_audio.get_device")
    @patch("utils.transcribe_audio.get_compute_type")
    @patch("utils.transcribe_audio.clean_chunk_text")
    @patch("utils.transcribe_audio.AudioSegment")
    def test_full_workflow_simulation(
        self,
        mock_audio_segment,
        mock_clean_text,
        mock_compute_type,
        mock_get_device,
        mock_whisper_model,
        mock_preprocess,
        mock_denoise,
    ):
        """Test a complete transcription workflow simulation."""
        # Create test audio file
        test_audio_path = os.path.join(self.test_dir, "lecture.wav")
        audio = AudioSegment.silent(duration=30000)  # 30 seconds
        audio.export(test_audio_path, format="wav")

        # Mock denoising
        denoised_path = os.path.join(self.test_dir, "denoised.wav")
        audio.export(denoised_path, format="wav")  # Create proper WAV file
        mock_denoise.return_value = denoised_path

        # Mock preprocessing
        def mock_preprocess_side_effect(input_path, output_path):
            # Create a proper WAV file for preprocessing output
            test_audio = AudioSegment.silent(duration=30000)
            test_audio.export(output_path, format="wav")

        mock_preprocess.side_effect = mock_preprocess_side_effect

        # Mock AudioSegment.from_file to return a mock audio object
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)  # 30 seconds in ms
        mock_audio.__getitem__ = MagicMock(return_value=mock_audio)  # For slicing
        mock_audio.export = MagicMock()  # Mock export method
        mock_audio_segment.from_file.return_value = mock_audio

        # Mock device detection
        mock_get_device.return_value = "cpu"
        mock_compute_type.return_value = "int8"

        # Mock Whisper model with realistic responses
        mock_model = MagicMock()
        chunk_responses = [
            "This is the first part of the lecture about machine learning.",
            "In this section we discuss neural networks and deep learning.",
            "Finally, we conclude with practical applications and examples.",
        ]

        def mock_transcribe_side_effect(audio_path, **kwargs):
            # Return different text for different chunks
            chunk_idx = mock_model.transcribe.call_count - 1
            if chunk_idx < len(chunk_responses):
                text = chunk_responses[chunk_idx]
            else:
                text = "Additional lecture content."
            return ([MagicMock(text=text)], None)

        mock_model.transcribe.side_effect = mock_transcribe_side_effect
        mock_whisper_model.return_value = mock_model

        # Mock text cleaning
        def mock_clean_side_effect(text):
            return {"cleaned_text": text.strip()}

        mock_clean_text.side_effect = mock_clean_side_effect

        # Run full transcription
        result_text, result_denoised_path = transcribe_audio_in_chunks(
            test_audio_path, model_size="tiny.en", chunk_ms=10000  # 10 second chunks
        )

        # Verify results
        assert "machine learning" in result_text
        assert "neural networks" in result_text
        assert "practical applications" in result_text
        assert result_denoised_path == denoised_path

        # Verify all components were called
        mock_denoise.assert_called_once_with(test_audio_path)
        mock_preprocess.assert_called()
        mock_whisper_model.assert_called_once()
        assert mock_model.transcribe.call_count >= 2  # Multiple chunks
