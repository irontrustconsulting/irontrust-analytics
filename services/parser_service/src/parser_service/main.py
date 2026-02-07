
from __future__ import annotations

import io
import os
import re
import json
import gzip
import logging
from typing import Tuple, List, Dict, Any
from urllib.parse import unquote_plus

import boto3
import botocore

import tempfile

# Your parser from libs/parsers
# Adjust the import if your module file is named differently
from parsers.parser import parse_pcap

# -------------------- Logging --------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger("parser_service")

# -------------------- Environment --------------------
# Required at runtime (either EVENT_JSON, or SOURCE_BUCKET + OBJECT_KEY)
SOURCE_BUCKET = os.getenv("SOURCE_BUCKET")
OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET")
OBJECT_KEY = os.getenv("OBJECT_KEY")                # input object key when not using EVENT_JSON
EVENT_JSON = os.getenv("EVENT_JSON")                # alternative: '{"bucket":"...","key":"..."}'

# Optional
AWS_REGION = os.getenv("AWS_REGION")                # use default provider chain if not set
OUTPUT_PREFIX = os.getenv("OUTPUT_PREFIX", "")      # if set, prepended after tenant_id
# If your tenant_id is always the first path segment ("<tenant_id>/..."), leave this at 0.
TENANT_SEGMENT_INDEX = int(os.getenv("TENANT_SEGMENT_INDEX", "0"))

# Spooled file limit (MiB) before spilling to /tmp
SPOOL_MAX_MB = int(os.getenv("SPOOL_MAX_MB", "100"))
SPOOL_MAX_SIZE = SPOOL_MAX_MB * 1024 * 1024


# -------------------- Helpers --------------------
def _normalize_key(key: str) -> str:
    """
    Normalize S3 key: URL-decode and strip leading slashes.
    EventBridge S3 events often provide URL-encoded keys.
    """
    key = unquote_plus(key or "")
    return key.lstrip("/")


def _resolve_event() -> Tuple[str, str]:
    """
    Resolve the (bucket, key) we should process.
    Priority:
      1) EVENT_JSON='{"bucket":"...","key":"..."}'
      2) SOURCE_BUCKET + OBJECT_KEY
    """
    if EVENT_JSON:
        try:
            evt = json.loads(EVENT_JSON)
            bucket = evt["bucket"]
            key = _normalize_key(evt["key"])
            return bucket, key
        except Exception as e:
            raise SystemExit(f"Invalid EVENT_JSON: {e}")

    if not SOURCE_BUCKET or not OBJECT_KEY:
        raise SystemExit(
            "Missing input. Provide EVENT_JSON='{\"bucket\":\"...\",\"key\":\"...\"}' "
            "or set SOURCE_BUCKET and OBJECT_KEY."
        )
    return SOURCE_BUCKET, _normalize_key(OBJECT_KEY)


def _extract_tenant_and_rest(key: str, segment_index: int = 0) -> Tuple[str, str]:
    """
    Given a key like: 'acme/pcaps/2026-01-22/file.pcap'
    Return ('acme', 'pcaps/2026-01-22/file.pcap') when segment_index=0.
    """
    parts = [p for p in key.split("/") if p != ""]
    if len(parts) <= segment_index:
        raise SystemExit(
            f"Cannot extract tenant_id from key '{key}' at segment_index={segment_index}"
        )
    tenant_id = parts[segment_index]
    rest = "/".join(parts[segment_index + 1 :])
    if not rest:
        # There is no file path after tenant_id; we need at least a filename
        raise SystemExit(f"Key '{key}' does not contain a file path after tenant_id='{tenant_id}'")
    return tenant_id, rest


def _swap_ext_to_jsonl_gz(path: str) -> str:
    """
    Replace .pcap/.pcapng with .jsonl.gz (case-insensitive).
    If no known extension, just append .jsonl.gz
    """
    m = re.search(r"\.(pcap|pcapng)$", path, flags=re.IGNORECASE)
    if m:
        return re.sub(r"\.(pcap|pcapng)$", ".jsonl.gz", path, flags=re.IGNORECASE)
    return f"{path}.jsonl.gz"


def _derive_output_key(input_key: str) -> Tuple[str, str]:
    """
    Build output path: s3://OUTPUT_BUCKET/<tenant_id>/<OUTPUT_PREFIX?>/<rest>.jsonl.gz

    Examples:
      input_key='acme/pcaps/2026-01-22/file.pcap', OUTPUT_PREFIX=''  ->
          'acme/pcaps/2026-01-22/file.jsonl.gz'
      input_key='acme/pcaps/2026-01-22/file.pcap', OUTPUT_PREFIX='bronze/pcap' ->
          'acme/bronze/pcap/pcaps/2026-01-22/file.jsonl.gz'
    """
    key = _normalize_key(input_key)
    tenant_id, rest = _extract_tenant_and_rest(key, TENANT_SEGMENT_INDEX)

    # Where to put the file under the tenant folder
    # If you want strictly `/<tenant_id>/<rest>.jsonl.gz` set OUTPUT_PREFIX=""
    # If you want `/<tenant_id>/bronze/pcap/<rest>.jsonl.gz`, set OUTPUT_PREFIX="bronze/pcap"
    pieces = [tenant_id]
    if OUTPUT_PREFIX:
        pieces.append(OUTPUT_PREFIX.strip("/"))
    pieces.append(_swap_ext_to_jsonl_gz(rest))
    out_key = "/".join(pieces)
    return tenant_id, out_key




def _stream_pcap_to_mem(s3, bucket: str, key: str) -> io.BufferedIOBase:
    """
    Download S3 object into a spooled temp file:
    - Stays in memory up to SPOOL_MAX_SIZE, then spills to /tmp.
    - Returns a *buffered* file-like object so isinstance(..., BufferedIOBase) passes.
    """
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
    except botocore.exceptions.ClientError as e:
        raise SystemExit(f"Failed to get s3://{bucket}/{key}: {e}")

    body = resp["Body"]  # botocore.response.StreamingBody
    spooled: tempfile.SpooledTemporaryFile = tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_SIZE)
    for chunk in iter(lambda: body.read(1024 * 1024), b""):  # 1 MiB chunks
        spooled.write(chunk)
    spooled.seek(0)

    # 🔑 The key change: wrap the spooled file so it passes your BufferedIOBase isinstance check
    return io.BufferedReader(spooled, buffer_size=1024 * 1024)





def _upload_jsonl_gz(
    s3, bucket: str, key: str, records: list[dict[str, any]]
) -> dict[str, any]:
    """
    Stream JSONL into a gzip buffer and upload to S3 using fileobj (no temp file needed).
    Compute size before upload because upload_fileobj may close the buffer.
    """
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        for rec in records:
            line = json.dumps(rec, default=str, separators=(",", ":")).encode("utf-8")
            gz.write(line + b"\n")

    # Compute size BEFORE upload (and rewind)
    size_bytes = buf.tell()       # current position = end
    buf.seek(0)

    s3.upload_fileobj(
        Fileobj=buf,
        Bucket=bucket,
        Key=key,
        ExtraArgs={"ContentType": "application/gzip", "ContentEncoding": "gzip"},
    )
    return {"bucket": bucket, "key": key, "size_bytes": size_bytes}



# -------------------- Main --------------------
def main() -> Dict[str, Any]:
    if not OUTPUT_BUCKET:
        raise SystemExit("OUTPUT_BUCKET is required")

    in_bucket, in_key = _resolve_event()
    log.info("Processing input: s3://%s/%s", in_bucket, in_key)

    s3 = boto3.client("s3", region_name=AWS_REGION) if AWS_REGION else boto3.client("s3")

    # 1) Read PCAP to a seekable in-memory file object
    pcap_obj = _stream_pcap_to_mem(s3, in_bucket, in_key)

    # 2) Parse (your parser handles file-like objects)
    records = parse_pcap(pcap_obj)
    count = len(records)
    log.info("Parsed %d records", count)

    # 3) Build tenant-aware output key and upload
    tenant_id, out_key = _derive_output_key(in_key)
    put_info = _upload_jsonl_gz(s3, OUTPUT_BUCKET, out_key, records)
    log.info("Wrote output: s3://%s/%s", put_info["bucket"], put_info["key"])

    return {
        "tenant_id": tenant_id,
        "input": {"bucket": in_bucket, "key": in_key},
        "output": put_info,
        "count": count,
    }


if __name__ == "__main__":
    res = main()
    print(json.dumps(res))
