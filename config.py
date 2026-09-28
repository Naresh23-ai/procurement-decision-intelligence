import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("RFP_DB_PATH", BASE_DIR / "database" / "rfp_evaluation.db"))

def _setting(name: str, default: str) -> str:
    """Read env first, then Streamlit secrets, then default."""
    value = os.getenv(name)
    if value not in (None, ""):
        return str(value)
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default

LLM_PROVIDER = _setting("LLM_PROVIDER", "mock").lower()
OPENAI_MODEL = _setting("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = _setting("OPENAI_API_KEY", "")
MAX_PDF_CHARS = int(_setting("MAX_PDF_CHARS", "50000"))
