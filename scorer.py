"""
scorer.py
Scores a Job Description against the keyword synonym bank.
"""
import re
from excel_reader import (
    load_keywords,
    load_scoring_structure,
    load_bullets,
    TRACK_LABELS,
)

# Cache loaded data (loaded once at startup)
_KEYWORDS = None
_SCORING = None
_BULLETS = None


def _get_data():
    global _KEYWORDS, _SCORING, _BULLETS
    if _KEYWORDS is None:
        _KEYWORDS = load_keywords()
        _SCORING = load_scoring_structure()
        _BULLETS = load_bullets()
    return _KEYWORDS, _SCORING, _BULLETS


def _normalize(text: str) -> str:
    """Lowercase, remove punctuation, collapse spaces."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _keyword_hit(jd_norm: str, keyword: str, synonyms: list[str]) -> tuple[int, str]:
    """
    Returns (score 0/1/2, matched_term).
    2 = exact keyword match, 1 = synonym match, 0 = no match
    """
    kw_norm = _normalize(keyword)
    if kw_norm and kw_norm in jd_norm:
        return 2, keyword

    for syn in synonyms:
        syn_norm = _normalize(syn)
        if syn_norm and syn_norm in jd_norm:
            return 1, syn

    return 0, ""


def _calc_additional_factors(track_code: str, text_lower: str) -> tuple[int, int, int]:
    """
    Calculates Excel's 3 Additional Factors (0-5 points each):
      1. Responsibility Pattern Match
      2. Company / Role Match
      3. Red Flag Penalty
    """
    resp_patterns = {
        'AI': ['ai transformation', 'digital transformation', 'automation', 'modernization', 'innovation'],
        'TPM': ['program', 'roadmap', 'delivery', 'stakeholders', 'release'],
        'ITDM': ['sla', 'itil', 'incident', 'change management', 'service delivery'],
        'PM': ['product', 'roadmap', 'customer', 'user research', 'analytics']
    }
    company_patterns = {
        'AI': ['ai', 'transformation', 'digital', 'consulting', 'strategy'],
        'TPM': ['product', 'platform', 'engineering', 'enterprise', 'gcc'],
        'ITDM': ['managed services', 'support', 'operations', 'msp', 'outsourcing'],
        'PM': ['saas', 'b2b', 'b2c', 'platform', 'product-led']
    }
    penalty_patterns = {
        'AI': ['python', 'tensorflow', 'pytorch', 'data scientist', 'ml engineer'],
        'TPM': ['helpdesk', 'l1 support', 'call center', 'desktop support', 'field support'],
        'ITDM': ['ai strategy', 'innovation', 'transformation roadmap', 'genai', 'ai vision'],
        'PM': ['software engineer', 'python', 'data scientist', 'service delivery', 'incident management']
    }

    r_score = min(5, sum(1 for p in resp_patterns.get(track_code, []) if p in text_lower))
    c_score = min(5, sum(1 for p in company_patterns.get(track_code, []) if p in text_lower))
    p_score = min(5, sum(1 for p in penalty_patterns.get(track_code, []) if p in text_lower))

    return r_score, c_score, p_score


def _excel_match_level(pts: int) -> str:
    """Excel sheet official match level boundaries."""
    if pts >= 32:
        return "Strong Match"
    elif pts >= 25:
        return "Good Match"
    elif pts >= 18:
        return "Moderate Match"
    else:
        return "Weak Match"


def score_jd(jd_text: str) -> dict:
    """
    Main scoring function matching the Excel workbook formula 100%.
    Final Score (out of 40) = Keyword Weighted Score + Resp Match (0-5) + Company Match (0-5) - Red Flag Penalty (0-5)
    """
    keywords_bank, scoring_structure, bullets = _get_data()
    jd_norm = _normalize(jd_text)
    jd_lower_raw = jd_text.lower()

    kw_lookup: dict[str, list[str]] = {
        k["keyword"].lower(): k["synonyms"] for k in keywords_bank
    }

    all_matched = set()
    tracks = {}

    for track_code, kw_rows in scoring_structure.items():
        scored_kws = []
        kw_weighted_total = 0

        for row in kw_rows:
            kw = row["keyword"]
            weight = row["weight"]
            synonyms = kw_lookup.get(kw.lower(), [])

            # Check matches across keyword + synonyms
            syn_variants = [kw.lower()] + [s.lower() for s in synonyms]
            matched_count = sum(1 for v in set(syn_variants) if v and v in jd_lower_raw)
            score = min(2, matched_count)
            matched_term = kw if score > 0 else ""

            weighted = weight * score
            kw_weighted_total += weighted

            if score > 0:
                all_matched.add(kw)

            scored_kws.append({
                "keyword": kw,
                "weight": weight,
                "score": score,
                "weighted": weighted,
                "matched_term": matched_term,
                "notes": row.get("notes", ""),
            })

        # Calculate Excel Additional Factors
        r_score, c_score, p_score = _calc_additional_factors(track_code, jd_lower_raw)

        # Excel Final Score formula: Keywords Weighted + Resp Match + Company Match - Penalty
        final_pts = kw_weighted_total + r_score + c_score - p_score
        final_pts = max(0, final_pts) # non-negative

        # Match level from Excel boundaries
        level = _excel_match_level(final_pts)

        # Percentage capacity (out of 40 max points)
        pct = min(100, round((final_pts / 40.0) * 100))

        tracks[track_code] = {
            "label": TRACK_LABELS[track_code],
            "keywords": scored_kws,
            "total_weighted": kw_weighted_total,
            "resp_score": r_score,
            "comp_score": c_score,
            "penalty_score": p_score,
            "final_pts": final_pts,
            "max_weighted": 40,
            "pct": pct,
            "level": level,
            "level_class": level.lower().replace(" ", "-"),
        }

    # Filter bullets — mark which ones hit based on theme matching
    track_bullets = {tc: [] for tc in TRACK_LABELS}
    for b in bullets:
        # Map bullet track label to track code
        b_track_code = _resolve_track(b["track"])
        if b_track_code is None:
            continue
        theme_norm = _normalize(b["theme"])
        hit = theme_norm in jd_norm or b["theme"].lower() in {
            k.lower() for k in all_matched
        }
        track_bullets[b_track_code].append({**b, "jd_hit_computed": hit})

    # Determine instant best track (highest %)
    track_order = ["AI", "TPM", "ITDM", "PM"]
    best_track = max(track_order, key=lambda tc: tracks.get(tc, {}).get("pct", 0))
    best_pct = tracks.get(best_track, {}).get("pct", 0)

    # Rank all tracks by score descending
    ranked_tracks = sorted(
        track_order,
        key=lambda tc: tracks.get(tc, {}).get("pct", 0),
        reverse=True,
    )

    return {
        "tracks": tracks,
        "bullets": track_bullets,
        "matched_keywords": sorted(all_matched),
        "best_track": best_track,
        "best_pct": best_pct,
        "ranked_tracks": ranked_tracks,
    }


def _match_level(pct: int) -> str:
    if pct >= 70:
        return "Strong Match"
    elif pct >= 40:
        return "Moderate Match"
    else:
        return "Weak Match"


def _resolve_track(track_str: str) -> str | None:
    """Map track label text to track code."""
    t = track_str.lower()
    if "ai" in t:
        return "AI"
    elif "tpm" in t or "technical program" in t:
        return "TPM"
    elif "itdm" in t or "it delivery" in t or "delivery" in t:
        return "ITDM"
    elif "pm" in t or "product" in t:
        return "PM"
    return None
