"""
student_view.py
---------------
Student submission form.

- Multiple photos supported (uploaded sequentially with a small delay)
- Blocks re-submission by student ID for the same question
- No re-submit button — one submission per student per question
"""

import time
import streamlit as st
from services import sheets_service, drive_service, image_utils


def render() -> None:
    st.title("📸 Submit Your Solution")

    _, refresh_col = st.columns([5, 1])
    with refresh_col:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        state = sheets_service.get_session_state()
    except Exception as e:
        st.error(f"⚠️ Could not reach the server. Please refresh.\n\n`{e}`")
        st.stop()

    status      = state["status"]
    question_id = state["question_id"]

    # ── Closed ────────────────────────────────────────────────────────────────
    if status != "Open":
        st.info("⏳ **Submissions are currently closed.**\n\nWait for your instructor, then tap 🔄 Refresh.")
        return

    st.success(f"✅ Session is **OPEN** — submitting for: `{question_id}`")
    st.markdown("---")

    # ── Already submitted ─────────────────────────────────────────────────────
    if (st.session_state.get("submitted")
            and st.session_state.get("submitted_for") == question_id):
        _show_success_screen(st.session_state["uploaded_filenames"])
        return

    # ── Form ──────────────────────────────────────────────────────────────────
    with st.form("submission_form", clear_on_submit=False):
        student_name = st.text_input("Full Name", placeholder="e.g. Ali Hassan", max_chars=60)
        student_id   = st.text_input("Student ID", placeholder="e.g. 202312345", max_chars=20)
        photos = st.file_uploader(
            "Upload photo(s) of your solution",
            type=["jpg", "jpeg", "png", "heic"],
            accept_multiple_files=True,
            help="You can select multiple photos.",
        )
        submitted = st.form_submit_button("📤  Submit", use_container_width=True)

    if submitted:
        _handle_submission(question_id, student_name, student_id, photos)


def _handle_submission(question_id, student_name, student_id, photos) -> None:
    # ── Validate ──────────────────────────────────────────────────────────────
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

    # ── Duplicate check ───────────────────────────────────────────────────────
    try:
        existing = sheets_service.get_student_submissions(question_id)
        if student_id.strip() in existing:
            st.warning("⚠️ You already submitted for this question. Contact your instructor if there's an issue.")
            return
    except Exception:
        pass  # If check fails, allow submission rather than block

    # ── Upload photos one by one ──────────────────────────────────────────────
    uploaded_filenames = []
    progress = st.progress(0, text="Starting upload…")

    for i, photo in enumerate(photos, start=1):
        progress.progress(int((i - 1) / len(photos) * 100), text=f"Uploading photo {i} of {len(photos)}…")

        # Suffix only when multiple photos: Ali_202312345_1, Ali_202312345_2
        id_with_suffix = f"{student_id.strip()}_{i}" if len(photos) > 1 else student_id.strip()

        try:
            raw_bytes  = photo.read()
            compressed = image_utils.compress_image(raw_bytes)
            drive_service.upload_image(
                image_bytes=compressed,
                question_id=question_id,
                student_name=student_name,
                student_id=id_with_suffix,
            )
            filename = drive_service.build_filename(question_id, student_name, id_with_suffix)
            uploaded_filenames.append(filename)
        except Exception as e:
            st.error(f"❌ Photo {i} failed: {e}")
            return

        # Small delay between uploads to avoid hammering the API
        if i < len(photos):
            time.sleep(0.5)

    progress.progress(100, text="Done!")

    # ── Log and confirm ───────────────────────────────────────────────────────
    sheets_service.log_student_submission(question_id, student_id.strip())
    st.session_state["submitted"]         = True
    st.session_state["submitted_for"]     = question_id
    st.session_state["uploaded_filenames"] = uploaded_filenames
    st.rerun()


def _show_success_screen(filenames: list) -> None:
    st.balloons()
    st.success("## ✅ Submission received!")
    st.markdown(f"**{len(filenames)} file(s) uploaded:**")
    for f in filenames:
        st.markdown(f"- `{f}`")
    st.markdown("You may close this tab. Good luck! 🎉")
