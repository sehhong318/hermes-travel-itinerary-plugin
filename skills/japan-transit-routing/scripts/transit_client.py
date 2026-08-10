#!/usr/bin/env python3
"""Small, dependency-free client for the optional Transit API."""

from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.transit.ls8h.com"
DEFAULT_TIMEOUT = 10


class TransitServiceError(RuntimeError):
    """Raised when optional transit data cannot be used safely."""


def _request_json(
    path: str,
    params: dict[str, Any],
    *,
    opener: Callable[..., Any] = urlopen,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "hermes-travel-itinerary/2"})
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, JSONDecodeError, UnicodeDecodeError) as error:
        raise TransitServiceError(
            "Transit API unavailable; use an official operator journey planner "
            "or a user-visible map app, and label the result as recheck-required."
        ) from error
    if not isinstance(payload, dict):
        raise TransitServiceError("Transit API returned an unexpected response shape.")
    return payload


def suggest_places(
    query: str,
    *,
    limit: int = 5,
    opener: Callable[..., Any] = urlopen,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Return validated station/place suggestions from the optional API."""
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    payload = _request_json(
        "/api/v1/places/suggest",
        {"q": query, "limit": limit},
        opener=opener,
        timeout=timeout,
    )
    places = payload.get("places")
    if not isinstance(places, list) or any(
        not isinstance(place, dict)
        or not isinstance(place.get("endpoint"), str)
        or not place["endpoint"]
        for place in places
    ):
        raise TransitServiceError("Transit API returned an unexpected response shape.")
    return payload


def _has_name(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("name"), str)
        and bool(value["name"].strip())
    )


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_journey(value: object, transit_modes: set[str]) -> bool:
    if not isinstance(value, dict):
        return False
    departure = value.get("departureSecs")
    arrival = value.get("arrivalSecs")
    duration = value.get("durationSecs")
    transfer_count = value.get("transferCount")
    if not all(
        _is_nonnegative_int(item)
        for item in (departure, arrival, duration, transfer_count)
    ):
        return False
    assert isinstance(departure, int)
    assert isinstance(arrival, int)
    assert isinstance(duration, int)
    departure_secs = departure
    arrival_secs = arrival
    duration_secs = duration
    if duration_secs == 0 or arrival_secs < departure_secs:
        return False
    legs = value.get("legs")
    if not isinstance(legs, list) or not legs:
        return False
    for leg in legs:
        if not isinstance(leg, dict) or not _has_name(leg.get("from")) or not _has_name(
            leg.get("to")
        ):
            return False
        mode = leg.get("mode")
        if mode is not None and not isinstance(mode, str):
            return False
        leg_departure = leg.get("departureSecs")
        leg_arrival = leg.get("arrivalSecs")
        if not _is_nonnegative_int(leg_departure) or not _is_nonnegative_int(
            leg_arrival
        ):
            return False
        assert isinstance(leg_departure, int)
        assert isinstance(leg_arrival, int)
        if leg_arrival < leg_departure:
            return False
        if str(mode or "").upper() in transit_modes:
            line = leg.get("line")
            route_name = leg.get("routeName")
            if not (
                (isinstance(route_name, str) and bool(route_name.strip()))
                or (isinstance(line, dict) and bool(line))
                or (isinstance(line, str) and bool(line.strip()))
            ):
                return False
    return True


def plan_route(
    origin: str,
    destination: str,
    *,
    date: str,
    time: str,
    route_type: str = "departure",
    num_itineraries: int = 3,
    opener: Callable[..., Any] = urlopen,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Plan a route and discard walk-only or malformed journeys."""
    if not origin.strip() or not destination.strip():
        raise ValueError("origin and destination endpoints must not be empty")
    if re.fullmatch(r"\d{8}", date) is None:
        raise ValueError("date must use YYYYMMDD")
    if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time) is None:
        raise ValueError("time must use HH:MM")
    if route_type not in {"departure", "arrival", "first", "last"}:
        raise ValueError("route_type must be departure, arrival, first, or last")
    if not 1 <= num_itineraries <= 5:
        raise ValueError("num_itineraries must be between 1 and 5")

    payload = _request_json(
        "/api/v1/plan",
        {
            "from": origin,
            "to": destination,
            "date": date,
            "time": time,
            "type": route_type,
            "numItineraries": num_itineraries,
        },
        opener=opener,
        timeout=timeout,
    )
    journeys = payload.get("journeys")
    if (
        not isinstance(payload.get("timezone"), str)
        or not payload["timezone"]
        or not _has_name(payload.get("from"))
        or not _has_name(payload.get("to"))
        or not isinstance(journeys, list)
    ):
        raise TransitServiceError("Transit API returned an unexpected response shape.")
    transit_modes = {"RAIL", "SUBWAY", "BUS", "TRAM", "FERRY"}
    filtered = []
    for journey in journeys:
        if not _valid_journey(journey, transit_modes):
            raise TransitServiceError("Transit API returned an unexpected response shape.")
        if any(
            str(leg.get("mode", "")).upper() in transit_modes
            for leg in journey["legs"]
        ):
            filtered.append(journey)
    if not filtered:
        raise TransitServiceError(
            "Transit API returned no usable public-transit journey; use an official "
            "operator journey planner or a user-visible map app and recheck on departure day."
        )
    return {**payload, "journeys": filtered}
