"""
Pytest test suite for property_filter.filter_listings().

Covers the provided smoke tests plus exhaustive edge-case coverage as required
by the assignment specification.
"""
from __future__ import annotations

from typing import Any

import pytest

from property_filter import LISTINGS, filter_listings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def base_listings() -> list[dict[str, Any]]:
    """Return a clean copy of the module-level LISTINGS fixture."""
    return [dict(record) for record in LISTINGS]


def make_listing(**overrides: Any) -> dict[str, Any]:
    """Return a minimal valid rent listing with any field overridden."""
    base: dict[str, Any] = {
        "id": "T-001",
        "district": "District 1",
        "listing_type": "rent",
        "price": 500.0,
        "bedrooms": 1,
        "area_sqm": 40.0,
        "available": True,
    }
    base.update(overrides)
    return base


# ===========================================================================
# 1. Provided smoke tests (must pass without modification)
# ===========================================================================


class TestProvidedSmokeTests:
    def test_rent_filter_with_district(self, base_listings: list[dict[str, Any]]) -> None:
        result = filter_listings(
            base_listings,
            listing_type="rent",
            max_price=1000,
            district="district 1",
            min_bedrooms=1,
        )
        assert result["matching_ids"] == ["R-100"]
        assert result["match_count"] == 1
        assert result["average_price"] == 750
        assert result["counts_by_district"] == {"District 1": 1}
        assert result["invalid_records"] == [{"id": "BROKEN-1", "reason": "invalid price"}]

    def test_sale_filter(self, base_listings: list[dict[str, Any]]) -> None:
        result = filter_listings(
            base_listings,
            listing_type="sale",
            max_price=200000,
            min_bedrooms=2,
        )
        assert result["matching_ids"] == ["S-200"]
        assert result["average_price"] == 180000

    def test_no_matches_returns_none_average(self, base_listings: list[dict[str, Any]]) -> None:
        result = filter_listings(
            base_listings,
            listing_type="rent",
            max_price=500,
        )
        assert result["matching_ids"] == []
        assert result["average_price"] is None


# ===========================================================================
# 2. Empty and trivial inputs
# ===========================================================================


class TestEmptyAndTrivialInputs:
    def test_empty_listings(self) -> None:
        result = filter_listings([], listing_type="rent", max_price=9999)
        assert result["matching_ids"] == []
        assert result["match_count"] == 0
        assert result["average_price"] is None
        assert result["counts_by_district"] == {}
        assert result["invalid_records"] == []

    def test_single_valid_match(self) -> None:
        listing = make_listing(id="X-1", price=300)
        result = filter_listings([listing], listing_type="rent", max_price=300)
        assert result["matching_ids"] == ["X-1"]
        assert result["match_count"] == 1
        assert result["average_price"] == 300
        assert result["counts_by_district"] == {"District 1": 1}
        assert result["invalid_records"] == []


# ===========================================================================
# 3. Validation — invalid records
# ===========================================================================


class TestInvalidRecords:
    @pytest.mark.parametrize("missing_field", [
        "id", "district", "listing_type", "price", "bedrooms", "area_sqm", "available",
    ])
    def test_missing_required_field(self, missing_field: str) -> None:
        listing = make_listing()
        del listing[missing_field]
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        # Record is invalid; nothing should match
        assert result["matching_ids"] == []
        assert len(result["invalid_records"]) == 1
        assert result["invalid_records"][0]["reason"] == "missing field"

    def test_invalid_price_string(self) -> None:
        listing = make_listing(price="call us")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"] == [{"id": "T-001", "reason": "invalid price"}]

    def test_invalid_price_none(self) -> None:
        listing = make_listing(price=None)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"][0]["reason"] == "missing field"

    def test_invalid_price_bool(self) -> None:
        # bool is a subclass of int in Python; must be rejected as a price.
        listing = make_listing(price=True)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"][0]["reason"] == "invalid price"

    def test_invalid_bedrooms_float(self) -> None:
        listing = make_listing(bedrooms=1.5)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"] == [{"id": "T-001", "reason": "invalid bedrooms"}]

    def test_invalid_bedrooms_string(self) -> None:
        listing = make_listing(bedrooms="two")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"][0]["reason"] == "invalid bedrooms"

    def test_invalid_bedrooms_bool(self) -> None:
        # bool must not be accepted as a bedroom count.
        listing = make_listing(bedrooms=True)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"][0]["reason"] == "invalid bedrooms"

    def test_invalid_area_sqm_string(self) -> None:
        listing = make_listing(area_sqm="big")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"] == [{"id": "T-001", "reason": "invalid area_sqm"}]

    def test_invalid_available_string(self) -> None:
        listing = make_listing(available="yes")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"] == [{"id": "T-001", "reason": "invalid available"}]

    def test_invalid_available_int(self) -> None:
        listing = make_listing(available=1)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"][0]["reason"] == "invalid available"

    def test_invalid_listing_type(self) -> None:
        listing = make_listing(listing_type="lease")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["invalid_records"] == [{"id": "T-001", "reason": "invalid listing_type"}]

    def test_multiple_invalid_records(self) -> None:
        listings = [
            make_listing(id="BAD-1", price="N/A"),
            make_listing(id="BAD-2", bedrooms=2.5),
            make_listing(id="BAD-3", area_sqm="large"),
        ]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        reasons = {r["id"]: r["reason"] for r in result["invalid_records"]}
        assert reasons["BAD-1"] == "invalid price"
        assert reasons["BAD-2"] == "invalid bedrooms"
        assert reasons["BAD-3"] == "invalid area_sqm"
        assert result["matching_ids"] == []


# ===========================================================================
# 4. Filtering rules
# ===========================================================================


class TestFilteringRules:
    def test_district_case_insensitive(self) -> None:
        listing = make_listing(id="D-1", district="Binh Thanh")
        for variant in ("binh thanh", "BINH THANH", "Binh Thanh", "bInH tHaNh"):
            result = filter_listings([listing], listing_type="rent", max_price=9999, district=variant)
            assert result["matching_ids"] == ["D-1"], f"Failed for variant: {variant!r}"

    def test_district_no_match(self) -> None:
        listing = make_listing(id="D-1", district="District 1")
        result = filter_listings([listing], listing_type="rent", max_price=9999, district="District 7")
        assert result["matching_ids"] == []
        assert result["match_count"] == 0

    def test_district_none_matches_all(self) -> None:
        listings = [
            make_listing(id="A", district="District 1"),
            make_listing(id="B", district="District 7"),
        ]
        result = filter_listings(listings, listing_type="rent", max_price=9999, district=None)
        assert set(result["matching_ids"]) == {"A", "B"}

    def test_price_boundary_included(self) -> None:
        listing = make_listing(id="P-1", price=1000)
        result = filter_listings([listing], listing_type="rent", max_price=1000)
        assert result["matching_ids"] == ["P-1"]

    def test_price_above_max_excluded(self) -> None:
        listing = make_listing(id="P-2", price=1001)
        result = filter_listings([listing], listing_type="rent", max_price=1000)
        assert result["matching_ids"] == []

    def test_min_bedrooms_boundary(self) -> None:
        listing = make_listing(id="B-1", bedrooms=2)
        result = filter_listings([listing], listing_type="rent", max_price=9999, min_bedrooms=2)
        assert result["matching_ids"] == ["B-1"]

    def test_min_bedrooms_below_threshold_excluded(self) -> None:
        listing = make_listing(id="B-2", bedrooms=1)
        result = filter_listings([listing], listing_type="rent", max_price=9999, min_bedrooms=2)
        assert result["matching_ids"] == []

    def test_unavailable_excluded_when_only_available_true(self) -> None:
        listing = make_listing(id="U-1", available=False)
        result = filter_listings([listing], listing_type="rent", max_price=9999, only_available=True)
        assert result["matching_ids"] == []

    def test_unavailable_included_when_only_available_false(self) -> None:
        listing = make_listing(id="U-2", available=False)
        result = filter_listings([listing], listing_type="rent", max_price=9999, only_available=False)
        assert result["matching_ids"] == ["U-2"]

    def test_mixed_rent_and_sale_only_rent_returned(self) -> None:
        listings = [
            make_listing(id="R-1", listing_type="rent"),
            make_listing(id="S-1", listing_type="sale"),
        ]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        assert result["matching_ids"] == ["R-1"]

    def test_mixed_rent_and_sale_only_sale_returned(self) -> None:
        listings = [
            make_listing(id="R-1", listing_type="rent"),
            make_listing(id="S-1", listing_type="sale"),
        ]
        result = filter_listings(listings, listing_type="sale", max_price=9999)
        assert result["matching_ids"] == ["S-1"]

    def test_order_preserved(self) -> None:
        listings = [make_listing(id=f"X-{i}") for i in range(5, 0, -1)]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        assert result["matching_ids"] == ["X-5", "X-4", "X-3", "X-2", "X-1"]


# ===========================================================================
# 5. Aggregation
# ===========================================================================


class TestAggregation:
    def test_average_price_single_match(self) -> None:
        listing = make_listing(price=800)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["average_price"] == 800.0

    def test_average_price_multiple_matches(self) -> None:
        listings = [
            make_listing(id="A", price=600),
            make_listing(id="B", price=900),
            make_listing(id="C", price=750),
        ]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        assert result["average_price"] == pytest.approx(750.0)

    def test_average_price_none_when_no_matches(self) -> None:
        result = filter_listings([], listing_type="rent", max_price=9999)
        assert result["average_price"] is None

    def test_counts_by_district_multiple_districts(self) -> None:
        listings = [
            make_listing(id="A", district="District 1"),
            make_listing(id="B", district="District 1"),
            make_listing(id="C", district="District 7"),
        ]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        assert result["counts_by_district"] == {"District 1": 2, "District 7": 1}

    def test_counts_by_district_empty_when_no_matches(self) -> None:
        result = filter_listings([], listing_type="rent", max_price=9999)
        assert result["counts_by_district"] == {}

    def test_match_count_equals_len_matching_ids(self) -> None:
        listings = [make_listing(id=f"X-{i}") for i in range(4)]
        result = filter_listings(listings, listing_type="rent", max_price=9999)
        assert result["match_count"] == len(result["matching_ids"])


# ===========================================================================
# 6. Immutability
# ===========================================================================


class TestImmutability:
    def test_input_listings_not_mutated(self) -> None:
        original = [make_listing()]
        import copy
        snapshot = copy.deepcopy(original)
        filter_listings(original, listing_type="rent", max_price=9999)
        assert original == snapshot

    def test_invalid_records_list_not_mutated(self) -> None:
        """Invalid records output should be a new list, not a reference to internals."""
        listing = make_listing(price="bad")
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        result["invalid_records"].clear()
        # Re-running should still return the same invalid records
        result2 = filter_listings([listing], listing_type="rent", max_price=9999)
        assert len(result2["invalid_records"]) == 1


# ===========================================================================
# 7. Price as float / int coercion
# ===========================================================================


class TestPriceTypes:
    def test_price_as_int_is_valid(self) -> None:
        listing = make_listing(price=500)
        result = filter_listings([listing], listing_type="rent", max_price=500)
        assert result["matching_ids"] == ["T-001"]

    def test_price_as_float_is_valid(self) -> None:
        listing = make_listing(price=499.99)
        result = filter_listings([listing], listing_type="rent", max_price=500)
        assert result["matching_ids"] == ["T-001"]

    def test_area_sqm_as_int_is_valid(self) -> None:
        listing = make_listing(area_sqm=50)
        result = filter_listings([listing], listing_type="rent", max_price=9999)
        assert result["matching_ids"] == ["T-001"]
