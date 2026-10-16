"""Environment-driven configuration for SupportSense AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"


@dataclass(frozen=True)
class Settings:
    """Runtime settings; no credentials are stored in source control."""

    retrieval_threshold: float = float(os.getenv("RETRIEVAL_THRESHOLD", "0.14"))
    max_question_length: int = int(os.getenv("MAX_QUESTION_LENGTH", "1000"))
    max_results: int = int(os.getenv("MAX_RETRIEVAL_RESULTS", "3"))
    default_user_role: str = "public"
    databricks_host: str = os.getenv("DATABRICKS_HOST", "").rstrip("/")
    databricks_token: str = os.getenv("DATABRICKS_TOKEN", "")
    databricks_serving_endpoint: str = os.getenv("DATABRICKS_SERVING_ENDPOINT", "")
    databricks_catalog: str = os.getenv("DATABRICKS_CATALOG", "main")
    databricks_schema: str = os.getenv("DATABRICKS_SCHEMA", "supportsense")


SETTINGS = Settings()
