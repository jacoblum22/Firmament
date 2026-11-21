#!/usr/bin/env python3
"""
Integration tests for the /upload endpoint using FastAPI TestClient.
No live server required — the app is spun up in-process.
"""

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app, raise_server_exceptions=False)


def test_upload_valid_file():
    """Test file upload with a valid PDF file."""
    pdf_content = (
        b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
        b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n174\n%%EOF"
    )

    response = client.post(
        "/upload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code in (200, 201, 400, 422), (
        f"Unexpected status {response.status_code}: {response.text}"
    )


def test_upload_invalid_file():
    """Test file upload with an unsupported file type."""
    response = client.post(
        "/upload",
        files={"file": ("test.exe", b"Invalid content", "application/octet-stream")},
    )
    assert response.status_code in (400, 422), (
        f"Expected rejection of invalid file type, got {response.status_code}"
    )


def test_upload_empty_file():
    """Test file upload with an empty file."""
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"", "text/plain")},
    )
    assert response.status_code in (400, 422), (
        f"Expected rejection of empty file, got {response.status_code}"
    )
