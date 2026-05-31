# Real Estate Marketplace — Take-Home Assignment

A production-quality solution to the take-home coding and system design assignment.
The project implements a property listing filter in Python and a full system design
document for a real estate marketplace.

---

## Project Structure

```
.
├── property_filter.py          # Part 1 — core implementation
├── system_design.md            # Part 2 — system design document
├── tests/
│   └── test_property_filter.py # Pytest test suite (46 tests)
├── README.md
└── PROMPTS.md
```

---

## Setup

**Requirements**: Python 3.12+

1. **Clone / unzip the project** and navigate into the directory:

   ```bash
   cd /path/to/project
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies** (only `pytest` is needed):

   ```bash
   pip install pytest
   ```

   No other third-party packages are required — `property_filter.py` uses only
   the Python standard library.

---

## Run Instructions

### Run the built-in smoke tests

```bash
python3.12 property_filter.py
# Expected output: All tests passed
```

---

## Test Instructions

Run the full pytest suite:

```bash
python3.12 -m pytest tests/test_property_filter.py -v
```

Expected output: **46 passed**.

Run with coverage (optional, requires `pytest-cov`):

```bash
pip install pytest-cov
python3.12 -m pytest tests/test_property_filter.py -v --cov=property_filter --cov-report=term-missing
```

---

## Part 1 — `property_filter.py`

### What it does

`filter_listings()` accepts a list of raw listing dictionaries and filter criteria,
then returns a summary dict with the shape:

```python
{
    "matching_ids": list[str],          # IDs of matching listings, input order preserved
    "match_count": int,                 # len(matching_ids)
    "average_price": float | None,      # None when no matches
    "counts_by_district": dict[str, int],
    "invalid_records": list[dict[str, str]],  # {"id": ..., "reason": ...}
}
```

### Validation rules (in priority order)

| Rule | Error reason |
|------|-------------|
| Any required field is absent or `None` | `"missing field"` |
| `price` is not a numeric (int/float, not bool) | `"invalid price"` |
| `bedrooms` is not an integer (bool excluded) | `"invalid bedrooms"` |
| `area_sqm` is not a numeric (int/float, not bool) | `"invalid area_sqm"` |
| `available` is not a `bool` | `"invalid available"` |
| `listing_type` is not `"rent"` or `"sale"` | `"invalid listing_type"` |

### Filter criteria

| Parameter | Default | Behaviour |
|-----------|---------|-----------|
| `listing_type` | required | Exact match (`"rent"` or `"sale"`) |
| `max_price` | required | `price <= max_price` |
| `district` | `None` | Case-insensitive match; `None` matches all districts |
| `min_bedrooms` | `0` | `bedrooms >= min_bedrooms` |
| `only_available` | `True` | When `True`, excludes `available=False` listings |

---

## Part 2 — `system_design.md`

A 15-section system design document covering:

- Functional and non-functional requirements
- Six user roles and their permissions
- Seven core workflows (listing creation, moderation, search, etc.)
- High-level architecture diagram (embedded image) with component responsibilities
- Full ERD (embedded image) for eight entities
- REST API design with request/response examples
- Search strategy: PostgreSQL MVP → Elasticsearch at scale
- Media handling: pre-signed S3 uploads, CDN, automated photo moderation
- RBAC permission matrix
- Reliability: caching, rate limiting, circuit breakers, backups
- Observability: structured logs, Prometheus metrics, Grafana dashboards, alerts
- Fraud prevention: duplicate detection, stale listing cleanup, spam scoring
- Three-phase scaling plan with migration triggers
- Documented tradeoffs and alternatives considered
- MVP scope vs. deferred features with reasoning

---

## Assumptions

- The `listing_type` filter in `filter_listings()` is always a valid value provided
  by the caller; invalid values simply yield no matches (since no valid record will
  share that type).
- `bool` is treated as invalid for `price`, `bedrooms`, and `area_sqm` even though
  Python's `bool` is a subclass of `int`. This avoids silent data quality issues
  where `True`/`False` slip through as numeric values.
- `average_price` is the arithmetic mean of matched listing prices (not weighted).
- District matching is purely string-based (case-insensitive). No fuzzy or
  geographic matching is performed in the Python module.
- The system design targets a Vietnamese real estate context (Ho Chi Minh City /
  Hanoi) but is written generically enough to apply globally.

---

## Limitations

- `filter_listings()` is a pure in-memory function; it does not paginate results.
  Callers with very large listing lists should paginate upstream.
- The module has no logging or metrics instrumentation; a production integration
  would add these at the service layer.
- The system design assumes managed cloud services (AWS or equivalent). A
  bare-metal / on-premises adaptation would require additional infrastructure work.
- Photo content moderation and geospatial search are described architecturally
  but not implemented in this submission.
