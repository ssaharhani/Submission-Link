"""
student_view.py
---------------
The student-facing submission form.

Flow:
  1. Poll Google Sheets for current status.
  2. If Closed → show a "Session is closed" message.
  3. If Open  → show the form (Name, ID, photo upload).
  4. On submit → compress image → upload to Drive → confirmation screen.

A manual "Refresh" button lets students sync without a full page reload
(addresses the 1-2 second state-latency noted in the spec).
"""

import streamlit as st
from services import sheets_service, drive_service, image_utils


def render() -> None:
    """Render the student submission page. Called from app.py."""

    st.title("📸 Submit Your Solution")

    # ── Refresh button (top-right feel via columns) ───────────────────────────
    _, refresh_col = st.columns([5, 1])
    with refresh_col:
        if st.button("🔄 Refresh"):
            st.rerun()

    # ── Poll the control sheet ────────────────────────────────────────────────
    try:
        state = sheets_service.get_session_state()
    except Exception as e:
        st.error(f"⚠️ Could not reach the server. Please try refreshing.\n\n`{e}`")
        st.stop()

    status = state["status"]
    question_id = state["question_id"]

    # ── Closed state ──────────────────────────────────────────────────────────
    if status != "Open":
        st.info("⏳ **Submissions are currently closed.**\n\nWait for your instructor to open the session, then tap 🔄 Refresh.")
        return

    # ── Open state: show the form ─────────────────────────────────────────────
    st.success(f"✅ Session is **OPEN** — submitting for: `{question_id}`")
    st.markdown("---")

    # Use session_state to prevent re-submission on rerun
    if st.session_state.get("submitted"):
        _show_success_screen(st.session_state["uploaded_filename"])
        return

    with st.form("submission_form", clear_on_submit=False):
        student_name = st.text_input(
            "Full Name",
            placeholder="e.g. Ali Hassan",
            max_chars=60,
        )
        student_id = st.text_input(
            "Student ID",
            placeholder="e.g. 202312345",
            max_chars=20,
        )
        photo = st.file_uploader(
            "Upload your solution photo",
            type=["jpg", "jpeg", "png", "heic"],
            help="Take a clear photo of your written solution. The image will be compressed automatically.",
        )

        submitted = st.form_submit_button("📤  Submit", use_container_width=True)

    if submitted:
        _handle_submission(question_id, student_name, student_id, photo)


# ── Private helpers ───────────────────────────────────────────────────────────

def _handle_submission(question_id, student_name, student_id, photo) -> None:
    """Validate inputs, compress, upload, update session state."""

    # Validation
    errors = []
    if not student_name.strip():
        errors.append("Please enter your full name.")
    if not student_id.strip():
        errors.append("Please enter your Student ID.")
    if photo is None:
        errors.append("Please upload a photo of your solution.")

    if errors:
        for err in errors:
            st.error(err)
        return

    # Compress
    with st.spinner("Compressing image…"):
        raw_bytes = photo.read()
        compressed = image_utils.compress_image(raw_bytes)

    # Upload
    with st.spinner("Uploading to Drive…"):
        try:
            drive_service.upload_image(
                image_bytes=compressed,
                question_id=question_id,
                student_name=student_name,
                student_id=student_id,
            )
        except Exception as e:
            st.error(f"❌ Upload failed. Please try again.\n\n`{e}`")
            return

    # Mark as submitted so a page rerun doesn't re-trigger the form
    filename = drive_service.build_filename(question_id, student_name, student_id)
    st.session_state["submitted"] = True
    st.session_state["uploaded_filename"] = filename
    st.rerun()


def _show_success_screen(filename: str) -> None:
    """Confirmation screen shown after a successful upload."""
    st.balloons()
    st.success("## ✅ Submission received!")
    st.markdown(f"**File saved as:** `{filename}`")
    st.markdown("You may close this tab. Good luck! 🎉")

    # Allow re-submission (e.g. wrong photo)
    if st.button("↩️ Submit again"):
        del st.session_state["submitted"]
        del st.session_state["uploaded_filename"]
        st.rerun()
