
from scapy.all import rdpcap, IP, TCP, UDP, DNS, DNSQR, Raw
import json
import socket
import os
import sys
from datetime import datetime

IANA_PROTOCOLS = {
    1: "ICMP",
    2: "IGMP",
    6: "TCP",
    17: "UDP",
    41: "IPv6",
    89: "OSPF",
}

def get_protocol_name(proto_num):
    return IANA_PROTOCOLS.get(proto_num, str(proto_num))

def get_service_name(port, proto):
    if 0 < port <= 1023:
        try:
            return socket.getservbyport(port, proto)
        except OSError:
            return None
    return None

def parse_dns_layer(dns_layer):
    questions = []
    answers = []

    # Normalize qd to list
    qd_raw = dns_layer.qd
    if qd_raw:
        if isinstance(qd_raw, list):
            qd_list = qd_raw
        else:
            qd_list = [qd_raw]

        for q in qd_list:
            try:
                questions.append({
                    "qname": q.qname.decode(errors="ignore") if isinstance(q.qname, bytes) else str(q.qname),
                    "qtype": q.qtype,
                    "qclass": q.qclass
                })
            except Exception:
                continue

    # Normalize answers
    if dns_layer.an:
        answers_raw = dns_layer.an
        if not isinstance(answers_raw, list):
            answers_raw = [answers_raw]

        for ans in answers_raw:
            try:
                if not hasattr(ans, 'type') or not hasattr(ans, 'rdata'):
                    continue

                rdata = None
                if ans.type == 1:  # A
                    rdata = ans.rdata
                elif ans.type == 28:  # AAAA
                    rdata = ans.rdata
                elif ans.type in [5, 12, 2]:  # CNAME, PTR, NS
                    rdata = ans.rdata.decode(errors="ignore") if isinstance(ans.rdata, bytes) else str(ans.rdata)
                elif ans.type == 16:  # TXT
                    rdata = b"".join(ans.rdata).decode(errors="ignore") if isinstance(ans.rdata, list) else ans.rdata.decode(errors="ignore")
                else:
                    rdata = str(ans.rdata)

                answers.append({
                    "rrname": ans.rrname.decode(errors="ignore") if hasattr(ans, "rrname") and isinstance(ans.rrname, bytes) else str(getattr(ans, "rrname", "")),
                    "rtype": ans.type,
                    "rclass": getattr(ans, "rclass", None),
                    "ttl": getattr(ans, "ttl", None),
                    "rdata": rdata
                })
            except Exception:
                continue

    return {
        "id": dns_layer.id,
        "qr": dns_layer.qr,
        "opcode": dns_layer.opcode,
        "rcode": dns_layer.rcode,
        "questions": questions,
        "answers": answers
    }


def main():
    output_dir = "parsed_output"
    os.makedirs(output_dir, exist_ok=True)
    input_file = sys.argv[1]

    packets = rdpcap(input_file)
    http_packets = []
    dns_packets = []
    other_packets = []

    for pkt in packets:
        if IP in pkt:
            ip_layer = pkt[IP]
            proto = ip_layer.proto
            proto_name = get_protocol_name(proto)

            entry = {
                "timestamp": datetime.utcfromtimestamp(float(pkt.time)).isoformat(),
                "src_ip": ip_layer.src,
                "dst_ip": ip_layer.dst,
                "ip_protocol": proto_name,
                "ip_header_length": ip_layer.ihl * 4,
                "packet_size": ip_layer.len,
                "type": "other"
            }

            if TCP in pkt:
                tcp_layer = pkt[TCP]
                entry.update({
                    "src_port": tcp_layer.sport,
                    "src_service": get_service_name(tcp_layer.sport, "tcp"),
                    "dst_port": tcp_layer.dport,
                    "dst_service": get_service_name(tcp_layer.dport, "tcp"),
                    "tcp_flags": str(tcp_layer.flags)
                })

                if DNS in pkt and (tcp_layer.sport == 53 or tcp_layer.dport == 53):
                    entry.update(parse_dns_layer(pkt[DNS]))
                    dns_packets.append(entry)
                    continue

                if pkt.haslayer(Raw):
                    raw_data = bytes(pkt[Raw].load)
                    if raw_data.startswith(b"GET") or raw_data.startswith(b"POST") or raw_data.startswith(b"HTTP"):
                        entry.update({
                            "type": "request" if raw_data.startswith((b"GET", b"POST")) else "response",
                            "method": raw_data.split(b" ")[0].decode(errors="ignore") if raw_data.startswith((b"GET", b"POST")) else None,
                            "path": raw_data.split(b" ")[1].decode(errors="ignore") if raw_data.startswith((b"GET", b"POST")) else None,
                            "status_code": raw_data.split(b" ")[1].decode(errors="ignore") if raw_data.startswith(b"HTTP") else None,
                            "reason": None,
                            "headers": {}
                        })
                        http_packets.append(entry)
                        continue

            elif UDP in pkt:
                udp_layer = pkt[UDP]
                entry.update({
                    "src_port": udp_layer.sport,
                    "src_service": get_service_name(udp_layer.sport, "udp"),
                    "dst_port": udp_layer.dport,
                    "dst_service": get_service_name(udp_layer.dport, "udp")
                })

                if DNS in pkt and (udp_layer.sport == 53 or udp_layer.dport == 53):
                    entry.update(parse_dns_layer(pkt[DNS]))
                    dns_packets.append(entry)
                    continue

            other_packets.append(entry)

    with open(os.path.join(output_dir, "http_traffic.json"), "a") as f:
        json.dump(http_packets, f, indent=4)

    with open(os.path.join(output_dir, "dns_traffic.json"), "a") as f:
        json.dump(dns_packets, f, indent=4)

    with open(os.path.join(output_dir, "other_traffic.json"), "a") as f:
        json.dump(other_packets, f, indent=4)

    print(f"Extracted {len(http_packets)} HTTP, {len(dns_packets)} DNS, and {len(other_packets)} other packets.")
    print("Saved to parsed_output/*.json")

if __name__ == "__main__":
    main()
