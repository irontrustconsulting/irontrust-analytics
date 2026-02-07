# batch_parse_pcaps.py
import os
import json
from scapy_parser import parse_pcap

def batch_parse(folder_path, output_dir):
    all_http = []
    all_dns = []
    all_other = []

    for file in os.listdir(folder_path):
        if file.endswith(".pcap") or file.endswith(".pcapng"):
            full_path = os.path.join(folder_path, file)
            print(f"Parsing {file}...")
            result = parse_pcap(full_path)
            all_http.extend(result["http"])
            all_dns.extend(result["dns"])
            all_other.extend(result["other"])

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "all_http.json"), "w") as f:
        json.dump(all_http, f, indent=2)

    with open(os.path.join(output_dir, "all_dns.json"), "w") as f:
        json.dump(all_dns, f, indent=2)

    with open(os.path.join(output_dir, "all_other.json"), "w") as f:
        json.dump(all_other, f, indent=2)

    print("Parsing complete. Aggregated JSON files written to", output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_folder", help="Path to folder with .pcap files")
    parser.add_argument("output_folder", help="Folder to store JSON output")
    args = parser.parse_args()

    batch_parse(args.input_folder, args.output_folder)
