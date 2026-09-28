"""
analytics_manager.py
Aggregates skill demand frequency, candidate resume coverage, and CRM funnel statistics.
"""
from collections import Counter
from history_manager import load_history_sessions
from applications_crm import load_applications
from master_resumes import load_master_resumes
from excel_reader import load_keywords


def get_skill_heatmap_analytics() -> dict:
    """
    Scans saved JD sessions, CRM records, and master resumes to compute:
    1. Top 15 most demanded keywords across all analyzed JDs.
    2. Candidate skill coverage (present in candidate's master resumes vs missing).
    3. CRM application funnel statistics.
    """
    sessions = load_history_sessions()
    crm_apps = load_applications()
    master_data = load_master_resumes()

    # Combine master resume texts into a single search string
    master_combined = ""
    for trk in ["AI", "TPM", "ITDM", "PM"]:
        master_combined += (master_data.get(trk) or "") + "\n"
    master_combined_lower = master_combined.lower()

    # Aggregate keyword frequencies from sessions and CRM JDs
    keyword_counts = Counter()
    total_jds = len(sessions) + len(crm_apps)
    all_keywords = load_keywords()

    def _process_jd_text(jd_text):
        if not jd_text:
            return
        jd_lower = jd_text.lower()
        for trk, kw_list in all_keywords.items():
            for kw_obj in kw_list:
                kw = kw_obj["keyword"]
                kw_lower = kw.lower()
                synonyms = kw_obj.get("synonyms", [])
                if kw_lower in jd_lower or any(syn.lower() in jd_lower for syn in synonyms):
                    keyword_counts[kw] += 1

    for s in sessions:
        _process_jd_text(s.get("jd_text", ""))

    for c in crm_apps:
        _process_jd_text(c.get("jd_text", ""))

    # Top 15 demanded skills
    top_skills = []
    for kw, count in keyword_counts.most_common(15):
        kw_lower = kw.lower()
        is_covered = (kw_lower in master_combined_lower)
        pct_demanded = round((count / max(total_jds, 1)) * 100) if total_jds > 0 else 0
        top_skills.append({
            "keyword": kw,
            "demand_count": count,
            "demand_pct": pct_demanded,
            "is_covered": is_covered
        })

    # CRM Funnel Counts
    stage_counts = Counter()
    for c in crm_apps:
        st = (c.get("status") or "SAVED").upper()
        stage_counts[st] += 1

    return {
        "total_jds_analyzed": total_jds,
        "total_crm_tracked": len(crm_apps),
        "top_demanded_skills": top_skills,
        "crm_funnel": {
            "saved": stage_counts["SAVED"],
            "applied": stage_counts["APPLIED"],
            "interviewing": stage_counts["INTERVIEWING"],
            "offer": stage_counts["OFFER"],
            "archived": stage_counts["ARCHIVED"]
        }
    }
