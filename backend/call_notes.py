from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import Facility


def generate_demo_call_notes(facility: Facility, procedure: str, service_label: str) -> dict[str, Any]:
    """Create a deterministic demo call transcript for Trust Review.

    This intentionally does not place a real call. It gives the demo a realistic
    agent/facility conversation and persists the outcome like a future call-agent
    integration would.
    """
    now = datetime.now(timezone.utc).isoformat()
    lower_name = facility.name.lower()
    script = _script_for_facility(lower_name, service_label)
    location = ", ".join([part for part in [facility.city, facility.state, facility.pincode] if part]) or facility.country or "India"
    date_label = now[:10]
    summary = script["summary"].format(facility=facility.name, service=service_label, location=location, information_date=date_label)
    return {
        "facility_id": facility.unique_id,
        "facility_name": facility.name,
        "procedure": procedure,
        "service_label": service_label,
        "mode": "demo_call",
        "status": "call_notes_saved",
        "information_date": now,
        "summary": summary,
        "verified_claims": script["verified_claims"],
        "open_questions": script["open_questions"],
        "recommendation": script["recommendation"],
        "conversation": [
            {"speaker": speaker, "text": text.format(facility=facility.name, service=service_label, location=location)}
            for speaker, text in script["conversation"]
        ],
        "next_refresh_after_days": 14,
        "source": "demo_call_script_pending_real_call_agent",
    }


def _script_for_facility(lower_name: str, service_label: str) -> dict[str, Any]:
    if "narayana" in lower_name or "cardiac" in lower_name:
        return {
            "summary": "Demo call notes from {information_date}: {facility} reception confirmed that cardiac surgery referrals are handled by the cardiac sciences desk; ICU availability and surgeon schedule should be reconfirmed before transfer.",
            "verified_claims": [
                "Cardiac sciences/cardiac surgery desk can receive referral inquiries.",
                "Emergency and ICU coordination is available through the hospital switchboard.",
                "Final acceptance depends on current bed availability and surgeon review.",
            ],
            "open_questions": [
                "Current ICU bed availability for the selected date/time.",
                "Whether the specific procedure requires pre-authorization or prior reports.",
            ],
            "recommendation": "Use as a strong candidate, but call again within 24 hours of referral for capacity confirmation.",
            "conversation": [
                ("CareSignal Agent", "Hello, I am calling on behalf of a care coordinator. Can you confirm whether {facility} currently handles {service} referrals?"),
                ("Facility Desk", "Yes, cardiac cases are handled through our cardiac sciences team. Please route patient reports and urgency details to the coordinator."),
                ("CareSignal Agent", "Is ICU or post-operative critical care coordination available if the case is accepted?"),
                ("Facility Desk", "Yes, but bed status changes during the day. The coordinator must confirm availability before transfer."),
                ("CareSignal Agent", "What should the referring team prepare before calling back?"),
                ("Facility Desk", "Diagnosis, recent reports, patient vitals, insurance/payment details, and expected arrival time."),
            ],
        }
    if "aravind" in lower_name or "eye" in lower_name:
        return {
            "summary": "Demo call notes from {information_date}: {facility} confirmed ophthalmology services and cataract/retina routing; procedure timing and specialist availability should be checked for the patient's specific diagnosis.",
            "verified_claims": [
                "Ophthalmology service desk can route cataract and retina inquiries.",
                "Patients should bring prior prescriptions, scans, and referral notes.",
                "Same-day evaluation may be possible, but surgery scheduling depends on specialist assessment.",
            ],
            "open_questions": [
                "Specific retina/corneal specialist availability on the planned visit date.",
                "Whether the case requires appointment booking or emergency walk-in triage.",
            ],
            "recommendation": "Good evidence for eye-care capability; verify specialist slot and procedure timing before referral.",
            "conversation": [
                ("CareSignal Agent", "Hello, can you confirm whether {facility} can evaluate a patient for {service}?"),
                ("Facility Desk", "Yes, our ophthalmology team evaluates these cases. The patient should bring earlier prescriptions and scans."),
                ("CareSignal Agent", "Can the desk confirm surgery availability immediately?"),
                ("Facility Desk", "The doctor decides after evaluation. The appointment desk can advise expected timing once records are reviewed."),
                ("CareSignal Agent", "What information should the coordinator share before sending the patient?"),
                ("Facility Desk", "Age, diagnosis, current symptoms, prior surgery history, and available eye reports."),
            ],
        }
    if "fortis" in lower_name or "escorts" in lower_name:
        return {
            "summary": "Demo call notes from {information_date}: {facility} confirmed heart-specialty routing; live acceptance still requires current bed/cath-lab/OT capacity verification.",
            "verified_claims": [
                "Heart institute desk can route cardiology/cardiac surgery inquiries.",
                "Emergency triage and planned referral pathways are separate.",
                "Capacity must be confirmed by the coordination desk before transfer.",
            ],
            "open_questions": [
                "Current operating theatre/cath-lab slot availability.",
                "Insurance/financial clearance requirements for the patient.",
            ],
            "recommendation": "Keep in shortlist for heart cases; request live coordinator confirmation before committing patient movement.",
            "conversation": [
                ("CareSignal Agent", "I am checking referral readiness for {service}. Can {facility} route this inquiry to the heart team?"),
                ("Facility Desk", "Yes, heart-related referrals go through the cardiac coordinator or emergency desk depending on acuity."),
                ("CareSignal Agent", "Can you confirm bed and procedure availability now?"),
                ("Facility Desk", "Availability changes frequently. The coordinator will confirm after reviewing patient details."),
                ("CareSignal Agent", "What should be provided for review?"),
                ("Facility Desk", "Clinical summary, ECG/echo or relevant reports, current vitals, and payment/insurance details."),
            ],
        }
    return {
        "summary": "Demo call notes from {information_date}: {facility} answered the general desk and could route a {service} inquiry, but the specific clinical service must be confirmed with the duty coordinator.",
        "verified_claims": [
            "Facility desk reachable in demo flow.",
            "Referral inquiry can be routed with patient details.",
            "Procedure-specific availability requires coordinator confirmation.",
        ],
        "open_questions": [
            "Named department contact and current specialist availability.",
            "Live bed/slot availability and referral documentation requirements.",
        ],
        "recommendation": "Treat as needs-review until a real call-agent integration confirms the department and capacity.",
        "conversation": [
            ("CareSignal Agent", "Hello, I am checking whether {facility} can handle a referral for {service}."),
            ("Facility Desk", "We can route the inquiry, but the department coordinator will need patient details before confirming."),
            ("CareSignal Agent", "What information should the care coordinator prepare?"),
            ("Facility Desk", "Diagnosis, recent reports, current condition, payer details, and requested appointment or transfer date."),
        ],
    }
