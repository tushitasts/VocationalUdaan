from typing import List, Dict
from models import VocationalTrack, TrainingCentre, CentreCourse
from sqlalchemy import or_

# interest keyword -> sector mapping
INTEREST_TO_SECTOR = {
    "beauty": ["Beauty & Wellness"],
    "parlour": ["Beauty & Wellness"],
    "makeup": ["Beauty & Wellness"],
    "tailor": ["Apparel", "Leather"],
    "stitch": ["Apparel", "Leather"],
    "sewing": ["Apparel", "Leather"],
    "electric": ["Electronics & Hardware", "Telecom", "Power", "Iron & Steel"],
    "electrician": ["Electronics & Hardware", "Telecom", "Power", "Iron & Steel"],
    "solar": ["Electronics & Hardware", "Telecom", "Power", "Iron & Steel", "Green Jobs"],
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
    "food": ["Tourism & Hospitality"],
    "technician": ["Electronics & Hardware", "Telecom"],
    "handicraft": ["Handicarfts"],
    "fitter": ["Capital Goods"],
    "education": ["Management"],
    "bake": ["Food Processing"],
    "health": ["Life Sciences", "Healthcare"],
    "nurse": ["Life Sciences", "Healthcare"],
    "courier": ["Logistics"],
    "clerk": ["Logistics"],
    "retail": ["Retail"],
    "sales": ["Retail"],
    "airline": ["Aviation"],
    "aviation": ["Aviation"],
    "finance": ["Banking & Finance"],
    "banking": ["Banking & Finance"],
    "construction": ["Construction"]
}

SKILL_ORDER = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


def sectors_from_interests(interests_text: str) -> List[str]:
    if not interests_text:
        return []

    tokens = [t.strip().lower() for t in interests_text.split(",") if t.strip()]
    sectors = set()

    for token in tokens:
        for key, mapped in INTEREST_TO_SECTOR.items():
            if key in token:
                sectors.update(mapped)

    return list(sectors)


def score_track(track, user):
    score = 0

    user_sectors = sectors_from_interests(user.interests or "")
    track_sector = (track.sector or "").lower()

    for s in user_sectors:
        if s.lower() in track_sector:
            score += 40

    if user.skill_level and track.recommended_skill_level:
        if SKILL_ORDER.get(user.skill_level, 1) >= SKILL_ORDER.get(track.recommended_skill_level, 1):
            score += 10

    if track.earning_high:
        score += track.earning_high / 1000

    return score


def get_centres_for_career(db_session, career_id):
    return (
        db_session.query(TrainingCentre)
        .join(CentreCourse, CentreCourse.centre_id == TrainingCentre.id)
        .filter(CentreCourse.career_id == career_id)
        .all()
    )


def match_tracks(user, db_session) -> List[Dict]:
    sectors = sectors_from_interests(user.interests or "")
    q = db_session.query(VocationalTrack)

    if sectors:
        conditions = []
        for s in sectors:
            conditions.append(VocationalTrack.sector.ilike(f"%{s}%"))
        q = q.filter(or_(*conditions))

    tracks = q.all()

    # 🔥 FALLBACK — never return empty unless DB is empty
    if not tracks:
        tracks = db_session.query(VocationalTrack).all()

    scored = []
    for t in tracks:
        score = score_track(t, user)
        centres = get_centres_for_career(db_session, t.id)
        scored.append((score, t, centres))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, t, centres in scored[:5]:
        results.append({
            "id": t.id,
            "title": t.name,
            "sector": t.sector,
            "description": t.attributes,
            "earning_low": t.earning_low,
            "earning_high": t.earning_high,
            "recommended_skill_level": t.recommended_skill_level,
            "centres": [
                {
                    "name": c.name,
                    "address": c.address,
                    "phone": getattr(c, "contact", None),
                }
                for c in centres
            ],
        })

    return results
