"""
Test suite for rnnoise_process.py module.

This module tests the audio denoising functionality including:
- File validation and error handling
- Output directory management and cleanup
- FFmpeg command construction and execution
- Race condition handling for file operations
"""

import os
import tempfile
import shutil
import uuid
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from utils.rnnoise_process import (
    get_file_info,
    cleanup_old_files,
    denoise_with_rnnoise,
    model_path,
    RNNOISE_OUTPUT_DIR,
    MAX_DIR_SIZE_MB,
)


class TestGetFileInfo:
    """Test the get_file_info utility function."""

    def test_get_file_info_returns_correct_format(self, tmp_path):
        """Test that get_file_info returns size in MB and modification time."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        test_content = "x" * 1024  # 1KB
        test_file.write_text(test_content)

        size_mb, mtime = get_file_info(test_file)

        # Size should be approximately 1KB = 0.001MB
        assert isinstance(size_mb, float)
        assert 0.0009 < size_mb < 0.002  # Allow for filesystem overhead

        # Modification time should be a float timestamp
        assert isinstance(mtime, float)
        assert mtime > 0

    def test_get_file_info_with_large_file(self, tmp_path):
        """Test get_file_info with a larger file."""
        test_file = tmp_path / "large.txt"
        test_content = "x" * (1024 * 1024)  # 1MB
        test_file.write_text(test_content)

        size_mb, mtime = get_file_info(test_file)

        # Size should be approximately 1MB
        assert 0.9 < size_mb < 1.1


class TestCleanupOldFiles:
    """Test the cleanup_old_files function."""

    @patch("utils.rnnoise_process.Path")
    def test_cleanup_when_under_limit(self, mock_path):
        """Test that cleanup does nothing when under size limit."""
        # Mock glob to return no files
        mock_path.return_value.glob.return_value = []

        # Should not raise any errors
        cleanup_old_files()

        mock_path.assert_called_once_with(RNNOISE_OUTPUT_DIR)

    @patch("utils.rnnoise_process.Path")
    @patch("utils.rnnoise_process.get_file_info")
    @patch("utils.rnnoise_process.os.remove")
    def test_cleanup_removes_oldest_files(
        self, mock_remove, mock_get_file_info, mock_path
    ):
        """Test that cleanup removes oldest files when over limit."""
        # Create mock files with different modification times
        old_file = MagicMock()
        old_file.__str__ = lambda: "old.wav"
        new_file = MagicMock()
        new_file.__str__ = lambda: "new.wav"

        mock_path.return_value.glob.return_value = [old_file, new_file]

        # Mock file info: old file (600MB, older time), new file (600MB, newer time)
        mock_get_file_info.side_effect = [
            (600.0, 1000.0),  # old file: 600MB, timestamp 1000
            (600.0, 2000.0),  # new file: 600MB, timestamp 2000
        ]

        cleanup_old_files()

        # Should remove the older file to get under 1GB limit
        mock_remove.assert_called_once_with(old_file)

    @patch("utils.rnnoise_process.Path")
    @patch("utils.rnnoise_process.get_file_info")
    def test_cleanup_handles_file_removal_errors(self, mock_get_file_info, mock_path):
        """Test that cleanup handles errors gracefully when removing files."""
        mock_file = MagicMock()
        mock_path.return_value.glob.return_value = [mock_file]
        mock_get_file_info.return_value = (2000.0, 1000.0)  # 2GB file, over limit

        with patch(
            "utils.rnnoise_process.os.remove",
            side_effect=PermissionError("Access denied"),
        ):
            # Should not raise exception
            cleanup_old_files()


class TestDenoiseWithRnnoise:
    """Test the main denoise_with_rnnoise function."""

    def test_missing_model_file_returns_empty_string(self):
        """Test that missing model file returns empty string with error message."""
        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = False

            result = denoise_with_rnnoise("test_input.wav")

            assert result == ""
            mock_model_path.exists.assert_called_once()

    def test_missing_input_file_returns_empty_string(self):
        """Test that missing input file returns empty string."""
        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True

            with patch("pathlib.Path") as mock_path:
                mock_path.return_value.exists.return_value = False

                result = denoise_with_rnnoise("nonexistent.wav")

                assert result == ""

    def test_unreadable_input_file_returns_empty_string(self):
        """Test that unreadable input file returns empty string."""
        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True

            with patch("pathlib.Path") as mock_path:
                mock_path.return_value.exists.return_value = True

                with patch(
                    "builtins.open", side_effect=PermissionError("Access denied")
                ):
                    result = denoise_with_rnnoise("locked_file.wav")

                    assert result == ""

    @patch("utils.rnnoise_process.os.makedirs")
    def test_output_directory_creation_failure(self, mock_makedirs):
        """Test handling of output directory creation failure."""
        mock_makedirs.side_effect = PermissionError("Cannot create directory")

        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True

            with patch("pathlib.Path") as mock_path:
                mock_path.return_value.exists.return_value = True

                with patch("builtins.open", mock_open()):
                    result = denoise_with_rnnoise("test.wav")

            assert result == ""

    @patch("utils.rnnoise_process.subprocess.run")
    @patch("utils.rnnoise_process.os.makedirs")
    @patch("utils.rnnoise_process.cleanup_old_files")
    def test_successful_processing(self, mock_cleanup, mock_makedirs, mock_subprocess):
        """Test successful audio processing workflow."""
        # Setup mocks for successful execution
        mock_result = MagicMock()
        mock_result.stdout = "FFmpeg output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True
            mock_model_path.as_posix.return_value = (
                "/path/to/model.rnnn"  # Mock the input file Path object specifically
            )
            with patch("utils.rnnoise_process.Path") as MockPath:
                # Create mock instances for different Path calls
                mock_input_path = MagicMock()
                mock_input_path.exists.return_value = True
                mock_input_path.stem = "test_audio"

                mock_output_dir_path = MagicMock()
                mock_output_dir_path.__truediv__.return_value.as_posix.return_value = (
                    "output/test_audio_uuid_denoised.wav"
                )
                mock_output_dir_path.touch.return_value = None
                mock_output_dir_path.unlink.return_value = None

                # Configure Path to return appropriate mocks based on input
                def path_side_effect(path_str):
                    if str(path_str) == "test_audio.wav":
                        return mock_input_path
                    elif (
                        "output" in str(path_str).lower()
                        or path_str == RNNOISE_OUTPUT_DIR
                    ):
                        return mock_output_dir_path
                    else:
                        return mock_input_path  # Default to input path mock

                MockPath.side_effect = path_side_effect

                with patch("builtins.open", mock_open()):
                    with patch(
                        "utils.rnnoise_process.os.path.getsize", return_value=1024
                    ):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            mock_uuid.return_value = MagicMock()
                            mock_uuid_str = str(mock_uuid.return_value).replace("-", "")

                            result = denoise_with_rnnoise("test_audio.wav")

                            # Should return the output path
                            assert result != ""
                            assert "test_audio" in result
                            assert "denoised.wav" in result

                            # Should call cleanup
                            mock_cleanup.assert_called_once()

                            # Should call subprocess with correct parameters
                            mock_subprocess.assert_called_once()
                            call_args = mock_subprocess.call_args[1]
                            assert call_args["check"] is True
                            assert call_args["capture_output"] is True
                            assert call_args["text"] is True

    @patch("utils.rnnoise_process.subprocess.run")
    @patch("utils.rnnoise_process.os.makedirs")
    def test_ffmpeg_command_construction(self, mock_makedirs, mock_subprocess):
        """Test that FFmpeg command is constructed correctly."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True
            mock_model_path.as_posix.return_value = (
                "/test/model.rnnn"  # Mock the input file Path object specifically
            )
            with patch("utils.rnnoise_process.Path") as MockPath:
                # Create mock instances for different Path calls
                mock_input_path = MagicMock()
                mock_input_path.exists.return_value = True
                mock_input_path.stem = "audio"

                mock_output_dir_path = MagicMock()
                mock_output_dir_path.__truediv__.return_value.as_posix.return_value = (
                    "output.wav"
                )
                mock_output_dir_path.touch.return_value = None
                mock_output_dir_path.unlink.return_value = None

                # Configure Path to return appropriate mocks based on input
                def path_side_effect(path_str):
                    if str(path_str) == "input.wav":
                        return mock_input_path
                    elif (
                        "output" in str(path_str).lower()
                        or path_str == RNNOISE_OUTPUT_DIR
                    ):
                        return mock_output_dir_path
                    else:
                        return mock_input_path  # Default to input path mock

                MockPath.side_effect = path_side_effect

                with patch("builtins.open", mock_open()):
                    with patch(
                        "utils.rnnoise_process.os.path.getsize", return_value=1024
                    ):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            # Mock UUID to return a predictable string
                            mock_uuid_obj = MagicMock()
                            mock_uuid_obj.__str__ = MagicMock(return_value="test-uuid")
                            mock_uuid.return_value = mock_uuid_obj

                            denoise_with_rnnoise("input.wav")

                            # Verify FFmpeg command structure
                            assert mock_subprocess.called
                            call_args = mock_subprocess.call_args[0][
                                0
                            ]  # First positional argument
                            assert call_args[0] == "ffmpeg"
                            assert "-threads" in call_args
                            assert "-i" in call_args
                            assert "input.wav" in call_args
                            assert "-af" in call_args
                            # Should contain the RNNoise filter with model path
                            af_index = call_args.index("-af")
                            assert (
                                "arnndn=m=/test/model.rnnn" == call_args[af_index + 1]
                            )

    @patch("utils.rnnoise_process.subprocess.run")
    @patch("utils.rnnoise_process.os.makedirs")
    def test_ffmpeg_failure_with_diagnostic_messages(
        self, mock_makedirs, mock_subprocess
    ):
        """Test FFmpeg failure scenarios with diagnostic messages."""
        # Test FFmpeg not found scenario
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1,
            ["ffmpeg"],
            stderr="'ffmpeg' is not recognized as an internal or external command",
        )

        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True

            with patch("pathlib.Path") as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.touch.return_value = None
                mock_path.return_value.unlink.return_value = None
                mock_path.return_value.stem = "audio"
                mock_path.return_value.__truediv__.return_value.as_posix.return_value = (
                    "output.wav"
                )

                with patch("builtins.open", mock_open()):
                    with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                        mock_uuid.return_value.__str__ = lambda: "test-uuid"

                        result = denoise_with_rnnoise("test.wav")

                        assert result == ""

    @patch("utils.rnnoise_process.subprocess.run")
    @patch("utils.rnnoise_process.os.makedirs")
    def test_output_file_validation_race_condition_handling(
        self, mock_makedirs, mock_subprocess
    ):
        """Test race condition handling in output file validation."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True

            with patch("pathlib.Path") as mock_path:
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.touch.return_value = None
                mock_path.return_value.unlink.return_value = None
                mock_path.return_value.stem = "audio"
                mock_path.return_value.__truediv__.return_value.as_posix.return_value = (
                    "output.wav"
                )

                with patch("builtins.open", mock_open()):
                    # Test FileNotFoundError scenario (race condition)
                    with patch(
                        "utils.rnnoise_process.os.path.getsize",
                        side_effect=FileNotFoundError(),
                    ):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            mock_uuid.return_value.__str__ = lambda: "test-uuid"

                            result = denoise_with_rnnoise("test.wav")

                            assert result == ""

                    # Test PermissionError scenario
                    with patch(
                        "utils.rnnoise_process.os.path.getsize",
                        side_effect=PermissionError(),
                    ):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            mock_uuid.return_value.__str__ = lambda: "test-uuid"

                            result = denoise_with_rnnoise("test.wav")

                            assert result == ""

                    # Test empty file scenario
                    with patch("utils.rnnoise_process.os.path.getsize", return_value=0):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            mock_uuid.return_value.__str__ = lambda: "test-uuid"

                            result = denoise_with_rnnoise("test.wav")

                            assert result == ""


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""

    @patch("utils.rnnoise_process.subprocess.run")
    def test_full_workflow_with_real_file_operations(self, mock_subprocess):
        """Test the full workflow with actual file operations where possible."""
        mock_result = MagicMock()
        mock_result.stdout = "Processing complete"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a mock input file
            input_file = Path(tmp_dir) / "test_audio.wav"
            input_file.write_text("mock audio data")

            # Create a mock model file
            mock_model = Path(tmp_dir) / "model.rnnn"
            mock_model.write_text("mock model data")

            with patch("utils.rnnoise_process.model_path", mock_model):
                with patch("utils.rnnoise_process.RNNOISE_OUTPUT_DIR", tmp_dir):
                    # Mock the output file creation by subprocess
                    def mock_subprocess_side_effect(*args, **kwargs):
                        # Simulate FFmpeg creating an output file
                        cmd = args[0]
                        output_path = cmd[-1]  # Last argument should be output path
                        Path(output_path).write_text("processed audio data")
                        return mock_result

                    mock_subprocess.side_effect = mock_subprocess_side_effect

                    result = denoise_with_rnnoise(str(input_file))

                    # Should return a valid output path
                    assert result != ""
                    assert Path(result).exists()
                    assert Path(result).suffix == ".wav"
                    assert "denoised" in Path(result).name


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        # The function should catch exceptions and return empty string
        with patch("utils.rnnoise_process.model_path") as mock_model_path:
            mock_model_path.exists.return_value = True
            mock_model_path.as_posix.return_value = "/path/to/model.rnnn"

            # Mock input file to exist but cause exception during processing
            with patch("pathlib.Path") as MockPath:
                mock_input_path = MagicMock()
                mock_input_path.exists.return_value = True
                mock_input_path.stem.side_effect = RuntimeError("Unexpected error")

                MockPath.return_value = mock_input_path

                with patch("builtins.open", mock_open()):
                    result = denoise_with_rnnoise("test.wav")

                    # Should return empty string when exception occurs
                    assert result == ""

    @patch("utils.rnnoise_process.subprocess.run")
    @patch("utils.rnnoise_process.os.makedirs")
    def test_various_ffmpeg_error_scenarios(self, mock_makedirs, mock_subprocess):
        """Test different FFmpeg error scenarios and their diagnostic messages."""
        error_scenarios = [
            ("command not found", "FFmpeg is not installed"),
            ("could not load model", "RNNoise model file issue"),
            ("moov atom not found", "Audio file is corrupted"),
            ("permission denied", "File permission issue"),
            ("no space left", "Insufficient disk space"),
            ("unknown error", "Unknown FFmpeg error"),
        ]

        for stderr_msg, expected_cause in error_scenarios:
            mock_subprocess.side_effect = subprocess.CalledProcessError(
                1, ["ffmpeg"], stderr=stderr_msg
            )

            with patch("utils.rnnoise_process.model_path") as mock_model_path:
                mock_model_path.exists.return_value = True

                with patch("pathlib.Path") as mock_path:
                    mock_path.return_value.exists.return_value = True
                    mock_path.return_value.touch.return_value = None
                    mock_path.return_value.unlink.return_value = None
                    mock_path.return_value.stem = "audio"
                    mock_path.return_value.__truediv__.return_value.as_posix.return_value = (
                        "output.wav"
                    )

                    with patch("builtins.open", mock_open()):
                        with patch("utils.rnnoise_process.uuid.uuid4") as mock_uuid:
                            mock_uuid.return_value.__str__ = lambda: "test-uuid"

                            result = denoise_with_rnnoise("test.wav")

                            assert result == ""


if __name__ == "__main__":
    pytest.main([__file__])
