"""
drive_service.py
----------------
Upload flow:
  1. Upload to Supabase (reliable, no quota issues)
  2. Send to Google Apps Script webhook → file appears in Drive with full preview

Configure in secrets.toml:
  [settings]
  supabase_url = "..."
  supabase_key = "..."
  supabase_bucket = "submissions"
  webhook_url = "https://script.google.com/macros/s/YOUR_ID/exec"
"""

import base64
import streamlit as st
import requests


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
    filename = build_filename(question_id, student_name, student_id)

    # ── Step 1: Upload to Supabase (primary storage) ──────────────────────────
    supabase_url = st.secrets["settings"]["supabase_url"].rstrip("/")
    supabase_key = st.secrets["settings"]["supabase_key"]
    bucket = st.secrets["settings"]["supabase_bucket"]

    url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "image/jpeg",
    }
    response = requests.put(url, headers=headers, data=image_bytes)
    if response.status_code not in (200, 201):
        raise Exception(f"Supabase upload failed: {response.status_code} {response.text}")

    # ── Step 2: Send to Apps Script webhook → lands in Drive ──────────────────
    webhook_url = st.secrets["settings"].get("webhook_url", "")
    if webhook_url:
        payload = {
            "filename": filename,
            "image": base64.b64encode(image_bytes).decode("utf-8"),
        }
        try:
            requests.post(webhook_url, json=payload, timeout=15)
        except Exception:
            pass  # Drive copy is best-effort; Supabase is the reliable backup

    return filename
