"""
student_view.py
---------------
Student submission form.

Features:
  - Blocks re-submission by same student ID for same question
  - Allows multiple photos per submission
  - Manual refresh button for session sync
"""

import streamlit as st
from services import sheets_service, drive_service, image_utils


def render() -> None:
    st.title("📸 Submit Your Solution")

    _, refresh_col = st.columns([5, 1])
    with refresh_col:
        if st.button("🔄 Refresh"):
            st.rerun()

    # ── Poll session state ────────────────────────────────────────────────────
    try:
        state = sheets_service.get_session_state()
    except Exception as e:
        st.error(f"⚠️ Could not reach the server. Please refresh.\n\n`{e}`")
        st.stop()

    status = state["status"]
    question_id = state["question_id"]

    # ── Closed ────────────────────────────────────────────────────────────────
    if status != "Open":
        st.info("⏳ **Submissions are currently closed.**\n\nWait for your instructor to open the session, then tap 🔄 Refresh.")
        return

    st.success(f"✅ Session is **OPEN** — submitting for: `{question_id}`")
    st.markdown("---")

    # ── Already submitted this session ────────────────────────────────────────
    if st.session_state.get("submitted") and st.session_state.get("submitted_for") == question_id:
        _show_success_screen(st.session_state["uploaded_filenames"])
        return

    # ── Submission form ───────────────────────────────────────────────────────
    with st.form("submission_form", clear_on_submit=False):
        student_name = st.text_input("Full Name", placeholder="e.g. Ali Hassan", max_chars=60)
        student_id = st.text_input("Student ID", placeholder="e.g. 202312345", max_chars=20)
        photos = st.file_uploader(
            "Upload photo(s) of your solution",
            type=["jpg", "jpeg", "png", "heic"],
            accept_multiple_files=True,
            help="You can select multiple photos. All will be uploaded.",
        )
        submitted = st.form_submit_button("📤  Submit", use_container_width=True)

    if submitted:
        _handle_submission(question_id, student_name, student_id, photos)


# ── Private helpers ───────────────────────────────────────────────────────────

def _handle_submission(question_id, student_name, student_id, photos) -> None:
    errors = []
    if not student_name.strip():
        errors.append("Please enter your full name.")
    if not student_id.strip():
        errors.append("Please enter your Student ID.")
    if not photos:
        errors.append("Please upload at least one photo.")
    if errors:
        for err in errors:
            st.error(err)
        return

    # Check if student already submitted for this question
    try:
        existing = sheets_service.get_student_submissions(question_id)
        if student_id.strip() in existing:
            st.warning("⚠️ You already submitted for this question. Contact your instructor if you need to resubmit.")
            return
    except Exception:
        pass  # If check fails, allow submission

    uploaded_filenames = []

    for i, photo in enumerate(photos, start=1):
        # Add photo number suffix if multiple files: Q1_Ali_1.jpg, Q1_Ali_2.jpg
        suffix = f"_{i}" if len(photos) > 1 else ""
        with st.spinner(f"Uploading photo {i} of {len(photos)}…"):
            try:
                raw_bytes = photo.read()
                compressed = image_utils.compress_image(raw_bytes)
                drive_service.upload_image(
                    image_bytes=compressed,
                    question_id=question_id,
                    student_name=student_name,
                    student_id=student_id + suffix,
                )
                filename = drive_service.build_filename(question_id, student_name, student_id + suffix)
                uploaded_filenames.append(filename)
            except Exception as e:
                st.error(f"❌ Photo {i} failed: {e}")
                return

    # Log submission to prevent duplicates
    sheets_service.log_student_submission(question_id, student_id.strip())

    st.session_state["submitted"] = True
    st.session_state["submitted_for"] = question_id
    st.session_state["uploaded_filenames"] = uploaded_filenames
    st.rerun()


def _show_success_screen(filenames: list) -> None:
    st.balloons()
    st.success("## ✅ Submission received!")
    st.markdown(f"**{len(filenames)} file(s) uploaded:**")
    for f in filenames:
        st.markdown(f"- `{f}`")
    st.markdown("You may close this tab. Good luck! 🎉")

    if st.button("↩️ Submit again"):
        del st.session_state["submitted"]
        del st.session_state["submitted_for"]
        del st.session_state["uploaded_filenames"]
        st.rerun()
