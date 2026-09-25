"""
master_resumes.py
Manages persistent storage for the 4 master candidate resumes (AI, TPM, ITDM, PM).
"""
import json
from pathlib import Path

MASTER_RESUMES_FILE = Path(__file__).parent / "master_resumes.json"

DEFAULT_RESUMES = {
    "AI": "",
    "TPM": "",
    "ITDM": "",
    "PM": ""
}


def load_master_resumes() -> dict:
    """Load the 4 master candidate resumes from JSON file."""
    if not MASTER_RESUMES_FILE.exists():
        return DEFAULT_RESUMES.copy()
    try:
        with open(MASTER_RESUMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all 4 track keys exist
            res = DEFAULT_RESUMES.copy()
            for track in ["AI", "TPM", "ITDM", "PM"]:
                res[track] = data.get(track, "")
            return res
    except Exception:
        return DEFAULT_RESUMES.copy()


def save_master_resumes(resumes_dict: dict) -> dict:
    """Save/update the 4 master candidate resumes in JSON file."""
    current = load_master_resumes()
    for track in ["AI", "TPM", "ITDM", "PM"]:
        if track in resumes_dict:
            current[track] = str(resumes_dict[track]).strip()

    with open(MASTER_RESUMES_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    return current


def update_single_master_resume(track: str, resume_text: str) -> dict:
    """Update a single track's master resume."""
    current = load_master_resumes()
    track_code = str(track).strip().upper()
    if track_code in current:
        current[track_code] = str(resume_text).strip()
        with open(MASTER_RESUMES_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    return current
