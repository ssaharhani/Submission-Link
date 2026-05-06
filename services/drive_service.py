"""
drive_service.py
----------------
All communication with Google Drive.

Responsibilities:
  1. Authenticate via the same service-account credentials as the Sheets service.
  2. Upload a file (bytes) to the configured Drive folder.
  3. Apply the naming convention: {Question_ID}_{Student_Name}_{Student_ID}.jpg

The teacher configures the target folder via secrets.toml → settings.drive_folder_id
"""

import io
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

# Drive requires its own scope
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",  # create/upload files
]


def _get_drive_service():
    """Build and return an authenticated Drive API client."""
    creds_dict = dict(st.secrets["google_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def build_filename(question_id: str, student_name: str, student_id: str) -> str:
    """
    Construct the canonical filename.
    Spaces in name/ID are replaced with underscores for clean Drive filenames.

    Example: "Bonus_Q1_Ali_Hassan_202312345.jpg"
    """
    clean_name = student_name.strip().replace(" ", "_")
    clean_id = student_id.strip().replace(" ", "_")
    return f"{question_id}_{clean_name}_{clean_id}.jpg"


def upload_image(
    image_bytes: bytes,
    question_id: str,
    student_name: str,
    student_id: str,
) -> str:
    """
    Upload compressed image bytes to the configured Drive folder.

    Returns the Drive file ID (useful for generating a view link).
    Raises an exception on failure — the caller (student_view) handles UI feedback.
    """
    service = _get_drive_service()
    folder_id = st.secrets["settings"]["drive_folder_id"]
    filename = build_filename(question_id, student_name, student_id)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaIoBaseUpload(
        io.BytesIO(image_bytes),
        mimetype="image/jpeg",
        resumable=False,   # non-resumable is fine for compressed mobile photos
    )

    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, name")
        .execute()
    )

    return uploaded.get("id", "")
