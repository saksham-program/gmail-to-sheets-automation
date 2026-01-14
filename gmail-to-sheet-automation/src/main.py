from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import GMAIL_MAX_RESULTS, LOG_LEVEL, STATE_FILE
from src.email_parser import parse_gmail_message
from src.gmail_service import GmailService
from src.sheets_service import SheetsService


def _setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"processed_message_ids": [], "updated_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # If state is corrupted, fail safe (do not reprocess blindly)
        raise RuntimeError(
            f"State file {path} is not valid JSON. Fix/delete it to continue."
        )


def _save_state(path: Path, processed_ids: set[str]) -> None:
    payload = {
        "processed_message_ids": sorted(processed_ids),
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run() -> int:
    _setup_logging()
    logger = logging.getLogger("gmail-to-sheets")

    state = _load_state(STATE_FILE)
    processed_ids: set[str] = set(state.get("processed_message_ids", []))

    gmail = GmailService()
    sheets = SheetsService(gmail.creds)

    unread_ids = gmail.list_unread_inbox_message_ids(max_results=GMAIL_MAX_RESULTS)
    logger.info("Found %d unread Inbox message(s)", len(unread_ids))

    new_ids = [mid for mid in unread_ids if mid not in processed_ids]
    logger.info("%d message(s) are new (not in state)", len(new_ids))

    rows: list[list[str]] = []
    successfully_processed: list[str] = []

    for mid in new_ids:
        try:
            msg = gmail.get_message(mid)
            parsed = parse_gmail_message(msg)

            # Columns: timestamp_utc, from, subject, body
            rows.append([parsed.timestamp_utc, parsed.sender, parsed.subject, parsed.body])
            successfully_processed.append(mid)
        except Exception as e:
            logger.exception("Failed to process message %s: %s", mid, e)

    if rows:
        sheets.append_rows(rows)

    # Mark as read ONLY the emails we successfully appended.
    if successfully_processed:
        gmail.mark_many_as_read(successfully_processed)
        logger.info("Marked %d message(s) as read", len(successfully_processed))

        processed_ids.update(successfully_processed)
        _save_state(STATE_FILE, processed_ids)
        logger.info("Updated state file: %s", STATE_FILE)

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
