from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Union
from pathlib import Path
from io import BytesIO, BufferedIOBase
from scapy.all import PcapReader, DNS, IP, UDP

def is_dns_packet(pkt) -> bool:
    return pkt.haslayer(UDP) and pkt.haslayer(DNS) and (
        pkt[UDP].sport == 53 or pkt[UDP].dport == 53
    )


def _decode_name(val):
    if val is None:
        return None
    if isinstance(val, (bytes, bytearray)):
        return val.decode(errors="ignore")
    return str(val)


def parse_dns_layer(dns) -> Dict[str, Any]:
    """Parse a scapy DNS layer (questions + answers) safely."""
    questions: List[Dict[str, Any]] = []
    answers: List[Dict[str, Any]] = []

    # Questions (qd can be None / single / list)
    qd = getattr(dns, "qd", None)
    if qd:
        qds = qd if isinstance(qd, list) else [qd]
        for q in qds:
            try:
                questions.append(
                    {
                        "qname": _decode_name(getattr(q, "qname", None)),
                        "qtype": getattr(q, "qtype", None),
                        "qclass": getattr(q, "qclass", None),
                    }
                )
            except Exception:
                continue  # skip malformed entries

    # Answers (an can be None / single / list)
    an = getattr(dns, "an", None)
    if an:
        ans_list = an if isinstance(an, list) else [an]
        for ans in ans_list:
            try:
                ans_type = getattr(ans, "type", None)
                raw_rdata = getattr(ans, "rdata", None)

                if ans_type in (1, 28):  # A, AAAA
                    rdata = raw_rdata
                elif ans_type in (2, 5, 12):  # NS, CNAME, PTR
                    rdata = _decode_name(raw_rdata)
                elif ans_type == 16:  # TXT
                    if isinstance(raw_rdata, list):
                        rdata = b"".join(raw_rdata).decode(errors="ignore")
                    elif isinstance(raw_rdata, (bytes, bytearray)):
                        rdata = raw_rdata.decode(errors="ignore")
                    else:
                        rdata = _decode_name(raw_rdata)
                else:
                    rdata = _decode_name(raw_rdata)

                answers.append(
                    {
                        "rrname": _decode_name(getattr(ans, "rrname", None)),
                        "rtype": ans_type,
                        "rclass": getattr(ans, "rclass", None),
                        "ttl": getattr(ans, "ttl", None),
                        "rdata": rdata,
                    }
                )
            except Exception:
                continue

    return {
        "id": getattr(dns, "id", None),
        "qr": getattr(dns, "qr", None),
        "opcode": getattr(dns, "opcode", None),
        "rcode": getattr(dns, "rcode", None),
        "qdcount": getattr(dns, "qdcount", None),
        "ancount": getattr(dns, "ancount", None),
        "questions": questions,
        "answers": answers,
    }


def parse_pcap(local_path_or_bytes: Union[str, Path, bytes, BufferedIOBase]) -> List[Dict[str, Any]]:
    """
    Stream-parse a PCAP from a file path, bytes, or in-memory file-like object.
    """
    out: List[Dict[str, Any]] = []

    if isinstance(local_path_or_bytes, (str, Path)):
        reader_source = local_path_or_bytes
    elif isinstance(local_path_or_bytes, bytes):
        reader_source = BytesIO(local_path_or_bytes)
    elif isinstance(local_path_or_bytes, BufferedIOBase):  # ← add this check
        reader_source = local_path_or_bytes
    else:
        raise TypeError("Input must be a file path (str/Path), bytes, or a file-like object")

    with PcapReader(reader_source) as pr:
        for pkt in pr:
            try:
                if not (pkt.haslayer(IP) and is_dns_packet(pkt)):
                    continue

                dns = pkt[DNS]
                parsed = parse_dns_layer(dns)

                if parsed.get("qr") == 0 and not parsed.get("questions"):
                    continue

                ip = pkt[IP]
                udp = pkt[UDP]

                out.append(
                    {
                        "timestamp": datetime.utcfromtimestamp(float(pkt.time)).isoformat(),
                        "src_ip": ip.src,
                        "dst_ip": ip.dst,
                        "src_port": int(udp.sport),
                        "dst_port": int(udp.dport),
                        **parsed,
                    }
                )
            except Exception:
                continue

    return out

