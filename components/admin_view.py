"""
admin_view.py
-------------
Instructor control panel.
- Session auto-closes after 15 minutes
- Shows countdown timer
- Status always starts Closed on first load
"""

import time
import streamlit as st
from services import sheets_service

AUTO_CLOSE_MINUTES = 15


def render() -> None:
    st.title("📋 Instructor Control Panel")
    st.markdown("---")

    try:
        sheets_service.ensure_header_row()
    except Exception as e:
        st.error(f"⚠️ Could not connect to Google Sheets: {e}")
        st.stop()

    try:
        state = sheets_service.get_session_state()
    except Exception as e:
        st.error(f"⚠️ Could not read session state: {e}")
        st.stop()

    current_status = state["status"]
    current_q_id = state["question_id"]
    opened_at = state.get("opened_at", 0)

    # ── Question ID ───────────────────────────────────────────────────────────
    st.subheader("1 · Set the Question ID")
    new_q_id = st.text_input(
        label="Question ID",
        value=current_q_id,
        placeholder="e.g. Q1, Bonus_Q2, Midterm_Q3",
    )

    st.markdown("---")

    # ── Status toggle ─────────────────────────────────────────────────────────
    st.subheader("2 · Open or Close Submissions")
    is_open = current_status == "Open"

    col1, col2 = st.columns([1, 2])
    with col1:
        if is_open:
            if st.button("🔴  CLOSE submissions", use_container_width=True):
                _save_state("Closed", new_q_id)
                st.rerun()
        else:
            if st.button("🟢  OPEN submissions", use_container_width=True):
                _save_state("Open", new_q_id)
                st.rerun()

    with col2:
        if is_open:
            # Show countdown
            if opened_at:
                elapsed = (time.time() - opened_at) / 60
                remaining = max(0, AUTO_CLOSE_MINUTES - elapsed)
                mins = int(remaining)
                secs = int((remaining - mins) * 60)
                st.success(f"**OPEN** — `{current_q_id}` — auto-closes in **{mins}m {secs}s**")
            else:
                st.success(f"**Status: OPEN** — accepting submissions for `{current_q_id}`")
        else:
            st.warning("**Status: CLOSED** — submissions are disabled")

    st.markdown("---")

    # ── Save question ID only ─────────────────────────────────────────────────
    st.subheader("3 · Save Question ID without toggling")
    if st.button("💾  Save Question ID"):
        _save_state(current_status, new_q_id)
        st.success(f"Saved! Question ID is now `{new_q_id}`")
        st.rerun()

    st.markdown("---")

    # ── Storage links ─────────────────────────────────────────────────────────
    st.subheader("4 · View submitted files")
    supabase_url = st.secrets["settings"].get("supabase_url", "")
    bucket = st.secrets["settings"].get("supabase_bucket", "submissions")
    if supabase_url:
        st.markdown(f"[📦 Open Supabase Storage]({supabase_url}/project/default/storage/buckets/{bucket})")

    webhook_url = st.secrets["settings"].get("webhook_url", "")
    if webhook_url:
        st.markdown("[📂 Open Google Drive folder](https://drive.google.com)")

    # ── Auto-refresh while open ───────────────────────────────────────────────
    if is_open:
        time.sleep(1)
        st.rerun()


def _save_state(status: str, question_id: str) -> None:
    try:
        sheets_service.set_session_state(status, question_id)
    except Exception as e:
        st.error(f"⚠️ Could not save: {e}")
        st.stop()
