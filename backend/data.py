from __future__ import annotations

import os
import re
import uuid
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request as urllib_request
from urllib.error import URLError

from .models import Facility, ScenarioShortlistRequest, ShortlistRequest, UserActionRequest, VerificationRequest, VoiceRequest
from .scoring import PROCEDURES


APP_SCHEMA = "lakebase_hackathon_demo.public"
FACILITIES_TABLE = f"{APP_SCHEMA}.facilities_gold_sync"
PINCODE_TABLE = f"{APP_SCHEMA}.india_post_pincode_directory_gold_sync"
NFHS_TABLE = "databricks_virtue_foundation_dataset_dais_2026.virtue_foundation_dataset.nfhs_5_district_health_indicators"
LAKEBASE_PG_ENDPOINT = os.getenv("CARESIGNAL_LAKEBASE_ENDPOINT", "projects/hackathon-demo/branches/production/endpoints/primary")
LAKEBASE_PG_HOST = os.getenv("PGHOST", "ep-sweet-hill-d8yapkbw.database.us-east-2.cloud.databricks.com")
LAKEBASE_PG_DATABASE = os.getenv("PGDATABASE", "publicdata")
LAKEBASE_PG_USER = os.getenv("PGUSER", "788bd6cb-634c-462f-94f1-7d81a436be59")
_LAKEBASE_TOKEN_CACHE: dict[str, Any] = {}
INDIA_STATES_AND_UTS = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

FACILITY_QUERY_COLUMNS = [
    "sync_pk",
    "unique_id",
    "name",
    "Name_Standardized",
    "organization_type",
    "officialPhone",
    "phone_numbers",
    "email",
    "officialWebsite",
    "websites",
    "address_line1",
    "address_line2",
    "address_city",
    "address_stateOrRegion",
    "address_zipOrPostcode",
    "address_country",
    "description",
    "specialties",
    "procedure",
    "equipment",
    "capability",
    "recency_of_page_update",
    "source",
    "latitude",
    "longitude",
    "source_urls",
    "service_tags_json",
    "service_tag_count",
    "facility_trust_score",
    "trust_tier",
    "review_flag",
    "primary_service_tag",
]


class DataStore:
    def __init__(self) -> None:
        self._facilities: list[Facility] | None = None
        self._pincode_locations: list[dict[str, Any]] | None = None
        self._location_filter_rows: list[dict[str, Any]] | None = None
        self._verifications: list[dict[str, Any]] = []
        self._shortlists: list[dict[str, Any]] = []
        self._user_actions: list[dict[str, Any]] = []
        self._scenario_shortlists: list[dict[str, Any]] = []
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
        # Keep filters fast and complete: use the bundled cache first instead of blocking dropdowns on live Lakebase queries.
        cache = _load_location_filter_cache()
        location_filter_rows = cache.get("state_cities") or self.location_filter_rows()
        cached_pincodes = cache.get("pincodes") or []
        locations = [] if cached_pincodes else self.location_dimensions()

        def options(values):
            cleaned = sorted({_clean_location_label(v) for v in values if _clean_location_label(v)})
            return [{"value": value, "label": value} for value in cleaned]

        state_values = list(INDIA_STATES_AND_UTS) + list(cache.get("states") or []) + [row.get("state") for row in location_filter_rows] + [row.get("state") for row in locations]
        city_values = [row.get("city") for row in location_filter_rows] or [row.get("city") for row in locations]
        state_city_pairs = [
            {"state": _clean_location_label(row["state"]), "city": _clean_location_label(row["city"])}
            for row in location_filter_rows
            if row.get("state") and row.get("city")
        ]
        return {
            "countries": [{"value": "India", "label": "India"}],
            "states": options(state_values),
            "cities": options(city_values),
            "state_cities": state_city_pairs,
            "pincodes": options(cached_pincodes or [row.get("postal_code") for row in locations]),
            "services": self.service_groupings(),
            "age_groups": [
                {"value": "all", "label": "All age groups"},
                {"value": "child", "label": "Children / pediatric"},
                {"value": "adult", "label": "Adults"},
                {"value": "senior", "label": "Seniors"},
            ],
        }

    def location_filter_rows(self) -> list[dict[str, Any]]:
        if self._location_filter_rows is None:
            self._location_filter_rows = _load_location_filter_rows()
        return self._location_filter_rows

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
        self.add_user_action(
            UserActionRequest(
                user_id=request.verifier_name or "demo-user",
                facility_id=request.unique_id,
                action_type="review",
                action_data={"procedure": request.procedure, "status": request.status, "notes": request.notes, "evidence_url": request.evidence_url},
            )
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
        self.add_user_action(
            UserActionRequest(
                user_id=request.planner_name or "demo-user",
                facility_id=request.unique_id,
                action_type="shortlist",
                action_data={"procedure": request.procedure, "notes": request.notes},
            )
        )
        return record

    def add_user_action(self, request: UserActionRequest) -> dict[str, Any]:
        now = _now_iso()
        record = {
            "action_id": str(uuid.uuid4()),
            "user_id": request.user_id or "demo-user",
            "facility_id": request.facility_id,
            "action_type": request.action_type,
            "action_data": request.action_data or {},
            "created_at": now,
            "updated_at": now,
        }
        self._user_actions.append(record)
        self._insert_lakebase(
            "user_actions",
            record,
        )
        return record

    def recent_user_actions(self, limit: int = 50, facility_id: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if facility_id:
            rows = self._select_lakebase(
                "SELECT action_id, user_id, facility_id, action_type, action_data, created_at, updated_at FROM public.user_actions WHERE facility_id = %s ORDER BY created_at DESC LIMIT %s",
                [facility_id, limit],
            )
        else:
            rows = self._select_lakebase(
                "SELECT action_id, user_id, facility_id, action_type, action_data, created_at, updated_at FROM public.user_actions ORDER BY created_at DESC LIMIT %s",
                [limit],
            )
        if not rows:
            rows = [row for row in reversed(self._user_actions) if not facility_id or row.get("facility_id") == facility_id][:limit]
        return [self._normalize_action_record(row) for row in rows[:limit]]

    def save_scenario_shortlist(self, request: ScenarioShortlistRequest) -> dict[str, Any]:
        now = _now_iso()
        location = request.location or "India"
        record = {
            "shortlist_id": str(uuid.uuid4()),
            "user_id": request.user_id or "demo-user",
            "location": location,
            "service": request.service,
            "facility_ids": request.facility_ids,
            "created_at": now,
            "title": request.title,
            "notes": request.notes,
        }
        self._scenario_shortlists.append(record)
        self._insert_lakebase(
            "shortlists",
            {
                "shortlist_id": record["shortlist_id"],
                "user_id": record["user_id"],
                "location": record["location"],
                "service": record["service"],
                "facility_ids": record["facility_ids"],
                "created_at": record["created_at"],
            },
        )
        self.add_user_action(
            UserActionRequest(
                user_id=record["user_id"],
                facility_id=request.facility_ids[0] if request.facility_ids else None,
                action_type="scenario",
                action_data={
                    "title": request.title,
                    "notes": request.notes,
                    "location": location,
                    "service": request.service,
                    "facility_ids": request.facility_ids,
                },
            )
        )
        return record

    def recent_scenario_shortlists(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._select_lakebase(
            "SELECT shortlist_id, user_id, location, service, facility_ids, created_at FROM public.shortlists ORDER BY created_at DESC LIMIT %s",
            [limit],
        ) or list(reversed(self._scenario_shortlists[-limit:]))
        return [self._normalize_shortlist_record(row) for row in rows[:limit]]

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

    def _normalize_action_record(self, row: dict[str, Any]) -> dict[str, Any]:
        record = dict(row)
        action_data = record.get("action_data")
        if isinstance(action_data, str):
            try:
                record["action_data"] = json.loads(action_data)
            except json.JSONDecodeError:
                record["action_data"] = {"value": action_data}
        elif action_data is None:
            record["action_data"] = {}
        for key in ["created_at", "updated_at"]:
            if isinstance(record.get(key), datetime):
                record[key] = record[key].isoformat()
        return record

    def _normalize_shortlist_record(self, row: dict[str, Any]) -> dict[str, Any]:
        record = dict(row)
        facility_ids = record.get("facility_ids")
        if isinstance(facility_ids, str):
            text = facility_ids.strip("{}")
            record["facility_ids"] = [item for item in text.split(",") if item]
        elif facility_ids is None:
            record["facility_ids"] = []
        else:
            record["facility_ids"] = list(facility_ids)
        if isinstance(record.get("created_at"), datetime):
            record["created_at"] = record["created_at"].isoformat()
        return record

    def _select_lakebase(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        try:
            conn = _connect_lakebase()
        except Exception:
            return []
        if conn is None:
            return []
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params or [])
                    columns = [column[0] for column in (cursor.description or [])]
                    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return rows
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return []

    def _insert_lakebase(self, table: str, values: dict[str, Any]) -> bool:
        try:
            conn = _connect_lakebase()
        except Exception:
            return False
        if conn is None:
            return False
        columns = list(values)
        placeholders = ", ".join(["%s"] * len(columns))
        column_sql = ", ".join(columns)
        sql = f"INSERT INTO public.{table} ({column_sql}) VALUES ({placeholders})"
        try:
            from psycopg2.extras import Json

            encoded_values = [Json(values[column]) if isinstance(values[column], dict) else values[column] for column in columns]
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, encoded_values)
            conn.close()
            return True
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return False



def _lakebase_password() -> str | None:
    password = os.getenv("PGPASSWORD")
    if password:
        return password
    now = time.time()
    cached_token = _LAKEBASE_TOKEN_CACHE.get("token")
    cached_expiry = float(_LAKEBASE_TOKEN_CACHE.get("expires_at", 0) or 0)
    if cached_token and cached_expiry - now > 300:
        return str(cached_token)
    try:
        from databricks.sdk import WorkspaceClient

        credential = WorkspaceClient().postgres.generate_database_credential(LAKEBASE_PG_ENDPOINT)
        token = getattr(credential, "token", None)
        expire_time = getattr(credential, "expire_time", None)
        expires_at = now + 3300
        if expire_time:
            try:
                expires_at = datetime.fromisoformat(str(expire_time).replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass
        if token:
            _LAKEBASE_TOKEN_CACHE.update({"token": token, "expires_at": expires_at})
            return str(token)
    except Exception:
        return None
    return None


def _connect_lakebase():
    password = _lakebase_password()
    if not password:
        return None
    try:
        import psycopg2

        return psycopg2.connect(
            host=LAKEBASE_PG_HOST,
            database=LAKEBASE_PG_DATABASE,
            user=LAKEBASE_PG_USER,
            password=password,
            port=os.getenv("PGPORT", "5432"),
            sslmode=os.getenv("PGSSLMODE", "require"),
        )
    except Exception:
        return None


def _location_label_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


_CANONICAL_STATE_BY_KEY = {_location_label_key(state): state for state in INDIA_STATES_AND_UTS}
_LOCATION_CACHE: dict[str, Any] | None = None


def _load_location_filter_cache() -> dict[str, Any]:
    global _LOCATION_CACHE
    if _LOCATION_CACHE is not None:
        return _LOCATION_CACHE
    cache_path = Path(__file__).with_name("location_cache.json")
    try:
        data = json.loads(cache_path.read_text())
    except Exception:
        data = {}
    state_cities = data.get("state_cities") if isinstance(data, dict) else []
    states = data.get("states") if isinstance(data, dict) else []
    pincodes = data.get("pincodes") if isinstance(data, dict) else []
    _LOCATION_CACHE = {
        "states": states if isinstance(states, list) else [],
        "state_cities": state_cities if isinstance(state_cities, list) else [],
        "pincodes": pincodes if isinstance(pincodes, list) else [],
    }
    return _LOCATION_CACHE


def _clean_location_label(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.lower() in {"na", "n/a", "none", "null", "nan"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return _CANONICAL_STATE_BY_KEY.get(_location_label_key(text), text)


def _load_location_filter_rows() -> list[dict[str, Any]]:
    query = f"""
        WITH official_states AS (
          SELECT DISTINCT statename AS state
          FROM {PINCODE_TABLE}
          WHERE pincode IS NOT NULL
            AND statename IS NOT NULL
            AND lower(trim(statename)) NOT IN ('', 'na', 'n/a', 'none', 'null')
        ), location_pairs AS (
          SELECT statename AS state, district AS city
          FROM {PINCODE_TABLE}
          WHERE pincode IS NOT NULL
            AND statename IS NOT NULL
            AND district IS NOT NULL
            AND lower(trim(statename)) NOT IN ('', 'na', 'n/a', 'none', 'null')
            AND lower(trim(district)) NOT IN ('', 'na', 'n/a', 'none', 'null')
          UNION
          SELECT address_stateOrRegion AS state, address_city AS city
          FROM {FACILITIES_TABLE}
          WHERE address_stateOrRegion IN (SELECT state FROM official_states)
            AND address_city IS NOT NULL
            AND lower(trim(address_city)) NOT IN ('', 'na', 'n/a', 'none', 'null')
        )
        SELECT DISTINCT
          'India' AS country,
          state,
          city
        FROM location_pairs
        ORDER BY state, city
    """
    try:
        rows = _load_query_rows(query)
    except Exception:
        return []
    cleaned: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        state = _clean_location_label(row.get("state"))
        city = _clean_location_label(row.get("city"))
        if not state or not city:
            continue
        key = (state, city)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"country": "India", "state": state, "city": city})
    return cleaned


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
          AND statename IS NOT NULL
          AND district IS NOT NULL
          AND lower(trim(statename)) NOT IN ('', 'na', 'n/a', 'none', 'null')
          AND lower(trim(district)) NOT IN ('', 'na', 'n/a', 'none', 'null')
        GROUP BY statename, district, pincode, latitude, longitude
        ORDER BY state, city, postal_code
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
    rows = _execute_statement_rows(query, warehouse_id, wait_timeout="20s", attempts=10)
    if rows:
        return rows
    return _execute_sql_connector_rows(query, warehouse_id)


def _load_databricks_facility_rows() -> list[dict[str, Any]]:
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
    if not warehouse_id:
        return []
    limit = int(os.getenv("CARESIGNAL_DATABRICKS_LIMIT", "250"))
    chunk_size = max(50, int(os.getenv("CARESIGNAL_DATABRICKS_CHUNK_SIZE", "250")))
    query_columns = ", ".join(f"`{column}`" for column in FACILITY_QUERY_COLUMNS)
    rows: list[dict[str, Any]] = []
    for offset in range(0, limit, chunk_size):
        chunk_limit = min(chunk_size, limit - offset)
        query = f"""
            SELECT {query_columns}
            FROM {FACILITIES_TABLE}
            ORDER BY sync_pk
            LIMIT {chunk_limit} OFFSET {offset}
        """
        chunk = _execute_statement_rows(query, warehouse_id, wait_timeout="20s", attempts=10)
        if not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < chunk_limit:
            break
    return rows


def _execute_statement_rows(query: str, warehouse_id: str, wait_timeout: str = "20s", attempts: int = 10) -> list[dict[str, Any]]:
    payload = {
        "statement": query,
        "warehouse_id": warehouse_id,
        "wait_timeout": wait_timeout,
        "on_wait_timeout": "CONTINUE",
        "disposition": "INLINE",
    }
    response: dict[str, Any] = {}
    host = (os.getenv("DATABRICKS_HOST") or "").rstrip("/")
    token = os.getenv("DATABRICKS_TOKEN") or os.getenv("DATABRICKS_PAT")
    if host and token:
        if not host.startswith("http"):
            host = f"https://{host}"
        response = _statement_api(host, token, payload)
        statement_id = response.get("statement_id")
        state = response.get("status", {}).get("state")
        poll_attempts = 0
        while state in {"PENDING", "RUNNING"} and statement_id and poll_attempts < attempts:
            poll_attempts += 1
            time.sleep(1)
            response = _statement_api(host, token, None, statement_id)
            state = response.get("status", {}).get("state")
    else:
        try:
            from databricks.sdk import WorkspaceClient

            client = WorkspaceClient()
            response = client.api_client.do("POST", "/api/2.0/sql/statements/", body=payload)
            statement_id = response.get("statement_id")
            state = response.get("status", {}).get("state")
            poll_attempts = 0
            while state in {"PENDING", "RUNNING"} and statement_id and poll_attempts < attempts:
                poll_attempts += 1
                time.sleep(1)
                response = client.api_client.do("GET", f"/api/2.0/sql/statements/{statement_id}")
                state = response.get("status", {}).get("state")
        except Exception:
            return []
    if response.get("status", {}).get("state") != "SUCCEEDED":
        return []
    columns = [column["name"] for column in response.get("manifest", {}).get("schema", {}).get("columns", [])]
    data = response.get("result", {}).get("data_array", [])
    return [dict(zip(columns, row)) for row in data] if columns else []


def _execute_sql_connector_rows(query: str, warehouse_id: str) -> list[dict[str, Any]]:
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()
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
    unique_id = str(_first(lower, "sync_pk", "unique_id", "id", "facility_id", "uuid") or f"dbx-{index}")
    name = str(
        _first(lower, "name_standardized", "name", "facility_name", "hospital_name", "organisation_name")
        or f"Facility {index + 1}"
    )
    website = _first_url(lower, "officialwebsite", "website", "websites", "url", "web_url", "facility_url")
    source_url = _first_url(lower, "source_urls", "source_url", "source", "reference_url", "data_source_url", "websites") or website
    specialty_text = str(
        _first(lower, "service_tags_json", "service_tags", "specialties", "speciality", "services", "departments")
        or text_blob
    )
    return Facility(
        unique_id=unique_id,
        name=name,
        country=_string_or_none(_first(lower, "address_country", "country", "country_name")) or "India",
        state=_string_or_none(_first(lower, "address_stateorregion", "state", "state_name")),
        district=_string_or_none(_first(lower, "district", "district_name")),
        city=_string_or_none(_first(lower, "address_city", "city", "town", "village")),
        pincode=_string_or_none(_first(lower, "address_ziporpostcode", "pincode", "pin_code", "postal_code", "address_postalcode")),
        latitude=_float_or_none(_first(lower, "latitude", "lat", "geo_latitude")),
        longitude=_float_or_none(_first(lower, "longitude", "lon", "lng", "geo_longitude")),
        address=_string_or_none(
            _first(lower, "address", "street_address", "location", "address_line1", "address_line2", "address_line3")
        ),
        phone=_string_or_none(_first(lower, "officialphone", "phone", "phone_numbers", "telephone", "mobile", "contact")),
        website=_string_or_none(website),
        source_url=_string_or_none(source_url),
        specialties=_split_values(specialty_text),
        procedures=_infer_terms(text_blob, "terms"),
        equipment=_infer_terms(text_blob, "equipment"),
        capabilities=_infer_terms(text_blob, "capabilities"),
        description=_string_or_none(_first(lower, "description", "about", "remarks")) or text_blob[:500],
        last_updated=_string_or_none(_first(lower, "recency_of_page_update", "last_updated", "updated_at", "modified_at")),
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


def _first_url(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value in [None, "", "null"]:
            continue
        candidates: list[str]
        if isinstance(value, str) and value.strip().startswith("["):
            try:
                parsed = json.loads(value)
                candidates = [str(item).strip() for item in parsed if item not in [None, "", "null"]]
            except json.JSONDecodeError:
                candidates = [value]
        else:
            candidates = [str(value).strip()]
        for candidate in candidates:
            if not candidate or candidate.lower() == "null":
                continue
            if candidate.startswith(("http://", "https://")):
                return candidate
            if "." in candidate and " " not in candidate:
                return candidate
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
