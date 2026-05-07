"""
app.py
------
Entry point. Controls routing (admin vs student) and admin authentication.
Admin session lasts 10 minutes before requiring password again.
"""

import time
import streamlit as st
from components import admin_view, student_view

st.set_page_config(
    page_title="Solution Submission",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
)

ADMIN_SESSION_MINUTES = 10


def _is_admin_url() -> bool:
    return st.query_params.get("role", "").lower() == "admin"


def _admin_session_valid() -> bool:
    """Return True if admin logged in within the last 10 minutes."""
    login_time = st.session_state.get("admin_login_time", 0)
    return (time.time() - login_time) < (ADMIN_SESSION_MINUTES * 60)


def _check_admin_password() -> bool:
    if _admin_session_valid():
        return True

    with st.sidebar:
        st.header("🔐 Instructor Login")
        st.caption(f"Session lasts {ADMIN_SESSION_MINUTES} minutes.")
        password = st.text_input("Password", type="password", key="pw_input")
        if st.button("Login"):
            expected = st.secrets["settings"].get("admin_password", "")
            if password == expected:
                st.session_state["admin_login_time"] = time.time()
                st.rerun()
            else:
                st.error("Incorrect password.")

    return False


def main():
    if _is_admin_url():
        if _check_admin_password():
            admin_view.render()
        else:
            st.info("Enter your instructor password in the sidebar to continue.")
    else:
        student_view.render()


if __name__ == "__main__":
    main()
