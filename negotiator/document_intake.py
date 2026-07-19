"""
Document intake (owner: Jagger) -- one of the two required intake paths (Section 5,
"Intake by Interview or Documents"). Parses a document -- an existing quote, a bill, an
inventory list, or a photo of one -- into plain text; `estimator.estimate_from_document()`
then runs that text through the exact same pipeline as text/voice intake.

Text-like documents (pasted quotes, .txt/.csv/.md) need no keys and work in the demo
today. Photo intake needs Claude vision (ANTHROPIC_API_KEY): transcribing a photo
without an actual vision call would mean fabricating its contents -- exactly the kind
of invented-inventory dishonesty the whole system is built to refuse, so we raise
instead of guessing.
"""
from __future__ import annotations

import base64
import csv
import io
import os
from typing import Union

_IMAGE_MEDIA_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def parse_document(content: Union[str, bytes], filename: str, document_type: str = "other") -> str:
    """
    Return plain text extracted from a document, ready for the Estimator's shared
    extraction pipeline. `document_type` (e.g. "quote", "bill", "inventory_list",
    "photo") labels the upload for the demo/UI; extraction itself is driven by the
    file extension.
    """
    ext = _extension(filename)
    if ext == ".csv":
        return _parse_csv(content)
    if ext in _IMAGE_MEDIA_TYPES:
        return _parse_image(content, ext)
    return content.decode() if isinstance(content, bytes) else str(content)


def _extension(filename: str) -> str:
    _, _, ext = filename.rpartition(".")
    return f".{ext.lower()}" if ext else ""


def _parse_csv(content: Union[str, bytes]) -> str:
    text = content.decode() if isinstance(content, bytes) else content
    reader = csv.DictReader(io.StringIO(text))
    rows = [", ".join(f"{k}: {v}" for k, v in row.items() if v) for row in reader]
    return "\n".join(rows)


def _parse_image(content: Union[str, bytes], ext: str) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Photo intake needs ANTHROPIC_API_KEY (Claude vision transcribes the "
            "image's visible pricing/terms into text before the Estimator parses it). "
            "Without a key this refuses to guess at a photo's contents -- use a "
            "text/CSV document, or the voice/text path, instead."
        )
    import anthropic

    image_bytes = content if isinstance(content, bytes) else content.encode()
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": _IMAGE_MEDIA_TYPES[ext],
                        "data": base64.b64encode(image_bytes).decode(),
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Transcribe every price, quantity, material spec, lead time, "
                        "and payment term visible in this image as plain text. Do not "
                        "invent anything not actually visible."
                    ),
                },
            ],
        }],
    )
    return "".join(block.text for block in message.content if block.type == "text")
