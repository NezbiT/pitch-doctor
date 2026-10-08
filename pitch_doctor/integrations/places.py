"""Google Places API (New) lookup for a business's Google Business Profile.

Two things keep this cheap. First, **field masking**: the Places API bills per
requested field group, so ``FIELD_MASK`` below asks for exactly the fields the
google_business check reads and nothing more. Second, a **SQLite cache with a
TTL**: a business's profile changes on the order of weeks, while a freelancer
prospecting a town re-scans the same names constantly, so repeat lookups
inside the TTL cost nothing.

Failure is always a value, never an exception: no API key, a quota error, or a
dead network all come back as a ``GbpProfile`` with ``error`` set, so the check
can report an honest degraded state instead of a false "looks good".
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from pathlib import Path

import httpx

from pitch_doctor.models import GbpProfile

API_KEY_ENV_VAR = "GOOGLE_PLACES_API_KEY"
CACHE_DIR_ENV_VAR = "PITCH_DOCTOR_CACHE_DIR"

SEARCH_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"

# Exactly the fields the check reads. Every addition here costs money on every
# uncached lookup, so keep this list honest -- notably we do *not* request
# ``places.reviews`` (the most expensive tier) because it still would not tell
# us whether the owner replied, which is the only thing we'd want it for.
FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.primaryType",
        "places.primaryTypeDisplayName",
        "places.businessStatus",
        "places.photos",
        "places.regularOpeningHours",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
    )
)

CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
CACHE_FILENAME = "places-cache.db"


def api_key() -> str | None:
    key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return key or None


def default_cache_path() -> Path:
    base = os.environ.get(CACHE_DIR_ENV_VAR, "").strip()
    root = Path(base) if base else Path.home() / ".pitch-doctor"
    return root / CACHE_FILENAME


def build_query(business_name: str, city: str | None) -> str:
    """The text query sent to Places, and also the cache key."""
    parts = [business_name.strip()]
    if city and city.strip():
        parts.append(city.strip())
    return ", ".join(parts)


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------


def _connect(cache_path: Path) -> sqlite3.Connection:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cache_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS places_cache (
            query      TEXT PRIMARY KEY,
            fetched_at REAL NOT NULL,
            payload    TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def read_cache(query: str, cache_path: Path, ttl: float = CACHE_TTL_SECONDS) -> dict | None:
    """The cached Places payload for ``query``, or None if absent or stale."""
    try:
        conn = _connect(cache_path)
    except (sqlite3.Error, OSError):
        return None  # An unusable cache path must never break a scan.
    try:
        row = conn.execute(
            "SELECT fetched_at, payload FROM places_cache WHERE query = ?", (query,)
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()

    if row is None:
        return None
    fetched_at, payload = row
    if time.time() - fetched_at > ttl:
        return None
    try:
        return json.loads(payload)
    except ValueError:
        return None


def write_cache(query: str, payload: dict, cache_path: Path) -> None:
    try:
        conn = _connect(cache_path)
    except (sqlite3.Error, OSError):
        return
    try:
        conn.execute(
            "INSERT OR REPLACE INTO places_cache (query, fetched_at, payload) VALUES (?, ?, ?)",
            (query, time.time(), json.dumps(payload)),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def parse_place(payload: dict) -> GbpProfile:
    """Turn a raw ``places:searchText`` payload into a GbpProfile.

    Pure and offline: this is where the tests do their work.
    """
    places = payload.get("places") or []
    if not places:
        return GbpProfile(found=False)

    place = places[0]
    display_name = place.get("displayName") or {}
    primary_type_display = place.get("primaryTypeDisplayName") or {}
    hours = place.get("regularOpeningHours") or {}

    return GbpProfile(
        found=True,
        place_id=place.get("id"),
        name=display_name.get("text") if isinstance(display_name, dict) else None,
        formatted_address=place.get("formattedAddress"),
        primary_type=(
            primary_type_display.get("text")
            if isinstance(primary_type_display, dict) and primary_type_display.get("text")
            else place.get("primaryType")
        ),
        business_status=place.get("businessStatus"),
        has_hours=bool(hours.get("periods") or hours.get("weekdayDescriptions")),
        photo_count=len(place.get("photos") or []),
        rating=place.get("rating"),
        review_count=place.get("userRatingCount") or 0,
        # Places exposes no owner-reply field at any tier, so "reviews the
        # owner never answered" is unknowable here rather than zero.
        reviews_without_reply=None,
        website_uri=place.get("websiteUri"),
        phone=place.get("nationalPhoneNumber"),
    )


# --------------------------------------------------------------------------
# Lookup
# --------------------------------------------------------------------------


async def fetch_place(query: str, timeout: float, key: str) -> dict:
    """Raw Places call. Raises httpx errors; callers turn those into a profile."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            SEARCH_TEXT_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": FIELD_MASK,
            },
            json={"textQuery": query, "maxResultCount": 1},
        )
    if response.status_code != 200:
        raise httpx.HTTPStatusError(
            f"Places API returned {response.status_code}: {response.text[:200]}",
            request=response.request,
            response=response,
        )
    return response.json()


async def lookup_business(
    business_name: str | None,
    city: str | None,
    *,
    timeout: float = 20.0,
    cache_path: Path | None = None,
    ttl: float = CACHE_TTL_SECONDS,
) -> GbpProfile:
    """Look up a Google Business Profile, via cache when possible.

    Never raises: every failure mode lands in ``GbpProfile.error``.
    """
    if not business_name or not business_name.strip():
        return GbpProfile(found=False, error="no business name to search for")

    key = api_key()
    if key is None:
        return GbpProfile(
            found=False,
            error=f"Google Places API key ({API_KEY_ENV_VAR}) is not configured. This check will be skipped.",
        )

    query = build_query(business_name, city)
    resolved_cache = cache_path or default_cache_path()

    cached = await asyncio.to_thread(read_cache, query, resolved_cache, ttl)
    if cached is not None:
        profile = parse_place(cached)
        profile.from_cache = True
        return profile

    try:
        payload = await fetch_place(query, timeout, key)
    except (httpx.HTTPError, ValueError) as exc:
        return GbpProfile(found=False, error=str(exc))

    await asyncio.to_thread(write_cache, query, payload, resolved_cache)
    return parse_place(payload)
