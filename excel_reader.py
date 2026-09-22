"""
excel_reader.py
Reads and parses the Resume Utility Excel workbook.
"""
import re
import pandas as pd
from pathlib import Path

EXCEL_FILE = Path(__file__).parent / "Resume_utility_FInal_18sep26.xlsx.xlsx"

# Sheet-to-track mapping for scoring sheets
SCORE_SHEETS = {
    "AI": "AI_SCORE",
    "TPM": "TPM_SCORE",
    "ITDM": "ITDM_SCORE",
    "PM": "PM_SCORE",
}

TRACK_LABELS = {
    "AI": "AI Transformation Manager",
    "TPM": "Technical Program Manager",
    "ITDM": "IT Delivery Manager",
    "PM": "Product Manager",
}


def _clean_str(val) -> str:
    """Return stripped string or empty string for NaN."""
    if pd.isna(val):
        return ""
    return str(val).strip()


def load_keywords() -> list[dict]:
    """
    Load KEYWORDS sheet.
    Returns list of dicts: {keyword, synonyms: [str], tier, track, weight}
    """
    df = pd.read_excel(EXCEL_FILE, sheet_name="KEYWORDS", header=None)

    # Find header row — look for cell containing 'Keyword'
    header_row = None
    for i, row in df.iterrows():
        for cell in row:
            if _clean_str(cell).lower() == "keyword":
                header_row = i
                break
        if header_row is not None:
            break

    if header_row is None:
        raise ValueError("Could not find KEYWORDS header row")

    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Rename columns (strip whitespace, handle emoji)
    col_map = {}
    for c in df.columns:
        s = _clean_str(c).lower()
        if "keyword" in s and "synonym" not in s:
            col_map[c] = "keyword"
        elif "synonym" in s:
            col_map[c] = "synonyms"
        elif "tier" in s:
            col_map[c] = "tier"
        elif "track" in s:
            col_map[c] = "track"
        elif "weight" in s and "tier" not in s:
            col_map[c] = "weight_num"
    df = df.rename(columns=col_map)

    keywords = []
    for _, row in df.iterrows():
        kw = _clean_str(row.get("keyword", ""))
        if not kw:
            continue
        syn_raw = _clean_str(row.get("synonyms", ""))
        synonyms = [s.strip() for s in syn_raw.split("|") if s.strip()]
        keywords.append({
            "keyword": kw,
            "synonyms": synonyms,
            "tier": _clean_str(row.get("tier", "")),
            "track": _clean_str(row.get("track", "")),
        })

    # Merge supplementary keywords from supplementary_keywords.py
    try:
        from supplementary_keywords import SUPPLEMENTARY_KEYWORDS
        existing_kw_set = {k["keyword"].strip().lower() for k in keywords}
        for sk in SUPPLEMENTARY_KEYWORDS:
            if sk["keyword"].strip().lower() not in existing_kw_set:
                keywords.append({
                    "keyword": sk["keyword"],
                    "synonyms": sk["synonyms"],
                    "tier": sk["tier"],
                    "track": sk["track"],
                })
                existing_kw_set.add(sk["keyword"].strip().lower())
    except ImportError:
        pass

    return keywords


def load_scoring_structure() -> dict[str, list[dict]]:
    """
    Load keyword rows from each scoring sheet.
    Returns {track_code: [{keyword, weight, notes}, ...]}
    """
    result = {}
    for track, sheet in SCORE_SHEETS.items():
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet, header=None)

        # Find header row containing 'Keyword'
        header_row = None
        for i, row in df.iterrows():
            for cell in row:
                if "keyword" in _clean_str(cell).lower():
                    header_row = i
                    break
            if header_row is not None:
                break

        if header_row is None:
            result[track] = []
            continue

        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        col_map = {}
        for c in df.columns:
            s = _clean_str(c).lower()
            if "keyword" in s and "synonym" not in s:
                col_map[c] = "keyword"
            elif "weight" in s and "score" not in s:
                col_map[c] = "weight"
            elif "notes" in s:
                col_map[c] = "notes"
        df = df.rename(columns=col_map)

        rows = []
        for _, row in df.iterrows():
            kw = _clean_str(row.get("keyword", ""))
            if not kw:
                continue
            try:
                weight = int(float(row.get("weight", 1)))
            except (ValueError, TypeError):
                weight = 1
            rows.append({
                "keyword": kw,
                "weight": weight,
                "notes": _clean_str(row.get("notes", "")),
            })

        # Append supplementary keywords for this track
        try:
            from supplementary_keywords import get_supplementary_keywords
            supp = get_supplementary_keywords(track)
            existing_track_kws = {r["keyword"].strip().lower() for r in rows}
            for sk in supp:
                if sk["keyword"].strip().lower() not in existing_track_kws:
                    rows.append({
                        "keyword": sk["keyword"],
                        "weight": sk["weight"],
                        "notes": f"Internet research keyword ({sk['tier']} tier)",
                    })
                    existing_track_kws.add(sk["keyword"].strip().lower())
        except ImportError:
            pass

        result[track] = rows

    return result


def load_bullets() -> list[dict]:
    """
    Load BULLET_GENERATOR sheet.
    Returns list of dicts: {track, theme, bullet, jd_hit, recommended}
    """
    df = pd.read_excel(EXCEL_FILE, sheet_name="BULLET_GENERATOR", header=None)

    # Find header row
    header_row = None
    for i, row in df.iterrows():
        for cell in row:
            if "track" in _clean_str(cell).lower():
                header_row = i
                break
        if header_row is not None:
            break

    if header_row is None:
        return []

    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    col_map = {}
    for c in df.columns:
        s = _clean_str(c).lower()
        if s == "track":
            col_map[c] = "track"
        elif "keyword" in s or "theme" in s:
            col_map[c] = "theme"
        elif "bullet" in s or "suggested" in s:
            col_map[c] = "bullet"
        elif "jd" in s and "hit" in s:
            col_map[c] = "jd_hit"
        elif "recommend" in s:
            col_map[c] = "recommended"
    df = df.rename(columns=col_map)

    bullets = []
    for _, row in df.iterrows():
        bullet = _clean_str(row.get("bullet", ""))
        if not bullet:
            continue
        # Strip emoji from track
        track_raw = _clean_str(row.get("track", ""))
        track_clean = re.sub(r"[^\w\s]", "", track_raw).strip()
        bullets.append({
            "track_raw": track_raw,
            "track": track_clean,
            "theme": _clean_str(row.get("theme", "")),
            "bullet": bullet,
            "jd_hit": _clean_str(row.get("jd_hit", "")),
            "recommended": _clean_str(row.get("recommended", "")),
        })

    return bullets
