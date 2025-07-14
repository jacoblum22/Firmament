"""
User-friendly error message utilities for StudyMate backend.
Provides standardized, helpful error messages for common failure scenarios.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorMessages:
    """Centralized error message handling with user-friendly messages"""

    # Generic error messages
    GENERIC_ERRORS = {
        "upload_failed": "We couldn't process your upload. Please try again.",
        "file_not_found": "The requested file could not be found. It may have been deleted or moved.",
        "processing_failed": "We encountered an issue while processing your file. Please try uploading again.",
        "server_error": "Something went wrong on our end. Please try again in a few moments.",
        "invalid_request": "The request couldn't be processed. Please check your input and try again.",
        "timeout": "The operation took too long to complete. Please try again.",
        "insufficient_storage": "Not enough storage space available. Please free up some space and try again.",
        "rate_limited": "You're making requests too quickly. Please wait a moment and try again.",
    }

    # File processing specific errors
    FILE_PROCESSING_ERRORS = {
        "ffmpeg_missing": {
            "message": "Audio processing is currently unavailable",
            "details": "Our audio converter needs to be set up. Please contact support if this issue persists.",
            "user_action": "Try uploading a different file format (PDF or TXT) for now.",
        },
        "audio_conversion_failed": {
            "message": "We couldn't convert your audio file",
            "details": "The audio file might be corrupted or in an unsupported format.",
            "user_action": "Try converting your file to MP3 or WAV format and upload again.",
        },
        "transcription_failed": {
            "message": "We couldn't transcribe your audio",
            "details": "The audio might be too quiet, noisy, or in an unsupported language.",
            "user_action": "Try improving audio quality or upload a different file.",
        },
        "pdf_processing_failed": {
            "message": "We couldn't extract text from your PDF",
            "details": "The PDF might be password-protected, corrupted, or contain only images.",
            "user_action": "Try saving the PDF in a different format or upload a text file instead.",
        },
        "topic_generation_failed": {
            "message": "We couldn't generate topics for your content",
            "details": "The text might be too short or doesn't contain enough meaningful content.",
            "user_action": "Try uploading a longer document with more detailed content.",
        },
    }

    @staticmethod
    def get_user_friendly_error(
        error_type: str,
        technical_error: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Convert technical errors into user-friendly messages.

        Args:
            error_type: The type of error (e.g., 'upload_failed', 'ffmpeg_missing')
            technical_error: The original technical error message
            context: Additional context for error customization

        Returns:
            Dict containing user-friendly error information
        """
        context = context or {}

        # Check for specific file processing errors first
        if error_type in ErrorMessages.FILE_PROCESSING_ERRORS:
            error_info = ErrorMessages.FILE_PROCESSING_ERRORS[error_type]
            return {
                "error": error_info["message"],
                "details": error_info["details"],
                "user_action": error_info["user_action"],
                "error_code": error_type,
                "recoverable": True,
            }

        # Handle generic errors
        if error_type in ErrorMessages.GENERIC_ERRORS:
            return {
                "error": ErrorMessages.GENERIC_ERRORS[error_type],
                "error_code": error_type,
                "recoverable": True,
            }

        # Handle specific technical errors
        if technical_error:
            return ErrorMessages._handle_technical_error(technical_error, context)

        # Fallback for unknown errors
        return {
            "error": "An unexpected error occurred. Please try again.",
            "error_code": "unknown_error",
            "recoverable": True,
        }

    @staticmethod
    def _handle_technical_error(
        technical_error: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle specific technical error patterns"""
        error_lower = technical_error.lower()

        # FFmpeg related errors
        if "ffmpeg" in error_lower and "not found" in error_lower:
            return ErrorMessages.get_user_friendly_error("ffmpeg_missing")

        # File not found errors
        if "no such file" in error_lower or "file not found" in error_lower:
            return {
                "error": "The file you're trying to access is no longer available.",
                "details": "It may have been deleted during processing or due to storage cleanup.",
                "user_action": "Please upload your file again.",
                "error_code": "file_not_found",
                "recoverable": True,
            }

        # Permission errors
        if "permission denied" in error_lower:
            return {
                "error": "We couldn't access the file due to permission restrictions.",
                "details": "This is usually a temporary server issue.",
                "user_action": "Please try again in a few moments.",
                "error_code": "permission_error",
                "recoverable": True,
            }

        # Memory/resource errors
        if any(
            keyword in error_lower
            for keyword in ["memory", "out of space", "disk full"]
        ):
            return {
                "error": "Our servers are currently experiencing high load.",
                "details": "We don't have enough resources to process your file right now.",
                "user_action": "Please try again in a few minutes, or try uploading a smaller file.",
                "error_code": "resource_exhausted",
                "recoverable": True,
            }

        # Network/timeout errors
        if any(
            keyword in error_lower for keyword in ["timeout", "connection", "network"]
        ):
            return {
                "error": "We lost connection while processing your file.",
                "details": "This can happen with very large files or slow connections.",
                "user_action": "Please check your internet connection and try again.",
                "error_code": "network_error",
                "recoverable": True,
            }

        # Fallback for unhandled technical errors
        return {
            "error": "We encountered a technical issue while processing your request.",
            "details": "Our team has been notified and will investigate.",
            "user_action": "Please try again. If the problem persists, contact support.",
            "error_code": "technical_error",
            "recoverable": True,
        }

    @staticmethod
    def format_file_size_error(actual_size: int, max_size: int, file_type: str) -> str:
        """Format a user-friendly file size error message"""
        actual_mb = actual_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)

        return (
            f"Your {file_type.upper()} file is too large ({actual_mb:.1f}MB). "
            f"The maximum size allowed is {max_mb:.1f}MB. "
            f"Try compressing your file or uploading a smaller version."
        )

    @staticmethod
    def format_validation_error(field: str, issue: str, suggestion: str = "") -> str:
        """Format a user-friendly validation error"""
        message = f"There's an issue with your {field}: {issue}."
        if suggestion:
            message += f" {suggestion}"
        return message

    @staticmethod
    def log_error_for_monitoring(
        error_type: str,
        technical_error: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        """Log error details for monitoring while showing user-friendly message"""
        logger.error(
            f"Error occurred: {error_type}",
            extra={
                "error_type": error_type,
                "technical_error": technical_error,
                "context": context,
                "user_id": user_id,
            },
        )
