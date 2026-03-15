from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import uuid
import json
import subprocess

app = FastAPI(title="Genome Time Machine API")

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
DATA_TMP = os.path.join(BASE_DIR, "data", "tmp")
DATA_EXPORTS = os.path.join(BASE_DIR, "data", "exports")
SCRIPT_INFER = os.path.join(BASE_DIR, "scripts", "infer_user_ancestry.py")
SCRIPT_EXPORT = os.path.join(BASE_DIR, "scripts", "export_story_page.py")

os.makedirs(DATA_TMP, exist_ok=True)
os.makedirs(DATA_EXPORTS, exist_ok=True)

class StoryRequest(BaseModel):
    inference: Dict[str, Any]

class ExportRequest(BaseModel):
    inference: Dict[str, Any]
    story: Dict[str, Any]

@app.get("/api/reference/status")
async def get_status():
    exists = os.path.exists(os.path.join(DATA_PROCESSED, "reference_pca.parquet"))
    return {"ready": exists}

@app.post("/api/upload/structured")
async def upload_structured(data: Dict[str, Any]):
    tmp_input = os.path.join(DATA_TMP, f"{uuid.uuid4()}_in.json")
    tmp_output = os.path.join(DATA_TMP, f"{uuid.uuid4()}_out.json")
    
    with open(tmp_input, "w") as f:
        json.dump(data, f)
        
    cmd = ["python3", SCRIPT_INFER, "--mode", "structured", "--input", tmp_input, "--out-json", tmp_output]
    try:
        subprocess.run(cmd, check=True)
        with open(tmp_output, "r") as f:
            res = json.load(f)
        return res
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Inference failed")
    finally:
        if os.path.exists(tmp_input): os.remove(tmp_input)
        if os.path.exists(tmp_output): os.remove(tmp_output)

@app.post("/api/upload/genotype")
async def upload_genotype(file: UploadFile = File(...)):
    tmp_input = os.path.join(DATA_TMP, f"{uuid.uuid4()}_{file.filename}")
    tmp_output = os.path.join(DATA_TMP, f"{uuid.uuid4()}_out.json")
    
    with open(tmp_input, "wb") as f:
        f.write(await file.read())
        
    cmd = ["python3", SCRIPT_INFER, "--mode", "genotype", "--input", tmp_input, "--out-json", tmp_output]
    try:
        subprocess.run(cmd, check=True)
        with open(tmp_output, "r") as f:
            res = json.load(f)
        return res
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Inference failed. Ensure valid format.")
    finally:
        if os.path.exists(tmp_input): os.remove(tmp_input)
        if os.path.exists(tmp_output): os.remove(tmp_output)

@app.post("/api/story/generate")
async def generate_story(req: StoryRequest):
    # For MVP, infer_user_ancestry already generates the story. 
    # We can just return the generated story if we passed it back before.
    # But if frontend needs regeneration, we can add a specific method.
    return {"message": "Story generated in inference step for MVP speed."}

@app.post("/api/story/export")
async def export_story(req: ExportRequest):
    tmp_json = os.path.join(DATA_TMP, f"{uuid.uuid4()}_export.json")
    story_id = req.story.get("id", str(uuid.uuid4()))
    out_html = os.path.join(DATA_EXPORTS, f"{story_id}.html")
    
    with open(tmp_json, "w") as f:
        json.dump(req.model_dump(), f)
        
    cmd = ["python3", SCRIPT_EXPORT, "--json", tmp_json, "--out-html", out_html]
    try:
        subprocess.run(cmd, check=True)
        return {"url": f"/exports/{story_id}.html", "path": out_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Export failed")
    finally:
        if os.path.exists(tmp_json): os.remove(tmp_json)
