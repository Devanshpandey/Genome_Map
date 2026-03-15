#!/usr/bin/env python3
import os
import sys
import json
import uuid
import argparse
import numpy as np
import pandas as pd
import _pickle as cPickle
from sklearn.neighbors import KNeighborsClassifier

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_structured(data_path, pop_mapping, templates):
    # Expects JSON like: {"proportions": {"GBR": 0.6, "TSI": 0.4}, "mtDNA": "H", "yDNA": "R"}
    try:
        user_data = load_json(data_path)
    except:
        user_data = {"proportions": {"CEU": 1.0}}
        
    props = user_data.get("proportions", {})
    if sum(props.values()) > 1.01 or sum(props.values()) < 0.99:
        total = sum(props.values())
        if total > 0:
            props = {k: v/total for k,v in props.items()}
            
    # Normalize to regions
    regions = {}
    for code, val in props.items():
        region = pop_mapping.get(code, {}).get("region_name", "Unknown Region")
        regions[region] = regions.get(region, 0) + val
        
    top_pops = sorted([{"name": pop_mapping.get(k, {}).get("display_label", k), "score": v} for k,v in props.items()], key=lambda x: x["score"], reverse=True)
    top_regions = sorted([{"name": k, "score": v} for k,v in regions.items()], key=lambda x: x["score"], reverse=True)
    
    return build_result(top_pops, top_regions, user_data.get("mtDNA", "unknown"), user_data.get("yDNA", "unknown"), templates, mode="structured")

def parse_23andme(file_path):
    # Format: rsid  chromosome  position  genotype
    # e.g.: rs123  22  1000  AG
    df = pd.read_csv(file_path, sep='\t', comment='#', names=['rsid', 'chrom', 'pos', 'gt'])
    # Convert GT (e.g., 'AG', 'AA', 'A') to dosages towards ALT based on ref index.
    return df

def align_user_to_ref(user_df, ref_var_df, mode="23andme"):
    # ref_var_df has: variant_id, chrom, pos, ref, alt
    # we need to build a dosage vector of length N (number of ref variants)
    
    dosage_vector = np.zeros(len(ref_var_df))
    # For MVP speed, merge on pos (assuming CHR22 only)
    # Ensure pos are ints
    ref_var_df['pos'] = ref_var_df['pos'].astype(int)
    
    if mode == "23andme":
        user_df['pos'] = pd.to_numeric(user_df['pos'], errors='coerce')
        user_df = user_df.dropna(subset=['pos'])
        user_df['pos'] = user_df['pos'].astype(int)
        
        merged = ref_var_df.merge(user_df, on='pos', how='inner')
        shared_variants = len(merged)
        
        for idx, row in merged.iterrows():
            ref = row['ref']
            alt = row['alt']
            gt = str(row['gt'])
            
            if gt == '--' or gt == '__': continue
            
            d = 0
            if len(gt) == 2:
                d += (gt[0] == alt)
                d += (gt[1] == alt)
            elif len(gt) == 1:
                d += (gt[0] == alt)
                
            # It's an approximation, strict strand handling omitted for MVP
            
            # Find the original index in dosage_vector
            orig_idx = ref_var_df.index[ref_var_df['pos'] == row['pos']].tolist()[0]
            dosage_vector[orig_idx] = d
            
    return dosage_vector.reshape(1, -1), shared_variants

def build_result(top_pops, top_regions, mt, y, templates, mode="genotype", warnings=None, metrics=None, coords=None):
    res = {
        "id": str(uuid.uuid4()),
        "mode": mode,
        "top_populations": top_pops[:3],
        "top_regions": top_regions[:3],
        "mtDNA": mt,
        "yDNA": y,
        "warnings": warnings or [],
        "metrics": metrics or {},
        "pca_coordinates": coords or []
    }
    return res

def run_genotype(data_path, ref_dir, pop_mapping, templates):
    # Load artifacts
    ref_var_df = pd.read_parquet(os.path.join(ref_dir, "reference_variant_index.parquet"))
    with open(os.path.join(ref_dir, "pca_model.pkl"), 'rb') as f:
        pca = cPickle.load(f)
    ref_pca_df = pd.read_parquet(os.path.join(ref_dir, "reference_pca.parquet"))
    
    # Check if 23andMe or VCF
    # simplified to just 23andme for this MVP projection wrapper
    user_df = parse_23andme(data_path)
    
    dosage_vec, shared = align_user_to_ref(user_df, ref_var_df, mode="23andme")
    
    total_ref_vars = len(ref_var_df)
    overlap_frac = shared / total_ref_vars if total_ref_vars > 0 else 0
    
    warnings = []
    if overlap_frac < 0.02 or shared < 1000:
        warnings.append("Low variant overlap. Results have low confidence. Consider using structured mode.")
        
    user_pc = pca.transform(dosage_vec)
    
    # KNN
    X_ref = ref_pca_df[[f"PC{i+1}" for i in range(10)]].values
    y_ref = ref_pca_df['pop'].values
    
    knn = KNeighborsClassifier(n_neighbors=10, weights='distance')
    knn.fit(X_ref, y_ref)
    
    distances, indices = knn.kneighbors(user_pc)
    
    pop_counts = {}
    for idx in indices[0]:
        pop = y_ref[idx]
        pop_counts[pop] = pop_counts.get(pop, 0) + 1
        
    top_pops_raw = sorted(pop_counts.items(), key=lambda x: x[1], reverse=True)
    
    props = {k: v/10.0 for k,v in top_pops_raw}
    
    # Map to regions
    regions = {}
    for code, val in props.items():
        region = pop_mapping.get(code, {}).get("region_name", "Unknown Region")
        regions[region] = regions.get(region, 0) + val
        
    top_pops = [{"name": pop_mapping.get(k, {}).get("display_label", k), "score": v} for k,v in list(props.items())]
    top_regions = [{"name": k, "score": v} for k,v in sorted(regions.items(), key=lambda x: x[1], reverse=True)]
    
    metrics = {
        "shared_variants": shared,
        "expected_variants": total_ref_vars,
        "overlap_fraction": overlap_frac
    }
    
    coords = user_pc[0].tolist()
    
    return build_result(top_pops, top_regions, "unknown", "unknown", templates, mode="genotype", warnings=warnings, metrics=metrics, coords=coords)

def generate_story(inference_res, templates, haplos):
    story = {"id": inference_res["id"], "chapters": [], "disclaimers": templates.get("disclaimers", [])}
    
    pop1 = inference_res["top_populations"][0]["name"] if inference_res["top_populations"] else "Unknown Population"
    pop2 = inference_res["top_populations"][1]["name"] if len(inference_res["top_populations"]) > 1 else pop1
    reg1 = inference_res["top_regions"][0]["name"] if inference_res["top_regions"] else "Unknown Region"
    
    for ch in templates.get("chapters", []):
        text = ch["template"]
        text = text.replace("{continent_primary}", reg1)
        text = text.replace("{region_1}", reg1)
        text = text.replace("{pop_1}", pop1)
        text = text.replace("{pop_2}", pop2)
        
        if ch["id"] == "maternal_line":
            mt = inference_res.get("mtDNA", "unknown")
            desc = haplos.get("mtDNA", {}).get(mt, haplos["mtDNA"]["unknown"])["safe_description"]
            text = text.replace("{mt_haplogroup}", mt).replace("{mt_description}", desc)
            
        if ch["id"] == "paternal_line":
            y = inference_res.get("yDNA", "unknown")
            desc = haplos.get("yDNA", {}).get(y, haplos["yDNA"]["unknown"])["safe_description"]
            text = text.replace("{y_haplogroup}", y).replace("{y_description}", desc)
            
        story["chapters"].append({
            "id": ch["id"],
            "title": ch["title"],
            "text": text
        })
        
    return story

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["structured", "genotype"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--ref-dir", default="data/processed")
    parser.add_argument("--shared-dir", default="shared")
    parser.add_argument("--out-json", required=True)
    
    args = parser.parse_args()
    
    # Load shared
    try:
        pops = load_json(os.path.join(args.shared_dir, "populations.json"))
        pop_mapping = {p["code"]: p for p in pops}
        templates = load_json(os.path.join(args.shared_dir, "story_templates.json"))
        haplos = load_json(os.path.join(args.shared_dir, "haplogroups.json"))
    except Exception as e:
        print(f"Error loading shared data: {e}")
        sys.exit(1)
        
    if args.mode == "structured":
        res = run_structured(args.input, pop_mapping, templates)
    else:
        res = run_genotype(args.input, args.ref_dir, pop_mapping, templates)
        
    story = generate_story(res, templates, haplos)
    
    out_dict = {
        "inference": res,
        "story": story
    }
    
    with open(args.out_json, 'w') as f:
        json.dump(out_dict, f, indent=2)
        
    print(f"Wrote results to {args.out_json}")

if __name__ == "__main__":
    main()
