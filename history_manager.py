"""
history_manager.py
Manages local JSON storage for saved JD analysis sessions.
"""
import json
import os
import time
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "saved_sessions.json"


def load_history_sessions() -> list[dict]:
    """Load all saved sessions from JSON file."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history_session(session_data: dict) -> dict:
    """
    Save or update a session in JSON file.
    Expects dict with: id, title, company, jd_text, date, best_track, best_score, scores, signals, etc.
    """
    history = load_history_sessions()
    
    session_id = session_data.get("id") or f"session_{int(time.time() * 1000)}"
    session_data["id"] = session_id
    session_data["timestamp"] = int(time.time())
    if not session_data.get("date"):
        session_data["date"] = time.strftime("%b %d, %Y %I:%M %p")

    # Check if session with same ID already exists
    existing_idx = None
    for idx, s in enumerate(history):
        if s.get("id") == session_id:
            existing_idx = idx
            break

    if existing_idx is not None:
        history[existing_idx] = session_data
    else:
        history.insert(0, session_data)  # newest first

    # Persist to disk
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return session_data


def delete_history_session(session_id: str) -> bool:
    """Delete a session by ID."""
    history = load_history_sessions()
    filtered = [s for s in history if s.get("id") != session_id]
    if len(filtered) < len(history):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)
        return True
    return False
