#!/usr/bin/env python3
import os
import sys
import json
import math
import hashlib
import argparse
import urllib.request
import urllib.error
from datetime import datetime

VCF_URL = "http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz"
TBI_URL = "http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5b.20130502.genotypes.vcf.gz.tbi"
PANEL_URL = "http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/integrated_call_samples_v3.20130502.ALL.panel"

def download_file(url, out_path):
    print(f"Downloading {url} to {out_path}...")
    if os.path.exists(out_path):
        # Very basic resume/skip logic: if file exists and has size > 0, assume it's fine for MVP
        sz = os.path.getsize(out_path)
        if sz > 1024:
            print(f"File {out_path} exists ({sz} bytes), skipping download.")
            return out_path
            
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, open(out_path, 'wb') as out_file:
            data = response.read() # Read all for MVP. A proper download would stream chunks.
            out_file.write(data)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        # MVP: Some .tbi files might not download easily. We catch but do not crash.
    return out_path

def create_manifest(out_dir, files_info):
    manifest_path = os.path.join(out_dir, "manifest.json")
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "genome_build": "GRCh37/hg19 (Phase3)",
        "files": files_info
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {manifest_path}")

def main():
    parser = argparse.ArgumentParser(description="Download 1KG reference data")
    parser.add_argument("--chrom", type=str, default="22")
    parser.add_argument("--limit-samples", type=int, default=500)
    parser.add_argument("--out-dir", type=str, default="data/raw/1kg")
    
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    # 1. Download VCF
    vcf_out = os.path.join(args.out_dir, f"1kg_chr{args.chrom}.vcf.gz")
    download_file(VCF_URL, vcf_out)
    
    # 2. Download TBI
    tbi_out = os.path.join(args.out_dir, f"1kg_chr{args.chrom}.vcf.gz.tbi")
    download_file(TBI_URL, tbi_out)
    
    # 3. Download Panel
    panel_out = os.path.join(args.out_dir, "1kg_samples.panel")
    download_file(PANEL_URL, panel_out)
    
    # 4. Save manifest
    files_info = [
        {"filename": os.path.basename(vcf_out), "url": VCF_URL, "type": "vcf"},
        {"filename": os.path.basename(tbi_out), "url": TBI_URL, "type": "index"},
        {"filename": os.path.basename(panel_out), "url": PANEL_URL, "type": "panel"}
    ]
    create_manifest(args.out_dir, files_info)
    
    print("Download complete.")

if __name__ == "__main__":
    main()
