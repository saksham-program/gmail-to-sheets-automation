from __future__ import annotations

import logging
from typing import Sequence

from googleapiclient.discovery import build

from config import SHEET_NAME, SPREADSHEET_ID

logger = logging.getLogger(__name__)


class SheetsService:
    """Google Sheets API wrapper for appending rows."""

    def __init__(self, creds) -> None:
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    def append_rows(self, rows: Sequence[Sequence[str]]) -> int:
        """Append rows to the configured sheet. Returns number of appended rows."""
        if not rows:
            return 0

        # Append into the given sheet tab, starting at column A.
        range_name = f"{SHEET_NAME}!A:D"
        body = {"values": [list(r) for r in rows]}

        result = (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

        updates = result.get("updates", {})
        updated_rows = updates.get("updatedRows", 0)
        logger.info("Appended %s row(s) to Google Sheets", updated_rows)
        return int(updated_rows)
