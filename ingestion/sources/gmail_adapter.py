import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ingestion.normalizer import EventEnvelope

# Only read access — we never modify emails
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def _get_gmail_service():
    """
    Handles OAuth2 authentication with Gmail.
    On first run opens a browser for authorization and saves the token.
    On subsequent runs loads the saved token — no browser needed.
    """
    creds = None

    if Path(TOKEN_FILE).exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # WSL2 can't open a browser directly — print the URL
            # for the user to open manually in Windows browser
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")
            print(f"\nOpen this URL in your browser:\n{auth_url}\n")
            code = input("Paste the authorization code here: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("gmail", "v1", credentials=creds)


def fetch_recent_emails(max_results: int = 10) -> list[EventEnvelope]:
    """
    Fetches the most recent emails from the Gmail inbox and returns
    them as normalized EventEnvelope objects.

    max_results is intentionally small — in production we'd use
    Gmail push notifications (Pub/Sub) instead of polling.
    """
    service = _get_gmail_service()

    print(f"[gmail] Fetching up to {max_results} recent emails...")
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        labelIds=["INBOX"],
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("[gmail] No messages found.")
        return []

    envelopes = []
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()
        envelope = EventEnvelope.from_gmail(msg)
        envelopes.append(envelope)

    print(f"[gmail] Fetched and normalized {len(envelopes)} emails.")
    return envelopes
