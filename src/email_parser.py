from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedEmail:
    message_id: str
    sender: str
    subject: str
    # ISO-8601 UTC string
    timestamp_utc: str
    body: str


def _get_header(headers: list[dict[str, str]], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _decode_base64url(data: str) -> str:
    if not data:
        return ""
    # Gmail uses base64url without padding
    missing_padding = (-len(data)) % 4
    if missing_padding:
        data += "=" * missing_padding
    decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
    return decoded.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    """Simple, dependency-free HTML -> text conversion."""
    if not html:
        return ""

    text = unescape(html)
    # Remove script/style blocks
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", "", text)
    # Replace <br> and block tags with newlines
    text = re.sub(r"(?i)<br\\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|tr|li|h\\d)>", "\n", text)
    # Remove all remaining tags
    text = re.sub(r"(?s)<.*?>", "", text)
    # Normalize whitespace
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_text_from_payload(payload: dict[str, Any]) -> tuple[str, str]:
    """Return (plain_text, html_text) best-effort from Gmail payload."""
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}

    if mime_type == "text/plain":
        return _decode_base64url(body.get("data", "")), ""
    if mime_type == "text/html":
        return "", _decode_base64url(body.get("data", ""))

    plain_acc: list[str] = []
    html_acc: list[str] = []

    for part in payload.get("parts", []) or []:
        p, h = _extract_text_from_payload(part)
        if p:
            plain_acc.append(p)
        if h:
            html_acc.append(h)

    return "\n".join(plain_acc).strip(), "\n".join(html_acc).strip()


def parse_gmail_message(message: dict[str, Any]) -> ParsedEmail:
    message_id = message.get("id", "")
    payload = message.get("payload", {}) or {}
    headers = payload.get("headers", []) or []

    sender = _get_header(headers, "From")
    subject = _get_header(headers, "Subject")
    date_hdr = _get_header(headers, "Date")

    # Prefer RFC 2822 Date header; fallback to internalDate (ms since epoch)
    ts = None
    if date_hdr:
        try:
            ts = parsedate_to_datetime(date_hdr)
        except Exception:
            ts = None

    if ts is None:
        internal_ms = message.get("internalDate")
        try:
            ts = datetime.fromtimestamp(int(internal_ms) / 1000, tz=timezone.utc)
        except Exception:
            ts = datetime.now(tz=timezone.utc)

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    ts_utc = ts.astimezone(timezone.utc).isoformat()

    plain, html = _extract_text_from_payload(payload)
    body = plain.strip() if plain.strip() else _strip_html(html)

    # Sheets-friendly: avoid extremely large cells
    max_len = 50000
    if len(body) > max_len:
        body = body[: max_len - 50] + "\n\n[truncated]"

    return ParsedEmail(
        message_id=message_id,
        sender=sender,
        subject=subject,
        timestamp_utc=ts_utc,
        body=body,
    )
