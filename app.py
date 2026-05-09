"""
app.py
------
Entry point. Controls routing (admin vs student) and admin authentication.
"""

import streamlit as st
from components import admin_view, student_view

st.set_page_config(
    page_title="Solution Submission",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="auto",
)

def _is_admin_url() -> bool:
    return st.query_params.get("role", "").lower() == "admin"


def _check_admin_password() -> bool:
    """Password required once per browser session — no timeout."""
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
