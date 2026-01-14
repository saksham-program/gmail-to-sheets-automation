from __future__ import annotations

import logging
from typing import Any, Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, SCOPES, TOKEN_FILE

logger = logging.getLogger(__name__)


class GmailService:
    """Gmail API wrapper: OAuth + unread Inbox fetching + marking read."""

    def __init__(self) -> None:
        self.creds = self._load_credentials()
        # cache_discovery=False avoids writing discovery docs to disk
        self.service = build("gmail", "v1", credentials=self.creds, cache_discovery=False)

    def _load_credentials(self) -> Credentials:
        creds: Credentials | None = None

        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing OAuth token...")
                creds.refresh(Request())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Missing OAuth client file: {CREDENTIALS_FILE}. "
                        "Download it from Google Cloud Console and place it there."
                    )

                logger.info("Starting OAuth desktop flow (browser login)...")
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)

            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            logger.info("Saved OAuth token to %s", TOKEN_FILE)

        return creds

    def list_unread_inbox_message_ids(self, max_results: int = 100) -> list[str]:
        """Return Gmail message IDs for unread emails in Inbox only."""
        query = "in:inbox is:unread"
        resp: dict[str, Any] = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = resp.get("messages", [])
        return [m["id"] for m in messages if "id" in m]

    def get_message(self, message_id: str) -> dict[str, Any]:
        """Fetch full Gmail message payload."""
        return (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

    def mark_as_read(self, message_id: str) -> None:
        """Remove the UNREAD label from message."""
        (
            self.service.users()
            .messages()
            .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )

    def mark_many_as_read(self, message_ids: Iterable[str]) -> None:
        ids = [mid for mid in message_ids]
        if not ids:
            return
        (
            self.service.users()
            .messages()
            .batchModify(
                userId="me",
                body={"ids": ids, "removeLabelIds": ["UNREAD"]},
            )
            .execute()
        )
