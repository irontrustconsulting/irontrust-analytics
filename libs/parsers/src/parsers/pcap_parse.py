from __future__ import annotations
from .parser import parse_pcap
from .downloader import temp_download, temp_download_in_memory

def parse_pcap_uri(uri: str, in_memory: bool = False):
    """
    Parse PCAP from URI, optionally in-memory.
    """
    if in_memory:
        with temp_download_in_memory(uri) as f:
            return parse_pcap(f)
    else:
        with temp_download(uri, suffix=".pcap") as local_path:
            return parse_pcap(str(local_path))

