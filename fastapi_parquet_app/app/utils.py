import os
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_PATH = Path("app/storage")

def get_project_path(user_id: int, project_name: str) -> Path:
    path = BASE_PATH / f"user_{user_id}" / "projects" / project_name
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_metadata(user_id: int, records: list[dict]):
    user_path = BASE_PATH / f"user_{user_id}"
    user_path.mkdir(parents=True, exist_ok=True)

    meta_file = user_path / "files.parquet"
    df_new = pd.DataFrame(records)

    if meta_file.exists():
        df_existing = pd.read_parquet(meta_file)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_parquet(meta_file, index=False)

def fetch_user_metadata(user_id: int):
    meta_file = BASE_PATH / f"user_{user_id}" / "files.parquet"
    if not meta_file.exists():
        return []
    return pd.read_parquet(meta_file).to_dict(orient="records")
