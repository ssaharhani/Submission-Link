"""
drive_service.py
----------------
All communication with Google Drive.

Upload flow:
  1. Upload file to service account's space
  2. Share the file with the teacher's Gmail so it appears in "Shared with me"
"""

import io
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    creds_dict = dict(st.secrets["google_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def build_filename(question_id: str, student_name: str, student_id: str) -> str:
    clean_name = student_name.strip().replace(" ", "_")
    clean_id = student_id.strip().replace(" ", "_")
    return f"{question_id}_{clean_name}_{clean_id}.jpg"


def upload_image(
    image_bytes: bytes,
    question_id: str,
    student_name: str,
    student_id: str,
) -> str:
    service = _get_drive_service()
    teacher_email = st.secrets["settings"]["teacher_email"]
    filename = build_filename(question_id, student_name, student_id)

    # Step 1: Upload the file
    file_metadata = {"name": filename}
    media = MediaIoBaseUpload(
        io.BytesIO(image_bytes),
        mimetype="image/jpeg",
        resumable=False,
    )
    uploaded = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name",
        )
        .execute()
    )
    file_id = uploaded.get("id", "")

    # Step 2: Share with teacher's Gmail → appears in "Shared with me"
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": teacher_email,
    }
    service.permissions().create(
        fileId=file_id,
        body=permission,
        sendNotificationEmail=False,
    ).execute()

    return file_id
