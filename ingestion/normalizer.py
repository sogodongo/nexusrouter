import uuid
from datetime import datetime, timezone
from pydantic import BaseModel


class EventEnvelope(BaseModel):
    event_id:        str
    source:          str
    raw_payload:     dict
    normalized_text: str
    sender:          str
    subject:         str
    received_at:     str
    attachments:     list[str] = []

    @classmethod
    def from_gmail(cls, gmail_message: dict) -> "EventEnvelope":
        """
        Converts a raw Gmail API message object into a standard EventEnvelope.
        Gmail's message format is deeply nested — this flattens it into
        something the classifier can work with directly.
        """
        headers = {
            h["name"].lower(): h["value"]
            for h in gmail_message.get("payload", {}).get("headers", [])
        }

        body = _extract_gmail_body(gmail_message.get("payload", {}))
        attachments = _extract_attachment_names(gmail_message.get("payload", {}))

        # Build the normalized text the classifier will read —
        # subject + body gives the most signal for intent classification
        subject = headers.get("subject", "")
        sender  = headers.get("from", "")
        normalized_text = f"Subject: {subject}\n\nFrom: {sender}\n\n{body}".strip()

        return cls(
            event_id=        gmail_message.get("id", str(uuid.uuid4())),
            source=          "gmail",
            raw_payload=     gmail_message,
            normalized_text= normalized_text,
            sender=          sender,
            subject=         subject,
            received_at=     datetime.now(timezone.utc).isoformat(),
            attachments=     attachments,
        )


def _extract_gmail_body(payload: dict) -> str:
    """
    Recursively extracts plain text from Gmail's MIME payload structure.
    Gmail nests multipart messages — we walk the tree until we find text/plain.
    """
    import base64

    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")

    # Walk multipart structure recursively
    for part in payload.get("parts", []):
        result = _extract_gmail_body(part)
        if result:
            return result

    return ""


def _extract_attachment_names(payload: dict) -> list[str]:
    """Returns filenames of any attachments in the message."""
    names = []
    for part in payload.get("parts", []):
        filename = part.get("filename", "")
        if filename:
            names.append(filename)
        names.extend(_extract_attachment_names(part))
    return names
