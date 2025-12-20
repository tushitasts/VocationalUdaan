from typing import List, Dict
from models import VocationalTrack, TrainingCentre, CentreCourse
from sqlalchemy import or_

# ---------------- INTEREST → SECTOR MAP ----------------

INTEREST_TO_SECTOR = {
    "beauty": ["Beauty & Wellness"],
    "parlour": ["Beauty & Wellness"],
    "makeup": ["Beauty & Wellness"],
    "tailor": ["Apparel", "Leather"],
    "stitch": ["Apparel", "Leather"],
    "sewing": ["Apparel", "Leather"],
    "electric": ["Electronics & Hardware", "Telecom", "Power"],
    "electrician": ["Electronics & Hardware", "Telecom", "Power"],
    "solar": ["Electronics & Hardware", "Power", "Green Jobs"],
    "vehicle": ["Automotive"],
    "computer": ["IT-ITeS"],
    "data": ["IT-ITeS"],
    "customer care": ["IT-ITeS"],
    "mobile": ["Electronics & Hardware", "Telecom"],
    "carpentry": ["Furniture & Fittings"],
    "plumb": ["Plumbing"],
    "agri": ["Agriculture"],
    "cook": ["Food Processing", "Tourism & Hospitality"],
    "chef": ["Tourism & Hospitality"],
    "health": ["Healthcare"],
    "nurse": ["Healthcare"],
    "retail": ["Retail"],
    "sales": ["Retail"],
    "aviation": ["Aviation"],
    "banking": ["Banking & Finance"],
    "construction": ["Construction"]
}

EDU_ORDER = ["None", "Class 8", "Class 10", "Class 12", "Graduate"]
SKILL_ORDER = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

# ---------------- HELPERS ----------------

def sectors_from_interests(interests_text: str) -> List[str]:
    if not interests_text:
        return []

    tokens = [t.strip().lower() for t in interests_text.split(",") if t.strip()]
    sectors = set()

    for token in tokens:
        for key, mapped in INTEREST_TO_SECTOR.items():
            if key in token:
                sectors.update(mapped)

    if not sectors:
        for token in tokens:
            sectors.add(token.title())

    return list(sectors)


def score_track(track, user):
    score = 0
    user_sectors = sectors_from_interests(getattr(user, "interests", "") or "")

    try:
        if track.sector and any(track.sector.lower() == s.lower() for s in user_sectors):
            score += 40
        elif track.sector:
            for s in user_sectors:
                if s.lower() in track.sector.lower():
                    score += 20
                    break
    except Exception:
        pass

    try:
        score += (track.earning_high or 0) / 1000
    except Exception:
        pass

    return score


def get_centres_for_career(db_session, career_id):
    if not career_id:
        return []

    return (
        db_session.query(TrainingCentre)
        .join(CentreCourse, CentreCourse.centre_id == TrainingCentre.id)
        .filter(CentreCourse.career_id == career_id)
        .all()
    )


def serialize_centres(centres):
    if not centres:
        return []

    out = []
    for c in centres[:3]:
        out.append({
            "name": c.name,
            "address": c.address,
            "contact": getattr(c, "contact", None),
        })
    return out

# ---------------- MAIN MATCH FUNCTION ----------------

def match_tracks(user_profile, db_session) -> List[Dict]:
    sectors = sectors_from_interests(getattr(user_profile, "interests", "") or "")

    base_query = db_session.query(VocationalTrack)

    # 🚨 CRITICAL FIX: guard against NULL sector
    if sectors:
        conditions = [
            VocationalTrack.sector.isnot(None),
            or_(*[VocationalTrack.sector.ilike(f"%{s}%") for s in sectors])
        ]
        base_query = base_query.filter(*conditions)

    tracks = base_query.all()

    # 🚨 PRODUCTION SAFETY: DB empty
    if not tracks:
        return []

    scored = []
    for t in tracks:
        centres = serialize_centres(get_centres_for_career(db_session, t.id))
        scored.append((
            score_track(t, user_profile),
            t,
            centres
        ))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, t, centres in scored[:5]:
        results.append({
            "id": t.id,
            "title": t.name,
            "sector": t.sector,
            "description": getattr(t, "attributes", None),
            "earning_low": getattr(t, "earning_low", None),
            "earning_high": getattr(t, "earning_high", None),
            "score": round(score, 2),
            "centres": centres,
        })

    return results
