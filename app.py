"""
app.py
------
Entry point for the Streamlit application.

Routing logic:
  • ?role=admin in the URL  → show password prompt → admin panel
  • Any other URL           → student submission form

This file stays intentionally thin. All logic lives in the components
and services so the teacher can modify any piece without touching this file.

Run locally:  streamlit run app.py
"""

import streamlit as st
from components import admin_view, student_view

# ── Page config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="Solution Submission",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
)


def _is_admin_url() -> bool:
    """Return True if ?role=admin is present in the query string."""
    params = st.query_params
    return params.get("role", "").lower() == "admin"


def _check_admin_password() -> bool:
    """
    Show a sidebar password prompt.
    Returns True if the correct password has been entered this session.
    """
    if st.session_state.get("admin_authenticated"):
        return True

    with st.sidebar:
        st.header("🔐 Instructor Login")
        password = st.text_input("Password", type="password", key="pw_input")
        if st.button("Login"):
            expected = st.secrets["settings"].get("admin_password", "")
            if password == expected:
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")

    return False


# ── Main routing ──────────────────────────────────────────────────────────────

def main():
    if _is_admin_url():
        # Admin route: require password, then show control panel
        if _check_admin_password():
            admin_view.render()
        else:
            st.info("Enter your instructor password in the sidebar to continue.")
    else:
        # Student route: no authentication required
        student_view.render()


if __name__ == "__main__":
    main()
