from __future__ import annotations

import os
import re
import uuid
import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib import request as urllib_request
from urllib.error import URLError

from .models import Facility, ShortlistRequest, VerificationRequest, VoiceRequest
from .scoring import PROCEDURES


FACILITIES_TABLE = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.facilities"
PINCODE_TABLE = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.india_post_pincode_directory"
NFHS_TABLE = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators"
APP_SCHEMA = "lakebase_hackathon_demo.public"


class DataStore:
    def __init__(self) -> None:
        self._facilities: list[Facility] | None = None
        self._pincode_locations: list[dict[str, Any]] | None = None
        self._verifications: list[dict[str, Any]] = []
        self._shortlists: list[dict[str, Any]] = []
        self._voice_sessions: dict[str, dict[str, Any]] = {}
        self._voice_turns: list[dict[str, Any]] = []
        self.last_source = "not_loaded"

    def list_procedures(self) -> list[dict[str, Any]]:
        return [
            {
                "id": procedure_id,
                "label": str(definition["label"]),
                "description": str(definition["description"]),
                "synonyms": list(definition["terms"]),
            }
            for procedure_id, definition in PROCEDURES.items()
        ]

    def list_facilities(self) -> list[Facility]:
        if self._facilities is None:
            self._facilities = self._load_facilities()
        return [self._apply_verification_state(facility) for facility in self._facilities]


    def filter_options(self) -> dict[str, list[dict[str, str]]]:
        facilities = self.list_facilities()
        locations = self.location_dimensions()
        def options(values):
            cleaned = sorted({str(v).strip() for v in values if v})
            return [{"value": value, "label": value} for value in cleaned]
        return {
            "countries": options([row.get("country") for row in locations] + [f.country or "India" for f in facilities]) or [{"value": "India", "label": "India"}],
            "states": options([row.get("state") for row in locations] + [f.state for f in facilities]),
            "cities": options([row.get("city") for row in locations] + [f.city for f in facilities]),
            "pincodes": options([row.get("postal_code") for row in locations] + [f.pincode for f in facilities]),
            "services": self.service_groupings(),
            "age_groups": [
                {"value": "all", "label": "All age groups"},
                {"value": "child", "label": "Children / pediatric"},
                {"value": "adult", "label": "Adults"},
                {"value": "senior", "label": "Seniors"},
            ],
        }

    def service_groupings(self) -> list[dict[str, str]]:
        return [
            {
                "service_id": procedure_id,
                "service_label": "Eye surgery / eye care" if procedure_id == "eye_care" else str(definition["label"]),
                "specialty_group": _specialty_group(procedure_id),
                "keywords": ", ".join(str(term) for term in definition.get("terms", [])),
            }
            for procedure_id, definition in PROCEDURES.items()
        ]

    def location_dimensions(self) -> list[dict[str, Any]]:
        if self._pincode_locations is None:
            self._pincode_locations = _load_pincode_locations()
        if self._pincode_locations:
            return self._pincode_locations
        seen: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for facility in self.list_facilities():
            key = (facility.country or "India", facility.state or "", facility.city or "", facility.pincode or "")
            if key not in seen:
                seen[key] = {
                    "country": key[0],
                    "state": key[1],
                    "city": key[2],
                    "postal_code": key[3],
                    "latitude": facility.latitude,
                    "longitude": facility.longitude,
                    "facility_count": 0,
                }
            seen[key]["facility_count"] += 1
        return sorted(seen.values(), key=lambda row: (row["country"], row["state"], row["city"], row["postal_code"]))

    def get_facility(self, unique_id: str) -> Facility | None:
        for facility in self.list_facilities():
            if facility.unique_id == unique_id:
                return facility
        return None

    def add_verification(self, request: VerificationRequest) -> dict[str, Any]:
        record = {
            "verification_id": str(uuid.uuid4()),
            "unique_id": request.unique_id,
            "procedure": request.procedure,
            "status": request.status,
            "verifier_name": request.verifier_name,
            "notes": request.notes,
            "evidence_url": request.evidence_url,
            "created_at": _now_iso(),
        }
        self._verifications.append(record)
        self._insert_lakebase(
            "facility_human_verifications",
            {
                "verification_id": record["verification_id"],
                "facility_unique_id": record["unique_id"],
                "procedure": record["procedure"],
                "verification_status": record["status"],
                "verifier_name": record["verifier_name"],
                "notes": record["notes"],
                "evidence_url": record["evidence_url"],
                "created_at": record["created_at"],
            },
        )
        return record

    def add_shortlist(self, request: ShortlistRequest) -> dict[str, Any]:
        record = {
            "shortlist_id": str(uuid.uuid4()),
            "facility_unique_id": request.unique_id,
            "procedure": request.procedure,
            "planner_name": request.planner_name,
            "notes": request.notes,
            "created_at": _now_iso(),
        }
        self._shortlists.append(record)
        self._insert_lakebase("planner_shortlists", record)
        return record

    def recent_shortlists(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._select_lakebase(
            "SELECT shortlist_id, facility_unique_id, procedure, planner_name, notes, created_at FROM public.planner_shortlists ORDER BY created_at DESC LIMIT %s",
            [limit],
        ) or list(reversed(self._shortlists[-limit:]))
        return [self._enrich_facility_record(row, "facility_unique_id") for row in rows[:limit]]

    def recent_verifications(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._select_lakebase(
            "SELECT verification_id, facility_unique_id, procedure, verification_status, verifier_name, notes, evidence_url, created_at FROM public.facility_human_verifications ORDER BY created_at DESC LIMIT %s",
            [limit],
        )
        if not rows:
            rows = [
                {
                    "verification_id": row.get("verification_id"),
                    "facility_unique_id": row.get("unique_id"),
                    "procedure": row.get("procedure"),
                    "verification_status": row.get("status"),
                    "verifier_name": row.get("verifier_name"),
                    "notes": row.get("notes"),
                    "evidence_url": row.get("evidence_url"),
                    "created_at": row.get("created_at"),
                }
                for row in reversed(self._verifications[-limit:])
            ]
        return [self._enrich_facility_record(row, "facility_unique_id") for row in rows[:limit]]

    def verification_notes(self, unique_id: str, procedure: str) -> list[str]:
        return [
            str(record["notes"])
            for record in self._verifications
            if record["unique_id"] == unique_id and record["procedure"] == procedure and record.get("notes")
        ]

    def start_or_get_voice_session(self, session_id: str | None) -> str:
        active_id = session_id or str(uuid.uuid4())
        if active_id not in self._voice_sessions:
            now = _now_iso()
            record = {"session_id": active_id, "created_at": now, "last_turn_at": now}
            self._voice_sessions[active_id] = record
            self._insert_lakebase("voice_assistant_sessions", record)
        return active_id

    def log_voice_turn(self, session_id: str, request: VoiceRequest, response_text: str, intent: str) -> bool:
        record = {
            "turn_id": str(uuid.uuid4()),
            "session_id": session_id,
            "facility_unique_id": request.unique_id,
            "procedure": request.procedure,
            "caller_transcript": request.transcript,
            "assistant_response": response_text,
            "intent": intent,
            "created_at": _now_iso(),
        }
        self._voice_turns.append(record)
        self._insert_lakebase("voice_assistant_turns", record)
        return True

    def log_call(self, session_id: str, facility_unique_id: str | None, procedure: str | None, summary: str) -> None:
        self._insert_lakebase(
            "facility_call_logs",
            {
                "call_id": str(uuid.uuid4()),
                "session_id": session_id,
                "facility_unique_id": facility_unique_id,
                "procedure": procedure,
                "call_summary": summary,
                "created_at": _now_iso(),
            },
        )

    def _load_facilities(self) -> list[Facility]:
        if _truthy(os.getenv("CARESIGNAL_FORCE_FALLBACK")):
            self.last_source = "fallback_forced"
            return fallback_facilities()
        try:
            rows = _load_databricks_facility_rows()
            if rows:
                self.last_source = "databricks_sql"
                return [_normalize_facility(row, index) for index, row in enumerate(rows)]
        except Exception as exc:  # Databricks packages or credentials may not exist locally.
            self.last_source = f"fallback_after_error:{exc.__class__.__name__}"
        self.last_source = self.last_source if self.last_source.startswith("fallback_after_error") else "fallback"
        return fallback_facilities()

    def _apply_verification_state(self, facility: Facility) -> Facility:
        related = [record for record in self._verifications if record["unique_id"] == facility.unique_id]
        if not related:
            return facility
        latest = max(related, key=lambda row: row["created_at"])
        return facility.model_copy(
            update={
                "human_verification_status": latest["status"],
                "human_verification_count": len(related),
            }
        )

    def _enrich_facility_record(self, row: dict[str, Any], key: str) -> dict[str, Any]:
        record = dict(row)
        facility_id = record.get(key) or record.get("unique_id")
        facility = self.get_facility(str(facility_id)) if facility_id else None
        if facility:
            record["facility_name"] = facility.name
            record["city"] = facility.city
            record["state"] = facility.state
        if isinstance(record.get("created_at"), datetime):
            record["created_at"] = record["created_at"].isoformat()
        return record

    def _select_lakebase(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        if not all(os.getenv(name) for name in ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]):
            return []
        try:
            import psycopg2
        except Exception:
            return []
        try:
            conn = psycopg2.connect(
                host=os.getenv("PGHOST"),
                database=os.getenv("PGDATABASE"),
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                port=os.getenv("PGPORT", "5432"),
                sslmode=os.getenv("PGSSLMODE", "require"),
            )
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or [])
                    columns = [column[0] for column in (cursor.description or [])]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            return []

    def _insert_lakebase(self, table: str, values: dict[str, Any]) -> None:
        if not all(os.getenv(name) for name in ["PGHOST", "PGDATABASE", "PGUSER", "PGPASSWORD"]):
            return
        try:
            import psycopg2
        except Exception:
            return
        columns = list(values)
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(columns)
        sql = f"INSERT INTO public.{table} ({column_sql}) VALUES ({placeholders})"
        try:
            conn = psycopg2.connect(
                host=os.getenv("PGHOST"),
                database=os.getenv("PGDATABASE"),
                user=os.getenv("PGUSER"),
                password=os.getenv("PGPASSWORD"),
                port=os.getenv("PGPORT", "5432"),
                sslmode=os.getenv("PGSSLMODE", "require"),
            )
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, [values[column] for column in columns])
            conn.close()
        except Exception:
            return



def _load_pincode_locations() -> list[dict[str, Any]]:
    limit = int(os.getenv("CARESIGNAL_PINCODE_LIMIT", "5000"))
    query = f"""
        SELECT
          'India' AS country,
          statename AS state,
          district AS city,
          CAST(pincode AS STRING) AS postal_code,
          TRY_CAST(latitude AS DOUBLE) AS latitude,
          TRY_CAST(longitude AS DOUBLE) AS longitude,
          COUNT(*) AS facility_count
        FROM {PINCODE_TABLE}
        WHERE pincode IS NOT NULL
        GROUP BY statename, district, pincode, latitude, longitude
        LIMIT {limit}
    """
    try:
        return _load_query_rows(query)
    except Exception:
        return []


def _load_query_rows(query: str) -> list[dict[str, Any]]:
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        return []
    host = (os.getenv("DATABRICKS_HOST") or "").rstrip("/")
    token = os.getenv("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_PAT")
    if host and token:
        if not host.startswith("http"):
            host = f"https://{host}"
        response = _statement_api(host, token, {"statement": query, "warehouse_id": warehouse_id, "wait_timeout": "20s", "disposition": "INLINE"})
        state = response.get("status", {}).get("state")
        statement_id = response.get("statement_id")
        attempts = 0
        while state in {"PENDING", "RUNNING"} and statement_id and attempts < 10:
            attempts += 1
            time.sleep(1)
            response = _statement_api(host, token, None, statement_id)
            state = response.get("status", {}).get("state")
        if state == "SUCCEEDED":
            columns = [column["name"] for column in response.get("manifest", {}).get("schema", {}).get("columns", [])]
            data = response.get("result", {}).get("data_array", [])
            return [dict(zip(columns, row)) for row in data] if columns else []
    from databricks import sql
    from databricks.sdk.core import Config
    cfg = Config()
    conn = sql.connect(server_hostname=cfg.host, http_path=f"/sql/1.0/warehouses/{warehouse_id}", credentials_provider=lambda: cfg.authenticate)
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            names = [column[0] for column in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
    finally:
        conn.close()

def _load_databricks_facility_rows() -> list[dict[str, Any]]:
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        return []
    statement_rows = _load_statement_execution_rows(warehouse_id)
    if statement_rows:
        return statement_rows
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
    limit = int(os.getenv("CARESIGNAL_DATABRICKS_LIMIT", "250"))
    query = f"SELECT * FROM {FACILITIES_TABLE} LIMIT {limit}"
    conn = sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{warehouse_id}",
        credentials_provider=lambda: cfg.authenticate,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            names = [column[0] for column in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
    finally:
        conn.close()


def _load_statement_execution_rows(warehouse_id: str) -> list[dict[str, Any]]:
    host = (os.getenv("DATABRICKS_HOST") or "").rstrip("/")
    token = os.getenv("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_PAT")
    if not host or not token:
        return []
    if not host.startswith("http"):
        host = f"https://{host}"
    limit = int(os.getenv("CARESIGNAL_DATABRICKS_LIMIT", "250"))
    payload = {
        "statement": f"SELECT * FROM {FACILITIES_TABLE} LIMIT {limit}",
        "warehouse_id": warehouse_id,
        "wait_timeout": "10s",
        "disposition": "INLINE",
    }
    response = _statement_api(host, token, payload)
    state = response.get("status", {}).get("state")
    statement_id = response.get("statement_id")
    attempts = 0
    while state in {"PENDING", "RUNNING"} and statement_id and attempts < 3:
        attempts += 1
        time.sleep(1)
        response = _statement_api(host, token, None, statement_id)
        state = response.get("status", {}).get("state")
    if state != "SUCCEEDED":
        return []
    columns = [column["name"] for column in response.get("manifest", {}).get("schema", {}).get("columns", [])]
    data = response.get("result", {}).get("data_array", [])
    return [dict(zip(columns, row)) for row in data] if columns else []


def _statement_api(host: str, token: str, payload: dict[str, Any] | None, statement_id: str | None = None) -> dict[str, Any]:
    url = f"{host}/api/2.0/sql/statements" if statement_id is None else f"{host}/api/2.0/sql/statements/{statement_id}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib_request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    try:
        with urllib_request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return {}


def _normalize_facility(row: dict[str, Any], index: int) -> Facility:
    lower = {key.lower(): value for key, value in row.items()}
    text_blob = " ".join(str(value) for value in row.values() if value is not None)
    unique_id = str(_first(lower, "unique_id", "id", "facility_id", "uuid") or f"dbx-{index}")
    name = str(_first(lower, "name", "facility_name", "hospital_name", "organisation_name") or f"Facility {index + 1}")
    website = _first(lower, "website", "url", "web_url", "facility_url")
    source_url = _first(lower, "source_url", "source", "reference_url", "data_source_url") or website
    specialty_text = str(_first(lower, "specialties", "speciality", "services", "departments") or text_blob)
    return Facility(
        unique_id=unique_id,
        name=name,
        country=_string_or_none(_first(lower, "country", "country_name")) or "India",
        state=_string_or_none(_first(lower, "state", "state_name", "address_stateorregion")),
        district=_string_or_none(_first(lower, "district", "district_name")),
        city=_string_or_none(_first(lower, "city", "town", "village", "address_city")),
        pincode=_string_or_none(_first(lower, "pincode", "pin_code", "postal_code", "address_postalcode")),
        latitude=_float_or_none(_first(lower, "latitude", "lat", "geo_latitude")),
        longitude=_float_or_none(_first(lower, "longitude", "lon", "lng", "geo_longitude")),
        address=_string_or_none(_first(lower, "address", "street_address", "location")),
        phone=_string_or_none(_first(lower, "phone", "telephone", "mobile", "contact")),
        website=_string_or_none(website),
        source_url=_string_or_none(source_url),
        specialties=_split_values(specialty_text),
        procedures=_infer_terms(text_blob, "terms"),
        equipment=_infer_terms(text_blob, "equipment"),
        capabilities=_infer_terms(text_blob, "capabilities"),
        description=_string_or_none(_first(lower, "description", "about", "remarks")) or text_blob[:500],
        last_updated=_string_or_none(_first(lower, "last_updated", "updated_at", "modified_at")),
        source_row=row,
    )


def fallback_facilities() -> list[Facility]:
    return [
        Facility(
            unique_id="fallback-aravind-madurai",
            name="Aravind Eye Hospital, Madurai",
            state="Tamil Nadu",
            district="Madurai",
            city="Madurai",
            pincode="625020",
            latitude=9.9252,
            longitude=78.1198,
            address="Anna Nagar, Madurai",
            phone="+91-452-4356100",
            website="https://aravind.org",
            source_url="https://aravind.org/hospitals/madurai/",
            specialties=["Ophthalmology", "Retina", "Cataract", "Glaucoma"],
            procedures=["Eye care", "Cataract surgery", "Retina services"],
            equipment=["Ophthalmic laser", "Retinal imaging", "OCT"],
            capabilities=["Cataract", "Retina", "Glaucoma", "Vision screening"],
            description="Large ophthalmology hospital with cataract, retina, glaucoma, pediatric eye care, and outreach services.",
            last_updated="2026-03-20",
        ),
        Facility(
            unique_id="fallback-narayana-bengaluru",
            name="Narayana Institute of Cardiac Sciences",
            state="Karnataka",
            district="Bengaluru Urban",
            city="Bengaluru",
            pincode="560099",
            latitude=12.8110,
            longitude=77.6948,
            address="Bommasandra, Bengaluru",
            phone="+91-80-71222222",
            website="https://www.narayanahealth.org",
            source_url="https://www.narayanahealth.org/hospitals/bangalore/narayana-institute-cardiac-sciences-bommasandra",
            specialties=["Cardiology", "Cardiac surgery", "Critical care"],
            procedures=["CABG", "Cardiac surgery", "Angioplasty"],
            equipment=["Cath lab", "Cardiac ICU", "Ventilator"],
            capabilities=["Bypass", "Cardiac surgery", "Critical care"],
            description="Cardiac sciences center with cardiac surgery, coronary intervention, cath lab services, and cardiac critical care.",
            last_updated="2026-02-14",
        ),
        Facility(
            unique_id="fallback-fortis-delhi",
            name="Fortis Escorts Heart Institute",
            state="Delhi",
            district="South East Delhi",
            city="New Delhi",
            pincode="110025",
            latitude=28.5613,
            longitude=77.2749,
            address="Okhla Road, New Delhi",
            phone="+91-11-47135000",
            website="https://www.fortishealthcare.com",
            source_url="https://www.fortishealthcare.com/location/fortis-escorts-heart-institute-okhla-road",
            specialties=["Cardiology", "CTVS", "Emergency", "Critical care"],
            procedures=["Cardiac surgery", "Emergency care"],
            equipment=["Cath lab", "CTVS operating theatre", "ICU", "Ambulance"],
            capabilities=["Cardiac surgery", "Emergency stabilization", "Critical care"],
            description="Heart institute with cardiac surgery, interventional cardiology, critical care, and emergency support.",
            last_updated="2025-12-01",
        ),
        Facility(
            unique_id="fallback-apollo-chennai",
            name="Apollo Hospitals, Greams Road",
            state="Tamil Nadu",
            district="Chennai",
            city="Chennai",
            pincode="600006",
            latitude=13.0632,
            longitude=80.2514,
            address="Greams Road, Chennai",
            phone="+91-44-28290200",
            website="https://www.apollohospitals.com",
            source_url="https://www.apollohospitals.com/chennai/",
            specialties=["Oncology", "Emergency", "ICU", "Maternity", "Dialysis"],
            procedures=["Oncology", "Emergency care", "Dialysis", "Maternity"],
            equipment=["Linear accelerator", "Dialysis unit", "ICU ventilator", "Ultrasound"],
            capabilities=["Chemotherapy", "Radiation oncology", "Emergency", "Dialysis", "Delivery"],
            description="Multispecialty hospital with oncology, dialysis, emergency, ICU, and maternity services.",
            last_updated="2026-01-10",
        ),
        Facility(
            unique_id="fallback-kokilaben-mumbai",
            name="Kokilaben Dhirubhai Ambani Hospital",
            state="Maharashtra",
            district="Mumbai Suburban",
            city="Mumbai",
            pincode="400053",
            latitude=19.1312,
            longitude=72.8258,
            address="Andheri West, Mumbai",
            phone="+91-22-42699999",
            website="https://www.kokilabenhospital.com",
            source_url="https://www.kokilabenhospital.com/departments/centresofexcellence/centrefor_cancer.html",
            specialties=["Oncology", "Critical care", "Emergency", "Nephrology"],
            procedures=["Cancer care", "ICU", "Dialysis"],
            equipment=["Radiotherapy", "PET CT", "Dialysis machines", "Ventilator"],
            capabilities=["Chemotherapy", "Radiation oncology", "ICU", "Renal care"],
            description="Tertiary facility with cancer care, critical care, emergency support, nephrology, and dialysis services.",
            last_updated="2025-11-05",
        ),
        Facility(
            unique_id="fallback-cloudnine-bengaluru",
            name="Cloudnine Hospital, Jayanagar",
            state="Karnataka",
            district="Bengaluru Urban",
            city="Bengaluru",
            pincode="560011",
            latitude=12.9250,
            longitude=77.5938,
            address="Jayanagar, Bengaluru",
            phone="+91-80-67999999",
            website="https://www.cloudninecare.com",
            source_url="https://www.cloudninecare.com/hospital-locations/bangalore/jayanagar",
            specialties=["Maternity", "Obstetrics", "Gynecology", "Neonatal care"],
            procedures=["Delivery", "Maternity", "Gynecology"],
            equipment=["Labor room", "NICU", "Ultrasound", "Fetal monitor"],
            capabilities=["Delivery", "Obstetrics", "Newborn care", "Gynecology"],
            description="Women and child hospital with maternity, obstetrics, gynecology, neonatal support, and delivery services.",
            last_updated="2026-04-01",
        ),
        Facility(
            unique_id="fallback-aiims-delhi",
            name="AIIMS New Delhi",
            state="Delhi",
            district="New Delhi",
            city="New Delhi",
            pincode="110029",
            latitude=28.5672,
            longitude=77.2100,
            address="Ansari Nagar, New Delhi",
            phone="+91-11-26588500",
            website="https://www.aiims.edu",
            source_url="https://www.aiims.edu",
            specialties=["Emergency", "Trauma", "ICU", "Oncology", "Cardiology", "Ophthalmology"],
            procedures=["Emergency care", "Trauma care", "ICU", "Oncology", "Eye care"],
            equipment=["Trauma center", "Ventilator", "ICU monitor", "Ambulance"],
            capabilities=["Emergency", "Trauma care", "Critical care", "Oncology", "Ophthalmology"],
            description="Public tertiary referral center with emergency, trauma, ICU, oncology, cardiology, and ophthalmology services.",
            last_updated="2025-10-12",
        ),
        Facility(
            unique_id="fallback-renal-hyderabad",
            name="Deccan Renal Care Centre",
            state="Telangana",
            district="Hyderabad",
            city="Hyderabad",
            pincode="500034",
            latitude=17.4126,
            longitude=78.4482,
            address="Banjara Hills, Hyderabad",
            phone="+91-40-44556677",
            website=None,
            source_url="https://example.org/deccan-renal-care",
            specialties=["Nephrology", "Dialysis"],
            procedures=["Dialysis", "Hemodialysis"],
            equipment=["Dialysis machines", "RO plant", "Dialyzer"],
            capabilities=["Dialysis", "Renal care", "Hemodialysis"],
            description="Sample fallback dialysis center with nephrology consultation, hemodialysis, and renal follow-up.",
            last_updated="2026-05-01",
        ),
    ]


def _infer_terms(text: str, key: str) -> list[str]:
    lower = text.lower()
    values: list[str] = []
    for definition in PROCEDURES.values():
        for term in definition.get(key, []):
            term_text = _pretty_term(str(term))
            if term_text.lower() in lower and term_text not in values:
                values.append(term_text)
    return values


def _split_values(value: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parsed: Any = None
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, list):
        parts = [str(part).strip() for part in parsed if str(part).strip()]
    else:
        cleaned = raw.strip("[]")
        parts = [part.strip().strip("'\"") for part in re.split(r"[,;|]", cleaned) if part.strip().strip("'\"")]
    seen: set[str] = set()
    friendly: list[str] = []
    for part in parts:
        item = _pretty_term(part)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            friendly.append(item)
    return friendly[:20]


def _pretty_term(value: str) -> str:
    overrides = {
        "internalMedicine": "Internal medicine",
        "generalSurgery": "General surgery",
        "orthopedicSurgery": "Orthopedic surgery",
        "physicalMedicineAndRehabilitation": "Physical medicine & rehabilitation",
        "oralAndMaxillofacialSurgery": "Oral & maxillofacial surgery",
        "critical": "Critical care",
        "criti": "Critical care",
        "icu": "ICU",
        "ctvs": "CTVS",
        "cabg": "CABG",
    }
    raw = str(value or "").strip().strip("[]'\"")
    if not raw:
        return ""
    if raw in overrides:
        return overrides[raw]
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw)
    spaced = re.sub(r"[_-]+", " ", spaced)
    words = []
    for word in spaced.split():
        lower = word.lower()
        if lower in {"icu", "ctvs", "cabg", "oct", "pet"}:
            words.append(lower.upper())
        elif lower in {"and", "or", "of"}:
            words.append(lower)
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def _first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in [None, ""]:
            return value
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in [None, ""]:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _specialty_group(procedure_id: str) -> str:
    return {
        "eye_care": "Ophthalmology",
        "cardiac_surgery": "Cardiology / CTVS",
        "icu_critical_care": "Critical Care",
        "dialysis": "Nephrology",
        "oncology": "Oncology",
        "maternity_obgyn": "Maternity / OBGYN",
        "emergency_trauma": "Emergency / Trauma",
    }.get(procedure_id, "General")


def _string_or_none(value: Any) -> str | None:
    if value in [None, ""]:
        return None
    return str(value)


def _truthy(value: str | None) -> bool:
    return str(value or "").lower() in {"1", "true", "yes", "on"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
