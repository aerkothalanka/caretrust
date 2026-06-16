from __future__ import annotations

from collections import defaultdict

from .data import DataStore
from .models import AssistantQuery, AssistantResponse, FacilityTopItem
from .scoring import infer_procedure, procedure_label, score_facility


def answer_query(store: DataStore, query: AssistantQuery) -> AssistantResponse:
    question = query.question.lower()
    procedure = infer_procedure(query.procedure, question) or "eye_care"

    if any(token in question for token in ["compare state", "state comparison", "states", "by state"]):
        return _state_comparison(store, procedure)
    if any(token in question for token in ["low confidence", "uncertain", "uncertainty", "weak evidence"]):
        return _low_confidence(store, procedure)
    if any(token in question for token in ["verified", "verification", "human"]):
        return _verified_comparison(store, procedure)
    if query.unique_id or any(token in question for token in ["why", "explain", "evidence", "trust card"]):
        return _facility_explanation(store, query, procedure)
    return _top_facilities(store, procedure, query.state)


def _top_facilities(store: DataStore, procedure: str, state: str | None) -> AssistantResponse:
    items = ranked_facilities(store, procedure, state, 10)
    leaders = ", ".join(f"{item.name} ({item.score:.1f})" for item in items[:3])
    answer = f"Top {procedure_label(procedure)} options are led by {leaders}. Scores are out of 10 and combine procedure evidence, contactability, location completeness, freshness, and human verification."
    return AssistantResponse(
        intent="top_facilities",
        answer=answer,
        chart_type="ranked_bar",
        data=[{"facility": item.name, "state": item.state, "score": item.score} for item in items],
    )


def _state_comparison(store: DataStore, procedure: str) -> AssistantResponse:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in ranked_facilities(store, procedure, None, 100):
        grouped[item.state or "Unknown"].append(item.score)
    data = [
        {"state": state, "average_score": round(sum(scores) / len(scores), 1), "facility_count": len(scores)}
        for state, scores in sorted(grouped.items())
    ]
    strongest = max(data, key=lambda row: row["average_score"]) if data else None
    answer = "No state comparison is available yet."
    if strongest:
        answer = f"{strongest['state']} has the strongest sample average for {procedure_label(procedure)} at {strongest['average_score']}/10 across {strongest['facility_count']} fallback or queried facilities."
    return AssistantResponse(intent="state_comparison", answer=answer, chart_type="state_average_bar", data=data)


def _low_confidence(store: DataStore, procedure: str) -> AssistantResponse:
    items = [
        item
        for item in ranked_facilities(store, procedure, None, 100)
        if item.score < 5.5 or any("sparse" in flag.lower() or "no source" in flag.lower() for flag in item.uncertainty_flags)
    ][:10]
    answer = f"I found {len(items)} lower-confidence {procedure_label(procedure)} claims. Prioritize verifying service availability, recent activity, and procedure-specific equipment before referral."
    return AssistantResponse(
        intent="low_confidence_claims",
        answer=answer,
        chart_type="flagged_table",
        data=[{"facility": item.name, "score": item.score, "flags": item.uncertainty_flags} for item in items],
        uncertainty_flags=["This is a deterministic template answer, not arbitrary SQL or free-form data exploration."],
    )


def _facility_explanation(store: DataStore, query: AssistantQuery, procedure: str) -> AssistantResponse:
    facility = store.get_facility(query.unique_id) if query.unique_id else None
    if facility is None:
        candidates = ranked_facilities(store, procedure, query.state, 10)
        facility = candidates[0] if candidates else None
    if facility is None:
        return AssistantResponse(intent="facility_explanation", answer="No matching facility was found.", uncertainty_flags=["Facility identifier was missing or unknown."])
    score = score_facility(facility, procedure)
    strongest = sorted(score.score_breakdown, key=lambda item: item.score, reverse=True)[:3]
    parts = ", ".join(f"{item.label} {_compact_score(item.score)}/{_compact_score(item.max_score)}" for item in strongest)
    answer = f"{facility.name} scores {score.total_score:.1f}/10 for {procedure_label(procedure)}. Strongest contributors are {parts}. Verify current availability directly before acting on the ranking."
    return AssistantResponse(
        intent="facility_explanation",
        answer=answer,
        chart_type="score_breakdown",
        data=[item.dict() for item in score.score_breakdown],
        uncertainty_flags=score.uncertainty_flags,
    )


def _verified_comparison(store: DataStore, procedure: str) -> AssistantResponse:
    items = ranked_facilities(store, procedure, None, 100)
    verified = [item for item in items if item.human_verification_status == "verified"]
    needs_review = [item for item in items if item.human_verification_status == "needs_review"]
    answer = f"{len(verified)} facilities have verified {procedure_label(procedure)} claims and {len(needs_review)} need review. Human verification adds up to 1.5 points and rejected claims are penalized."
    return AssistantResponse(
        intent="verified_comparison",
        answer=answer,
        chart_type="verification_table",
        data=[
            {
                "facility": item.name,
                "score": item.score,
                "verification_status": item.human_verification_status,
                "verification_count": item.human_verification_count,
            }
            for item in items[:20]
        ],
    )


def ranked_facilities(
    store: DataStore,
    procedure: str,
    state: str | None,
    limit: int,
    country: str | None = None,
    city: str | None = None,
    pincode: str | None = None,
) -> list[FacilityTopItem]:
    normalized_country = country.lower() if country else None
    normalized_state = state.lower() if state else None
    normalized_city = city.lower() if city else None
    normalized_pincode = str(pincode).lower() if pincode else None
    items: list[FacilityTopItem] = []
    for facility in store.list_facilities():
        if normalized_country and (facility.country or "").lower() != normalized_country:
            continue
        if normalized_state and (facility.state or "").lower() != normalized_state:
            continue
        if normalized_city and not _location_matches(facility.city, normalized_city):
            continue
        if normalized_pincode and (facility.pincode or "").lower() != normalized_pincode:
            continue
        items.append(facility_top_item(facility, procedure))
    return sorted(items, key=lambda item: (item.score, item.human_verification_count), reverse=True)[:limit]


def _location_key(value: str | None) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def _location_matches(facility_value: str | None, requested_value: str | None) -> bool:
    facility_key = _location_key(facility_value)
    requested_key = _location_key(requested_value)
    if not facility_key or not requested_key:
        return False
    return facility_key == requested_key or facility_key in requested_key or requested_key in facility_key


def facility_top_item(facility, procedure: str) -> FacilityTopItem:
    score = score_facility(facility, procedure)
    return FacilityTopItem(
        **facility.model_dump(),
        score=score.total_score,
        score_breakdown=score.score_breakdown,
        uncertainty_flags=score.uncertainty_flags,
        evidence_snippets=score.evidence_snippets,
    )


def _compact_score(value: float) -> str:
    return f"{float(value):.2f}".rstrip("0").rstrip(".")
