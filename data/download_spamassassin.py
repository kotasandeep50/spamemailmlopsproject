"""Download a small public email corpus without changing the existing fallback dataset."""
from email import policy
from email.parser import BytesParser
from pathlib import Path
import argparse
import io
import tarfile
import urllib.request

CORPUS_URLS = {
    "ham": "https://spamassassin.apache.org/old/publiccorpus/20021010_easy_ham.tar.bz2",
    "spam": "https://spamassassin.apache.org/old/publiccorpus/20021010_spam.tar.bz2",
}


def message_text(raw_message: bytes) -> str:
    message = BytesParser(policy=policy.default).parsebytes(raw_message)
    subject = str(message.get("subject", "")).strip()
    body_parts = []

    def decoded_text(part) -> str:
        payload = part.get_payload(decode=True)
        if payload is None:
            return str(part.get_payload())
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except (LookupError, UnicodeError):
            return payload.decode("utf-8", errors="replace")

    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                body_parts.append(decoded_text(part))
    else:
        body_parts.append(decoded_text(message))
    body = "\n".join(str(part) for part in body_parts).strip()
    return f"Subject: {subject}\n\n{body}".strip() if subject else body


def download_archive(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/raw/spamassassin_emails.csv")
    parser.add_argument("--raw-output", default="data/raw/spamassassin_messages")
    args = parser.parse_args()
    rows = []
    for label, url in CORPUS_URLS.items():
        print(f"Downloading {label} corpus...")
        archive_bytes = download_archive(url)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:bz2") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                raw_message = archive.extractfile(member).read()
                text = message_text(raw_message)
                if text:
                    rows.append((text, 1 if label == "spam" else 0))
                    raw_directory = Path(args.raw_output) / label
                    raw_directory.mkdir(parents=True, exist_ok=True)
                    raw_name = Path(member.name).name or f"message-{len(rows)}"
                    (raw_directory / f"{raw_name}.eml").write_bytes(raw_message)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as file:
        file.write("text,label\n")
        for text, label in rows:
            escaped = text.replace('"', '""')
            file.write(f'"{escaped}",{label}\n')
    print(f"Saved {len(rows)} labeled emails to {output}")


if __name__ == "__main__":
    main()
