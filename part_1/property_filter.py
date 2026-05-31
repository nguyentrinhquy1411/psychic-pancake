from __future__ import annotations

from typing import Any, Optional


LISTINGS: list[dict[str, Any]] = [
    {
        "id": "R-100",
        "title": "Studio near District 1",
        "district": "District 1",
        "listing_type": "rent",
        "price": 750,
        "bedrooms": 1,
        "area_sqm": 32,
        "available": True,
    },
    {
        "id": "R-101",
        "title": "Two bedroom apartment in Thao Dien",
        "district": "Thao Dien",
        "listing_type": "rent",
        "price": 1400,
        "bedrooms": 2,
        "area_sqm": 78,
        "available": True,
    },
    {
        "id": "S-200",
        "title": "Condo for sale in Binh Thanh",
        "district": "Binh Thanh",
        "listing_type": "sale",
        "price": 180000,
        "bedrooms": 2,
        "area_sqm": 70,
        "available": True,
    },
    {
        "id": "R-102",
        "title": "Unavailable rental listing",
        "district": "District 7",
        "listing_type": "rent",
        "price": 900,
        "bedrooms": 2,
        "area_sqm": 65,
        "available": False,
    },
    {
        "id": "BROKEN-1",
        "title": "Missing valid price",
        "district": "District 1",
        "listing_type": "rent",
        "price": "contact us",
        "bedrooms": 1,
        "area_sqm": 40,
        "available": True,
    },
]

REQUIRED_FIELDS = ("id", "district", "listing_type", "price", "bedrooms", "area_sqm", "available")
VALID_LISTING_TYPES = {"rent", "sale"}


def _is_numeric(value: Any) -> bool:
    """Return True if value is an int or float (but not a bool)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_record(record: dict[str, Any]) -> Optional[str]:
    """
    Validate a single listing record.

    Returns None when the record is valid, or a human-readable reason string
    when a validation rule is violated. Checks are ordered so that the first
    failing rule is reported (missing field takes precedence).
    """
    # Check every required field is present and not None.
    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None:
            return "missing field"

    if not _is_numeric(record["price"]):
        return "invalid price"

    # bedrooms must be a non-negative integer (bool excluded).
    if not isinstance(record["bedrooms"], int) or isinstance(record["bedrooms"], bool):
        return "invalid bedrooms"

    if not _is_numeric(record["area_sqm"]):
        return "invalid area_sqm"

    if not isinstance(record["available"], bool):
        return "invalid available"

    if record["listing_type"] not in VALID_LISTING_TYPES:
        return "invalid listing_type"

    return None


def _matches_filters(
    record: dict[str, Any],
    listing_type: str,
    max_price: float,
    district: Optional[str],
    min_bedrooms: int,
    only_available: bool,
) -> bool:
    """Return True when a valid record satisfies all supplied filter criteria."""
    if record["listing_type"] != listing_type:
        return False

    if district and record["district"].lower() != district.lower():
        return False

    if record["price"] > max_price:
        return False

    if record["bedrooms"] < min_bedrooms:
        return False

    if only_available and not record["available"]:
        return False

    return True


def filter_listings(
    listings: list[dict[str, Any]],
    listing_type: str,
    max_price: float,
    district: Optional[str] = None,
    min_bedrooms: int = 0,
    only_available: bool = True,
) -> dict[str, Any]:
    """
    Return a summary dictionary with this exact shape:

    {
        "matching_ids": list[str],
        "match_count": int,
        "average_price": float | None,
        "counts_by_district": dict[str, int],
        "invalid_records": list[dict[str, str]],
    }

    Rules:
    - Accept listing_type "rent" or "sale" only.
    - Skip invalid records and include {"id": <id>, "reason": <reason>}.
    - A valid record must have id, district, listing_type, numeric price,
      integer bedrooms, numeric area_sqm, and boolean available.
    - Match records with the requested listing_type.
    - If district is provided, match it case-insensitively.
    - Match records with price <= max_price and bedrooms >= min_bedrooms.
    - If only_available is True, exclude unavailable listings.
    - Keep matching_ids in the same order as the input.
    - average_price is None when there are no matches.
    - Do not mutate the input listings.
    """
    matching_ids: list[str] = []
    prices: list[float] = []
    counts_by_district: dict[str, int] = {}
    invalid_records: list[dict[str, str]] = []

    for record in listings:
        # Use .get() so we can still retrieve an id for the error report even
        # when other fields are missing.
        record_id = record.get("id", "<unknown>")

        reason = _validate_record(record)
        if reason is not None:
            invalid_records.append({"id": str(record_id), "reason": reason})
            continue

        if not _matches_filters(record, listing_type, max_price, district, min_bedrooms, only_available):
            continue

        matching_ids.append(record["id"])
        prices.append(record["price"])
        district_name: str = record["district"]
        counts_by_district[district_name] = counts_by_district.get(district_name, 0) + 1

    average_price: Optional[float] = sum(prices) / len(prices) if prices else None

    return {
        "matching_ids": matching_ids,
        "match_count": len(matching_ids),
        "average_price": average_price,
        "counts_by_district": counts_by_district,
        "invalid_records": invalid_records,
    }


def run_tests() -> None:
    result = filter_listings(
        LISTINGS,
        listing_type="rent",
        max_price=1000,
        district="district 1",
        min_bedrooms=1,
    )
    assert result["matching_ids"] == ["R-100"]
    assert result["match_count"] == 1
    assert result["average_price"] == 750
    assert result["counts_by_district"] == {"District 1": 1}
    assert result["invalid_records"] == [
        {"id": "BROKEN-1", "reason": "invalid price"}
    ]

    sale_result = filter_listings(
        LISTINGS,
        listing_type="sale",
        max_price=200000,
        min_bedrooms=2,
    )
    assert sale_result["matching_ids"] == ["S-200"]
    assert sale_result["average_price"] == 180000

    empty_result = filter_listings(
        LISTINGS,
        listing_type="rent",
        max_price=500,
    )
    assert empty_result["matching_ids"] == []
    assert empty_result["average_price"] is None

    print("All tests passed")


if __name__ == "__main__":
    run_tests()
