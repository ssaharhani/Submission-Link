"""
sheets_service.py
-----------------
All communication with the Google Sheet "control plane."

The sheet must have exactly one data row (row 2) with two columns:
  A: Status       → "Open" or "Closed"
  B: Question_ID  → e.g. "Q1", "Bonus_Q1"

The teacher never touches this file; he only configures secrets.toml.
"""

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

# Scopes required for Sheets read/write
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # needed by gspread internally
]

# Row / column positions in the sheet (1-indexed)
STATUS_COL = 1       # Column A
QUESTION_COL = 2     # Column B
DATA_ROW = 2         # Row 1 is the header; row 2 is the live data row


@st.cache_resource(ttl=0)   # Resource cached once; we bypass cache by calling directly
def _get_client() -> gspread.Client:
    """Build and return an authenticated gspread client."""
    creds_dict = dict(st.secrets["google_credentials"])
    # gspread expects a plain dict, not Streamlit's AttrDict
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_worksheet() -> gspread.Worksheet:
    """Open the control sheet and return the first worksheet."""
    client = _get_client()
    sheet_url = st.secrets["settings"]["sheet_url"]
    spreadsheet = client.open_by_url(sheet_url)
    return spreadsheet.sheet1


# ── Public API ────────────────────────────────────────────────────────────────

def get_session_state() -> dict:
    """
    Returns the current session state as a dict:
        {"status": "Open" | "Closed", "question_id": str}
    Raises an exception if the sheet cannot be read.
    """
    ws = _get_worksheet()
    row = ws.row_values(DATA_ROW)

    # Provide safe defaults if the row is empty or incomplete
    status = row[STATUS_COL - 1] if len(row) >= STATUS_COL else "Closed"
    question_id = row[QUESTION_COL - 1] if len(row) >= QUESTION_COL else "Q1"

    return {"status": status, "question_id": question_id}


def set_session_state(status: str, question_id: str) -> None:
    """
    Writes both control values back to the sheet in one batch update.
    Called only from the admin view.
    """
    ws = _get_worksheet()
    ws.update(f"A{DATA_ROW}:B{DATA_ROW}", [[status, question_id]])


def ensure_header_row() -> None:
    """
    Creates the header row if the sheet is brand new.
    Safe to call on every admin load.
    """
    ws = _get_worksheet()
    if ws.cell(1, 1).value != "Status":
        ws.update("A1:B1", [["Status", "Question_ID"]])
        ws.update(f"A{DATA_ROW}:B{DATA_ROW}", [["Closed", "Q1"]])
