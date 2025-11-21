from typing import List, Dict
from models import VocationalTrack, TrainingCentre, CentreCourse
from sqlalchemy import or_

# interest keyword -> sector mapping (expand as you like)
INTEREST_TO_SECTOR = {
    "beauty": ["Beauty & Wellness"],
    "parlour": ["Beauty & Wellness"],
    "makeup": ["Beauty & Wellness"],
    "tailor": ["Apparel","Leather"],
    "stitch": ["Apparel","Leather"],
    "sewing": ["Apparel","Leather"],
    "electric": ["Electronics & Hardware","Telecom","Power","Iron & Steel"],
    "electrician": ["Electronics & Hardware","Telecom","Power","Iron & Steel"],
    "solar": ["Electronics & Hardware","Telecom","Power","Iron & Steel","Green Jobs"],
    "vehicle":["Automotive"],
    "computer": ["IT-ITeS"],
    "data": ["IT-ITeS"],
    "customer care":["IT-ITeS"],
    "mobile": ["Electronics & Hardware","Telecom"],
    "carpentry": ["Furniture & Fittings"],
    "plumb": ["Plumbing"],
    "agri": ["Agriculture"],
    "cook": ["Food Processing", "Tourism & Hospitality","Food Processing"],
    "chef":["Tourism & Hospitality"],
    "food":["Tourism & Hospitality"],
    "technician":["Electronics & Hardware","Telecom"],
    "handicraft":["Handicarfts"],
    "fitter":["Capital Goods"],
    "education":["Management"],
    "bake": ["Food Processing"],
    "health": ["Life Sciences","Healthcare"],
    "nurse": ["Life Sciences","Healthcare"],
    "courier":["Logistics"],
    "clerk":["Logistics"],
    "retail":["Retail"],
    "sales":["Retail"],
    "airline":["Aviation"],
    "aviation":["Aviation"],
    "finance":["Banking & Finance"],
    "banking":["Banking & Finance"],
    "construction":["Construction"]
}

EDU_ORDER = ["None", "Class 8", "Class 10", "Class 12", "Graduate"]
SKILL_ORDER = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}


def edu_ok(user_edu: str, min_edu: str) -> bool:
    try:
        return EDU_ORDER.index(user_edu) >= EDU_ORDER.index(min_edu)
    except Exception:
        return True


def skill_ok(user_level: str, recommended: str) -> bool:
    if not recommended or not user_level:
        return True
    return SKILL_ORDER.get(user_level, 1) >= SKILL_ORDER.get(recommended, 1)


def sectors_from_interests(interests_text: str) -> List[str]:
    """
    Convert free-text interests into a list of sector labels we should match against.
    - Uses INTEREST_TO_SECTOR mapping via substring matches (case-insensitive)
    - If nothing matches, fallback to title-cased tokens (so "electronics" -> "Electronics")
    """
    sectors = set()
    if not interests_text:
        return []
    tokens = [t.strip().lower() for t in interests_text.split(",") if t.strip()]
    for token in tokens:
        for key, mapped in INTEREST_TO_SECTOR.items():
            if key in token:
                sectors.update(mapped)
    if not sectors:
        # fallback: interpret user tokens as sector names (title-cased)
        for token in tokens:
            sectors.add(token.title())
    # debug: uncomment to inspect what sectors are derived
    # print("DEBUG sectors_from_interests ->", sectors)
    return list(sectors)


def _normalise_text(x):
    if not x:
        return ""
    return str(x).strip().lower()


def score_track(track, user_profile, user_pincode_prefix):
    """
    Score a track numerically. Higher = more relevant.
    - Big boost for sector exact match vs smaller for partial match.
    - Secondary boost for skill match and earning_high.
    """
    score = 0
    try:
        user_sectors = sectors_from_interests(user_profile.interests or "")
        track_sector = getattr(track, "sector", None)
        # exact match (case-insensitive trimmed)
        if track_sector and any(_normalise_text(track_sector) == _normalise_text(s) for s in user_sectors):
            score += 40
        # partial match (user sector contained in track sector or vice-versa)
        else:
            for s in user_sectors:
                if track_sector and (s.lower() in _normalise_text(track_sector) or _normalise_text(track_sector) in s.lower()):
                    score += 20
                    break
    except Exception:
        pass

    # skill level match
    try:
        if skill_ok(user_profile.skill_level or "", getattr(track, "recommended_skill_level", None) or ""):
            score += 10
    except Exception:
        pass

    # earning potential tiny boost (normalized)
    try:
        score += ((getattr(track, "earning_high", 0) or 0) / 1000)
    except Exception:
        pass

    return score


# --- centre lookup via join on centre_courses table (use CentreCourse model) ---
def get_centres_for_career(db_session, career_id):
    """
    Return list of TrainingCentre objects linked to `career_id` via centre_courses.
    """
    centres = (
        db_session.query(TrainingCentre)
        .join(CentreCourse, CentreCourse.centre_id == TrainingCentre.id)
        .filter(CentreCourse.career_id == career_id)
        .all()
    )
    return centres


def _order_and_serialize_centres(centre_objs, user_pincode=None):
    """
    Return up to 3 serialized centres, ordered by pincode proximity if available.
    Serialized fields match what the template expects.
    """
    if not centre_objs:
        return []
    if not user_pincode:
        subset = centre_objs[:3]
    else:
        pfx = user_pincode[:3]
        same_pin = [c for c in centre_objs if (getattr(c, "pincode", "") or "").startswith(user_pincode)]
        same_region = [
            c for c in centre_objs
            if ((getattr(c, "pincode", "") or "")[:3] == pfx) and c not in same_pin
        ]
        others = [c for c in centre_objs if c not in same_pin and c not in same_region]
        ordered = same_pin + same_region + others
        subset = ordered[:3]

    return [
        {
            "name": c.name,
            "address": c.address,
            "pincode": getattr(c, "pincode", None),
            "phone": getattr(c, "contact", None) or getattr(c, "phone", None),
            "courses": getattr(c, "courses", None),
        }
        for c in subset
    ]


def match_tracks(user_profile, db_session) -> List[Dict]:
    """
    Main entry: return a list of recommended tracks (with centres) for the user_profile.
    Uses flexible partial case-insensitive matching (ilike) on the VocationalTrack.sector column.
    """
    #sectors = sectors_from_interests(user_profile.interests or "")
    sectors = sectors_from_interests(getattr(user_profile, "interests", "") or "")
    q = db_session.query(VocationalTrack)

    # If we derived sectors, filter using case-insensitive partial matching,
    # so 'electronics' will match 'Electronics & Hardware' etc.
    if sectors:
        conditions = []
        for s in sectors:
            # Use ilike for partial matches; guard against None sector column
            conditions.append(VocationalTrack.sector.ilike(f"%{s}%"))
        q = q.filter(or_(*conditions))

    tracks = q.all()
    if not tracks:
        tracks = db_session.query(VocationalTrack).all()

    pfx = (getattr(user_profile, "pincode", "") or "")[:3]

    scored = []
    for t in tracks:
        s = score_track(t, user_profile, pfx) or 0
        centres_objs = get_centres_for_career(db_session, t.id)
        centres = _order_and_serialize_centres(centres_objs) #user_profile.pincode
        scored.append((s, t, centres))

    scored_sorted = sorted(scored, key=lambda x: x[0], reverse=True)

    results = []
    for score_val, t, centres in scored_sorted[:5]:
        results.append({
            "id": t.id,
            "title": getattr(t, "name", None) or getattr(t, "title", None),
            "sector": t.sector,
            "description": getattr(t, "attributes", None) or getattr(t, "description", None),
            "duration": getattr(t, "typical_duration_months", None),
            "earning_low": getattr(t, "earning_low", None),
            "earning_high": getattr(t, "earning_high", None),
            "recommended_skill_level": getattr(t, "recommended_skill_level", None),
            "score": round(score_val, 2),
            "centres": centres,
        })
    return results

