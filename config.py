"""Project configuration.

Fill in SPREADSHEET_ID (and optionally SHEET_NAME) before running.
"""

from __future__ import annotations

from pathlib import Path

# --- Google API OAuth ---
# credentials/credentials.json: OAuth client secret downloaded from Google Cloud Console
CREDENTIALS_FILE: Path = Path("credentials") / "credentials.json"

# credentials/token.json: Cached OAuth tokens generated after first login
TOKEN_FILE: Path = Path("credentials") / "token.json"

# --- Persistent state (duplicate prevention) ---
# Stored in project root for transparency & easy evaluation.
STATE_FILE: Path = Path("state.json")

# --- Gmail / Sheets settings ---
# IMPORTANT: Replace with your real spreadsheet ID before running.
SPREADSHEET_ID: str = "your_spreadsheet_id_here"

# Target tab name. If it doesn't exist, Google Sheets API will error.
SHEET_NAME: str = "Name of Your Sheet Tab"

# How many unread messages to fetch per run (safety limit)
GMAIL_MAX_RESULTS: int = 100

# --- OAuth scopes ---
# Gmail: read + modify (to mark processed emails as read)
# Sheets: append rows
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]

# --- Logging ---
LOG_LEVEL: str = "INFO"
