# Genome Time Machine

A runnable MVP to explore probabilistic genetic similarity and ancestral history against the 1000 Genomes Phase 3 reference panel.

This tool implements an end-to-end pipeline to download genetic reference data, prepare a PCA-based variant model, and project user genotypes to infer population similarity.

## ⭐ Quickstart (End-to-End on a Laptop)

Follow these steps to run the complete pipeline from scratch on your local machine.

### 1. Install Dependencies
```bash
make install
```
*(Ensure you have Python 3.10+ and Node.js 18+ installed).*

### 2. Download Reference Data (CHR22)
```bash
make download-ref
```
*This downloads the 1000 Genomes Phase 3 minimal CHR22 VCF and sample panel to `data/raw/1kg`.*

### 3. Prepare Reference Panel
```bash
make prepare-ref
```
*This streams the VCF, builds a sparse PCA model, and computes population centroids, saving artifacts to `data/processed/`.*

### 4. Start the Application
```bash
# In terminal 1 (starts FastAPI backend on port 8000)
make api

# In terminal 2 (starts Next.js frontend on port 3000)
make web
```
Then open [http://localhost:3000](http://localhost:3000) in your browser.

*(Alternatively, use `make dev` if you prefer docker-compose).*

---

## Architecture Summary

This repository consists of four main components interacting as a complete application:
1. **Data Pipeline (`scripts/`)**: Uses `cyvcf2` and `scikit-learn` to efficiently parse VCF data, apply a balanced sampling strategy across populations, and build a Principal Component Analysis (PCA) model mapping variant dosages to a 10-dimensional feature space.
2. **Inference Engine (`scripts/infer_user_ancestry.py`)**: Projects newly uploaded user genotypes (VCF or 23andMe format) onto the pre-computed PCA basis. A K-Nearest Neighbors (KNN) model then measures similarity against reference samples to infer top matching geographical regions.
3. **Backend API (`apps/api/`)**: A FastAPI application that serves endpoints to process structural queries, parse uploaded genetic data, run the inference engine, and formulate "story chapters" based on deterministic templates.
4. **Frontend UI (`apps/web/`)**: A Next.js 14 web client utilizing Tailwind CSS and Framer Motion to visualize the probabilistic results via interactive maps and exportable story pages.

## Scientific Limitations & Disclaimers
* **Not Medical Advice**: This application provides educational visualizations based on reference populations. It does not provide clinical or diagnostic information.
* **Limited Scope**: The underlying dataset relies entirely on the 1000 Genomes Project individuals. It does not contain an exhaustive list of all human populations or granular sub-regional clusters.
* **Probabilistic Nature**: Similarity clustering (PCA/KNN) does not definitively prove "ancestry." The model demonstrates which reference samples your genotype most closely resembles.
* **Chromosome 22 Restriction**: This MVP operates solely on Chromosome 22 for memory and speed efficiency. A whole-genome panel would yield significantly higher resolution.
* **Modern vs Ancient**: Results reflect similarity to *modern* sampled populations, not necessarily historical or ancient migration origin points.

## Recommended Next Steps
To evolve this MVP further, the following extensions are suggested:
1. **Incorporate HGDP Data**: Add the Human Genome Diversity Project (HGDP) panel to the raw download phase. Merge the panels during `prepare_reference_panel.py` to vastly increase available reference populations and global resolution.
2. **Add Ancient DNA Projections**: Integrate AADR (Allen Ancient DNA Resource) panels. By projecting ancient individuals into the same PCA space, the UI could map temporal relationships ("Your genome matches the Anatolian Neolithic Farmer clustering").
3. **Full Genome Indexing**: Switch the pipeline from `CHR22` to whole-genome by utilizing Dask or Ray to parallelize `prepare_reference_panel.py` across all chromosomes without memory exhaustion.
