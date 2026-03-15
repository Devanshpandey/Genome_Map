#!/usr/bin/env python3
import os
import json
import argparse
import random
import numpy as np
import pandas as pd
from cyvcf2 import VCF
from sklearn.decomposition import PCA
import _pickle as cPickle

def load_panel(panel_path):
    df = pd.read_csv(panel_path, sep='\t', usecols=[0, 1, 2], names=['sample', 'pop', 'superpop'], header=0)
    return df

def get_balanced_samples(panel_df, limit_samples, seed=42):
    random.seed(seed)
    # Group by superpop
    superpops = panel_df['superpop'].unique()
    n_superpops = len(superpops)
    target_per_sp = math.ceil(limit_samples / n_superpops) if n_superpops > 0 else limit_samples
    
    selected_samples = []
    for sp in superpops:
        sp_samples = panel_df[panel_df['superpop'] == sp]['sample'].tolist()
        random.shuffle(sp_samples)
        selected_samples.extend(sp_samples[:target_per_sp])
    
    return selected_samples[:limit_samples]

def process_vcf(vcf_path, selected_samples, maf_thresh=0.01):
    print(f"Opening VCF: {vcf_path}")
    vcf = VCF(vcf_path)
    
    # Set samples to read
    if selected_samples:
        vcf.set_samples(selected_samples)
    
    actual_samples = vcf.samples
    n_samples = len(actual_samples)
    print(f"Reading {n_samples} samples from VCF.")
    
    variants = []
    dosages = []
    
    count = 0
    for variant in vcf:
        if not variant.is_snp or len(variant.ALT) > 1:
            continue
            
        # Optional: compute MAF and filter
        af = variant.aaf
        if af < maf_thresh or af > (1.0 - maf_thresh):
            continue
            
        # Get genotypes (0=REF, 1=ALT, 2=unknown/missing in cyvcf2 format... wait)
        # cyvcf2 variant.gt_types is a numpy array of types: 0=HOM_REF, 1=HET, 2=UNKNOWN, 3=HOM_ALT
        gt_types = variant.gt_types
        # We need alt alleles dosage: 0, 1, 2. Convert cyvcf2 gt_types to dosage:
        # HOM_REF (0) -> 0
        # HET (1) -> 1
        # HOM_ALT (3) -> 2
        # UNKNOWN (2) -> 0 (impute to ref for MVP)
        
        dosage_arr = np.zeros(n_samples, dtype=np.int8)
        dosage_arr[gt_types == 1] = 1
        dosage_arr[gt_types == 3] = 2
        
        dosages.append(dosage_arr)
        variants.append({
            'variant_id': variant.ID if variant.ID else f"{variant.CHROM}_{variant.POS}_{variant.REF}_{variant.ALT[0]}",
            'chrom': variant.CHROM,
            'pos': variant.POS,
            'ref': variant.REF,
            'alt': variant.ALT[0]
        })
        
        count += 1
        if count % 10000 == 0:
            print(f"Processed {count} variants...")
            
    # Convert lists to matrix (Variants x Samples -> Samples x Variants)
    print("Transposing genotype matrix...")
    X = np.array(dosages, dtype=np.int8).T 
    
    # Filter out variants with zero variance
    var_vars = np.var(X, axis=0)
    keep_idx = var_vars > 0
    X = X[:, keep_idx]
    variants = [var for i, var in enumerate(variants) if keep_idx[i]]
    
    print(f"Final dosage matrix shape: {X.shape}")
    return X, variants, actual_samples

def compute_pca_and_centroids(X, sample_ids, panel_df, out_dir):
    print("Computing PCA...")
    # scikit-learn PCA with whiten=False
    pca = PCA(n_components=10, whiten=False, random_state=42)
    X_pca = pca.fit_transform(X)
    
    # Save PCA model
    pca_model_path = os.path.join(out_dir, "pca_model.pkl")
    with open(pca_model_path, 'wb') as f:
        cPickle.dump(pca, f)
        
    # Save PCA components coordinates (reference projection)
    pca_df = pd.DataFrame(X_pca, columns=[f"PC{i+1}" for i in range(10)])
    pca_df['sample'] = sample_ids
    pca_df = pca_df.merge(panel_df, on='sample', how='left')
    
    pca_parquet_path = os.path.join(out_dir, "reference_pca.parquet")
    pca_df.to_parquet(pca_parquet_path, index=False)
    
    # Compute population centroids
    print("Computing population centroids...")
    centroids = {}
    for pop in pca_df['pop'].unique():
        if pd.isna(pop): continue
        pop_data = pca_df[pca_df['pop'] == pop]
        mean_coords = pop_data[[f"PC{i+1}" for i in range(10)]].mean().tolist()
        centroids[pop] = mean_coords
        
    centroids_path = os.path.join(out_dir, "reference_population_centroids.json")
    with open(centroids_path, 'w') as f:
        json.dump(centroids, f, indent=2)
        
    print(f"Saved artifacts to {out_dir}")

def main():
    parser = argparse.ArgumentParser(description="Prepare 1KG reference panel")
    parser.add_argument("--in-dir", type=str, default="data/raw/1kg")
    parser.add_argument("--out-dir", type=str, default="data/processed")
    parser.add_argument("--limit-samples", type=int, default=500)
    import math # ensure math is available for get_balanced_samples
    
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    
    vcf_path = ""
    for file in os.listdir(args.in_dir):
        if file.endswith(".vcf.gz") and not file.endswith(".tbi"):
            vcf_path = os.path.join(args.in_dir, file)
            break
            
    panel_path = os.path.join(args.in_dir, "1kg_samples.panel")
    
    if not os.path.exists(vcf_path) or not os.path.exists(panel_path):
        print(f"Error: Missing VCF ({vcf_path}) or panel ({panel_path}) in {args.in_dir}")
        sys.exit(1)
        
    print("Loading panel...")
    panel_df = load_panel(panel_path)
    
    selected_samples = []
    if args.limit_samples > 0:
        print(f"Selecting balanced subset of {args.limit_samples} samples...")
        import math
        selected_samples = get_balanced_samples(panel_df, args.limit_samples)
        
    X, variants, actual_samples = process_vcf(vcf_path, selected_samples)
    
    # Save variant index
    print("Saving reference variant index...")
    var_df = pd.DataFrame(variants)
    var_df.to_parquet(os.path.join(args.out_dir, "reference_variant_index.parquet"), index=False)
    
    compute_pca_and_centroids(X, actual_samples, panel_df, args.out_dir)
    print("Done!")

if __name__ == "__main__":
    main()
