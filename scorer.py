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


def score_jd(jd_text: str) -> dict:
    """
    Main scoring function.
    Returns a dict with:
      - tracks: {track_code: {label, keywords: [...], total_weighted, max_weighted, pct, level}}
      - bullets: {track_code: [matched bullets]}
      - matched_keywords: [str]  — all keywords that hit
    """
    keywords_bank, scoring_structure, bullets = _get_data()
    jd_norm = _normalize(jd_text)

    # Build keyword→synonyms lookup
    kw_lookup: dict[str, list[str]] = {
        k["keyword"].lower(): k["synonyms"] for k in keywords_bank
    }

    all_matched = set()
    tracks = {}

    for track_code, kw_rows in scoring_structure.items():
        scored_kws = []
        total_weighted = 0
        max_weighted = 0

        for row in kw_rows:
            kw = row["keyword"]
            weight = row["weight"]
            synonyms = kw_lookup.get(kw.lower(), [])
            score, matched_term = _keyword_hit(jd_norm, kw, synonyms)

            weighted = weight * score
            max_weighted += weight * 2  # max possible = weight × 2

            total_weighted += weighted
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

        pct = round(total_weighted / max_weighted * 100) if max_weighted else 0
        level = _match_level(pct)

        tracks[track_code] = {
            "label": TRACK_LABELS[track_code],
            "keywords": scored_kws,
            "total_weighted": total_weighted,
            "max_weighted": max_weighted,
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
