from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import os
import pandas as pd
from app.utils import get_project_path, save_metadata, fetch_user_metadata
import shutil
from pathlib import Path
from datetime import datetime

app = FastAPI()

@app.post("/upload/")
async def upload_pdf_and_generate_related_files(
    user_id: int = Form(...),
    file: UploadFile = File(...)
):
    # Derive project name from PDF filename
    project_name = Path(file.filename).stem
    project_path = get_project_path(user_id, project_name)

    # Save original PDF
    pdf_path = project_path / file.filename
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Simulate backend-generated files
    updated_json = project_path / f"{project_name}_updated.json"
    updated_txt = project_path / f"{project_name}_updated.txt"

    updated_json.write_text(f'{{"info": "Processed JSON for {project_name}"}}')
    updated_txt.write_text(f"This is the updated text version of {project_name}")

    # Save metadata
    timestamp = datetime.utcnow().isoformat()
    records = [
        {
            "project": project_name,
            "file_type": "original_pdf",
            "file_name": file.filename,
            "file_path": str(pdf_path),
            "timestamp": timestamp
        },
        {
            "project": project_name,
            "file_type": "updated_json",
            "file_name": updated_json.name,
            "file_path": str(updated_json),
            "timestamp": timestamp
        },
        {
            "project": project_name,
            "file_type": "updated_text",
            "file_name": updated_txt.name,
            "file_path": str(updated_txt),
            "timestamp": timestamp
        }
    ]
    save_metadata(user_id, records)

    return {"message": "Files stored", "project": project_name}

@app.get("/projects/{user_id}")
def get_user_projects(user_id: int):
    metadata = fetch_user_metadata(user_id)
    projects = {}
    for record in metadata:
        proj = record["project"]
        if proj not in projects:
            projects[proj] = []
        projects[proj].append(record)
    return {"projects": projects}



# Delete a specific file
@app.delete("/file/{user_id}/{project_name}/{file_name}")
def delete_file(user_id: int, project_name: str, file_name: str):
    project_path = get_project_path(user_id, project_name)
    file_path = project_path / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)

    # Update parquet
    meta_file = BASE_PATH / f"user_{user_id}" / "files.parquet"
    if meta_file.exists():
        df = pd.read_parquet(meta_file)
        df = df[df["file_name"] != file_name]
        df.to_parquet(meta_file, index=False)

    return {"message": f"Deleted {file_name}"}

# Delete entire project
@app.delete("/projects/{user_id}/{project_name}")
def delete_project(user_id: int, project_name: str):
    project_path = get_project_path(user_id, project_name)

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    shutil.rmtree(project_path)

    # Clean up metadata
    meta_file = BASE_PATH / f"user_{user_id}" / "files.parquet"
    if meta_file.exists():
        df = pd.read_parquet(meta_file)
        df = df[df["project"] != project_name]
        df.to_parquet(meta_file, index=False)

    return {"message": f"Project '{project_name}' deleted"}

# Rename project
@app.put("/projects/{user_id}/{old_project_name}/rename")
def rename_project(user_id: int, old_project_name: str, new_project_name: str = Form(...)):
    old_path = get_project_path(user_id, old_project_name)
    new_path = get_project_path(user_id, new_project_name)

    if not old_path.exists():
        raise HTTPException(status_code=404, detail="Old project not found")
    if new_path.exists():
        raise HTTPException(status_code=400, detail="New project name already exists")

    old_path.rename(new_path)

    # Update metadata
    meta_file = BASE_PATH / f"user_{user_id}" / "files.parquet"
    if meta_file.exists():
        df = pd.read_parquet(meta_file)
        df.loc[df["project"] == old_project_name, "project"] = new_project_name
        df["file_path"] = df["file_path"].str.replace(old_project_name, new_project_name)
        df["file_name"] = df["file_name"].apply(lambda f: f.replace(old_project_name, new_project_name) if old_project_name in f else f)
        df.to_parquet(meta_file, index=False)

    return {"message": f"Renamed '{old_project_name}' to '{new_project_name}'"}
