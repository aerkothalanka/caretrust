from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .models import Facility, FacilityScore, ScoreBreakdownItem


PROCEDURES: dict[str, dict[str, object]] = {
    "eye_care": {
        "label": "Eye care",
        "description": "Ophthalmology, cataract, retina, glaucoma, and vision care.",
        "terms": ["eye", "ophthalmology", "ophthalmic", "cataract", "retina", "glaucoma", "vision"],
        "equipment": ["ophthalmic", "slit lamp", "phaco", "laser", "oct", "retinal"],
        "capabilities": ["cataract", "retina", "glaucoma", "optometry", "vision screening"],
    },
    "cardiac_surgery": {
        "label": "Cardiac surgery",
        "description": "Cardiac surgery, cath lab, coronary, and heart procedures.",
        "terms": ["cardiac", "cardiology", "heart", "coronary", "cabg", "bypass", "ctvs"],
        "equipment": ["cath lab", "ctvs", "heart-lung", "ecmo", "icu"],
        "capabilities": ["cardiac surgery", "bypass", "angioplasty", "cardiology", "critical care"],
    },
    "icu_critical_care": {
        "label": "ICU/critical care",
        "description": "ICU, ventilator, emergency stabilization, and critical care.",
        "terms": ["icu", "critical", "intensive", "ventilator", "emergency", "trauma"],
        "equipment": ["ventilator", "monitor", "icu", "oxygen", "defibrillator"],
        "capabilities": ["critical care", "icu", "ventilation", "emergency stabilization"],
    },
    "dialysis": {
        "label": "Dialysis",
        "description": "Dialysis, nephrology, renal care, and hemodialysis services.",
        "terms": ["dialysis", "nephrology", "renal", "kidney", "hemodialysis"],
        "equipment": ["dialysis", "hemodialysis", "ro plant", "dialyzer"],
        "capabilities": ["dialysis", "nephrology", "renal care", "hemodialysis"],
    },
    "oncology": {
        "label": "Oncology",
        "description": "Cancer care, chemotherapy, radiation, and oncology services.",
        "terms": ["oncology", "cancer", "chemotherapy", "radiation", "radiotherapy", "tumor"],
        "equipment": ["linear accelerator", "radiotherapy", "chemo", "pet ct", "mammography"],
        "capabilities": ["oncology", "chemotherapy", "radiation oncology", "surgical oncology"],
    },
    "maternity_obgyn": {
        "label": "Maternity/OBGYN",
        "description": "Maternity, obstetrics, gynecology, delivery, and newborn care.",
        "terms": ["maternity", "obstetric", "obgyn", "gynaecology", "gynecology", "delivery", "neonatal"],
        "equipment": ["labor room", "nicu", "ultrasound", "fetal monitor"],
        "capabilities": ["maternity", "delivery", "obstetrics", "gynecology", "newborn care"],
    },
    "emergency_trauma": {
        "label": "Emergency/trauma",
        "description": "Emergency department, trauma care, ambulance, and urgent care.",
        "terms": ["emergency", "trauma", "ambulance", "casualty", "urgent"],
        "equipment": ["ambulance", "defibrillator", "trauma", "emergency", "oxygen"],
        "capabilities": ["emergency", "trauma care", "ambulance", "urgent care"],
    },
}


SCORE_ALLOCATION: list[tuple[str, str, float]] = [
    ("specialties_match", "Specialties match", 1.5),
    ("procedure_match", "Procedure match", 1.5),
    ("equipment_support", "Equipment support", 1.0),
    ("capability_support", "Capability support", 1.0),
    ("description_support", "Description support", 1.0),
    ("source_url_relevance", "Source URL relevance", 1.0),
    ("contactability", "Phone/website contactability", 0.75),
    ("location_completeness", "Location completeness", 0.5),
    ("human_verification_boost", "Human verification boost", 1.5),
    ("freshness_activity", "Freshness/activity", 0.25),
]


def procedure_terms(procedure: str, kind: str = "terms") -> list[str]:
    raw = PROCEDURES.get(procedure, {}).get(kind, [])
    return [str(term).lower() for term in raw]


def score_facility(facility: Facility, procedure: str) -> FacilityScore:
    terms = procedure_terms(procedure)
    equipment_terms = procedure_terms(procedure, "equipment")
    capability_terms = procedure_terms(procedure, "capabilities")

    specialty_text = _joined(facility.specialties)
    procedure_text = _joined(facility.procedures)
    equipment_text = _joined(facility.equipment)
    capability_text = _joined(facility.capabilities)
    description = (facility.description or "").lower()
    all_text = " ".join([specialty_text, procedure_text, equipment_text, capability_text, description])

    breakdown: list[ScoreBreakdownItem] = []
    flags: list[str] = []
    evidence: list[str] = []

    specialty_hits = _hits(terms, specialty_text)
    score = 1.5 if specialty_hits else (0.75 if _hits(terms, all_text) else 0.0)
    breakdown.append(_item("specialties_match", "Specialties match", 1.5, score, specialty_hits or _hits(terms, all_text)))

    procedure_hits = _hits(terms, procedure_text)
    score = 1.5 if procedure_hits else (0.75 if _hits(terms, description) else 0.0)
    breakdown.append(_item("procedure_match", "Procedure match", 1.5, score, procedure_hits or _hits(terms, description)))

    equipment_hits = _hits(equipment_terms, equipment_text) or _hits(equipment_terms, description)
    score = min(1.0, 0.5 + 0.25 * (len(equipment_hits) - 1)) if equipment_hits else 0.0
    breakdown.append(_item("equipment_support", "Equipment support", 1.0, score, equipment_hits))

    capability_hits = _hits(capability_terms, capability_text) or _hits(capability_terms, description)
    score = min(1.0, 0.5 + 0.25 * (len(capability_hits) - 1)) if capability_hits else 0.0
    breakdown.append(_item("capability_support", "Capability support", 1.0, score, capability_hits))

    description_hits = _hits(terms + equipment_terms + capability_terms, description)
    score = 0.0
    if description_hits:
        score = 1.0 if len(description) >= 80 else 0.6
    breakdown.append(_item("description_support", "Description support", 1.0, score, description_hits[:5]))

    url_text = " ".join(filter(None, [facility.source_url, facility.website])).lower()
    url_hits = _hits(terms, url_text)
    score = 0.0
    if facility.source_url:
        score = 1.0 if url_hits or any(marker in facility.source_url.lower() for marker in ["hospital", "health", "clinic", "medical"]) else 0.6
    elif facility.website:
        score = 0.5
    breakdown.append(_item("source_url_relevance", "Source URL relevance", 1.0, score, url_hits or ([facility.source_url] if facility.source_url else [])))

    contact_score = (0.35 if facility.phone else 0.0) + (0.4 if facility.website else 0.0)
    contact_evidence = [value for value in [facility.phone, facility.website] if value]
    breakdown.append(_item("contactability", "Phone/website contactability", 0.75, contact_score, contact_evidence))

    location_fields = [facility.state, facility.district, facility.city, facility.pincode, facility.address]
    present_location = [field for field in location_fields if field]
    location_score = min(0.5, len(present_location) * 0.1)
    breakdown.append(_item("location_completeness", "Location completeness", 0.5, location_score, present_location[:3]))

    verification_score = 0.0
    if facility.human_verification_status == "verified":
        verification_score = 1.5
    elif facility.human_verification_status == "needs_review":
        verification_score = 0.5
        flags.append("Human verifier marked this claim as needing follow-up.")
    elif facility.human_verification_status == "rejected":
        verification_score = -1.5
        flags.append("Human verifier rejected or disputed this procedure claim.")
    breakdown.append(
        _item(
            "human_verification_boost",
            "Human verification boost",
            1.5,
            verification_score,
            [facility.human_verification_status] if facility.human_verification_status != "unverified" else [],
        )
    )

    freshness_score = _freshness_score(facility.last_updated)
    breakdown.append(_item("freshness_activity", "Freshness/activity", 0.25, freshness_score, [facility.last_updated] if facility.last_updated else []))

    penalty = 0.0
    if not facility.source_url:
        penalty += 0.25
        flags.append("No source URL is available for this facility claim.")
    if not facility.phone and not facility.website:
        penalty += 0.25
        flags.append("No direct phone or website was found.")
    if len(description_hits) < 2 and not equipment_hits and not capability_hits:
        penalty += 0.5
        flags.append("Procedure support is sparse; ranking relies on limited text evidence.")
    if not specialty_hits and not procedure_hits:
        penalty += 0.75
        flags.append("Procedure is inferred from related text rather than explicit specialty/procedure fields.")
    if facility.human_verification_status == "rejected":
        penalty += 1.0

    total = sum(part.score for part in breakdown) - penalty
    total = round(max(0.0, min(10.0, total)), 1)

    evidence.extend(_evidence_from_facility(facility, terms + equipment_terms + capability_terms))
    if not flags:
        flags.append("No major uncertainty flags; still verify availability before referral.")

    return FacilityScore(
        procedure=procedure,
        total_score=total,
        score_breakdown=breakdown,
        uncertainty_flags=flags,
        evidence_snippets=evidence[:5],
    )


def _joined(values: Iterable[str]) -> str:
    return " ".join(value.lower() for value in values if value)


def _hits(terms: Iterable[str], text: str) -> list[str]:
    seen = []
    text = text.lower()
    for term in terms:
        normalized = term.lower()
        if normalized and normalized in text and normalized not in seen:
            seen.append(normalized)
    return seen


def _item(key: str, label: str, max_score: float, score: float, evidence: list[str]) -> ScoreBreakdownItem:
    return ScoreBreakdownItem(
        key=key,
        label=label,
        max_score=max_score,
        score=round(max(-max_score, min(max_score, score)), 2),
        evidence=[str(value) for value in evidence if value],
    )


def _freshness_score(value: str | None) -> float:
    if not value:
        return 0.0
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value[:19], fmt).replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dt).days
            return 0.25 if age_days <= 365 else 0.1
        except ValueError:
            continue
    return 0.1


def _evidence_from_facility(facility: Facility, terms: list[str]) -> list[str]:
    snippets: list[str] = []
    fields = [
        ("Specialties", ", ".join(facility.specialties)),
        ("Procedures", ", ".join(facility.procedures)),
        ("Equipment", ", ".join(facility.equipment)),
        ("Capabilities", ", ".join(facility.capabilities)),
        ("Description", facility.description or ""),
    ]
    for label, value in fields:
        if value and _hits(terms, value):
            snippets.append(f"{label}: {value[:240]}")
    if facility.source_url:
        snippets.append(f"Source URL: {facility.source_url}")
    return snippets
