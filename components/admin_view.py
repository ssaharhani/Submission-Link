"""
admin_view.py
-------------
The instructor's control panel.

What the teacher sees:
  • Current Question ID (editable text field)
  • A big Open / Close toggle button
  • Live status readout
  • A direct link to the Drive folder

Authentication is handled in app.py before this component is called.
"""

import streamlit as st
from services import sheets_service


def render() -> None:
    """Render the full admin panel. Called from app.py after auth passes."""

    st.title("📋 Instructor Control Panel")
    st.markdown("---")

    # ── Ensure the sheet has a header row on first use ────────────────────────
    try:
        sheets_service.ensure_header_row()
    except Exception as e:
        st.error(f"⚠️ Could not connect to Google Sheets: {e}")
        st.stop()

    # ── Load current state from the sheet ────────────────────────────────────
    try:
        state = sheets_service.get_session_state()
    except Exception as e:
        st.error(f"⚠️ Could not read session state: {e}")
        st.stop()

    current_status = state["status"]
    current_q_id = state["question_id"]

    # ── Question ID input ─────────────────────────────────────────────────────
    st.subheader("1 · Set the Question ID")
    new_q_id = st.text_input(
        label="Question ID",
        value=current_q_id,
        placeholder="e.g. Q1, Bonus_Q2, Midterm_Q3",
        help="This becomes the prefix in every uploaded filename.",
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
            st.success(f"**Status: OPEN** — accepting submissions for `{current_q_id}`")
        else:
            st.warning(f"**Status: CLOSED** — submissions are disabled")

    st.markdown("---")

    # ── Quick-save button (if teacher only changed the question ID) ───────────
    st.subheader("3 · Save Question ID without toggling")
    if st.button("💾  Save Question ID", use_container_width=False):
        _save_state(current_status, new_q_id)
        st.success(f"Saved! Question ID is now `{new_q_id}` (status unchanged).")
        st.rerun()

    st.markdown("---")

    # ── Drive folder shortcut ─────────────────────────────────────────────────
    st.subheader("4 · View submitted files")
    folder_id = st.secrets["settings"].get("drive_folder_id", "")
    if folder_id:
        drive_url = f"https://drive.google.com/drive/folders/{folder_id}"
        st.markdown(f"[📂 Open Google Drive folder]({drive_url})")
    else:
        st.info("Set `drive_folder_id` in secrets.toml to see this link.")


# ── Private helpers ───────────────────────────────────────────────────────────

def _save_state(status: str, question_id: str) -> None:
    """Write state to Sheets with user-friendly error handling."""
    try:
        sheets_service.set_session_state(status, question_id)
    except Exception as e:
        st.error(f"⚠️ Could not save to Google Sheets: {e}")
        st.stop()
