"""
drive_service.py
----------------
Uses domain-wide delegation to upload as the teacher directly.
The service account impersonates the teacher's Gmail so files
land in the teacher's Drive with no quota issues.
"""

import io
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _get_drive_service():
    creds_dict = dict(st.secrets["google_credentials"])
    teacher_email = st.secrets["settings"]["teacher_email"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES,
        subject=teacher_email,   # ← impersonate the teacher's Gmail
    )
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
    folder_id = st.secrets["settings"]["drive_folder_id"]
    filename = build_filename(question_id, student_name, student_id)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

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

    return uploaded.get("id", "")
