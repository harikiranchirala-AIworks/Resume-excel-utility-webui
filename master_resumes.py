"""
master_resumes.py
Manages persistent storage for the 4 master candidate resumes (AI, TPM, ITDM, PM).
"""
import json
from pathlib import Path

MASTER_RESUMES_FILE = Path(__file__).parent / "master_resumes.json"

DEFAULT_CANDIDATE_INFO = {
    "name": "",
    "phone": "",
    "email": "",
    "location": "",
    "linkedin": ""
}

DEFAULT_DATA = {
    "AI": "",
    "TPM": "",
    "ITDM": "",
    "PM": "",
    "candidate_info": DEFAULT_CANDIDATE_INFO
}


def load_master_resumes() -> dict:
    """Load the 4 master candidate resumes and candidate contact info from JSON file."""
    if not MASTER_RESUMES_FILE.exists():
        return json.loads(json.dumps(DEFAULT_DATA))
    try:
        with open(MASTER_RESUMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            res = json.loads(json.dumps(DEFAULT_DATA))
            for track in ["AI", "TPM", "ITDM", "PM"]:
                res[track] = data.get(track, "")
            cand_info = data.get("candidate_info", {})
            if isinstance(cand_info, dict):
                for k in DEFAULT_CANDIDATE_INFO:
                    res["candidate_info"][k] = str(cand_info.get(k, "")).strip()
            return res
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))


def save_master_resumes(resumes_dict: dict) -> dict:
    """Save/update the 4 master candidate resumes and candidate info in JSON file."""
    current = load_master_resumes()
    for track in ["AI", "TPM", "ITDM", "PM"]:
        if track in resumes_dict:
            current[track] = str(resumes_dict[track]).strip()

    if "candidate_info" in resumes_dict and isinstance(resumes_dict["candidate_info"], dict):
        for k in DEFAULT_CANDIDATE_INFO:
            if k in resumes_dict["candidate_info"]:
                current["candidate_info"][k] = str(resumes_dict["candidate_info"][k]).strip()

    with open(MASTER_RESUMES_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2, ensure_ascii=False)

    return current


def update_single_master_resume(track: str, resume_text: str) -> dict:
    """Update a single track's master resume."""
    current = load_master_resumes()
    track_code = str(track).strip().upper()
    if track_code in ["AI", "TPM", "ITDM", "PM"]:
        current[track_code] = str(resume_text).strip()
        with open(MASTER_RESUMES_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    return current


def save_candidate_info(candidate_info: dict) -> dict:
    """Save/update candidate contact details."""
    current = load_master_resumes()
    if isinstance(candidate_info, dict):
        for k in DEFAULT_CANDIDATE_INFO:
            if k in candidate_info:
                current["candidate_info"][k] = str(candidate_info[k]).strip()
        with open(MASTER_RESUMES_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    return current
