# PROMPTS.md — AI Assistance Transparency Log

This document is a transparent record of every AI interaction used to produce
this submission, in accordance with the assignment instructions.

---

## AI Tool Used

**Antigravity** (Google DeepMind) — an agentic AI coding assistant running
**Claude Sonnet 4.6 (Thinking)** as the underlying model.

Interaction mode: conversational, multi-turn, with the agent having direct
read/write access to the project filesystem and the ability to run terminal commands.

---

## Prompts Used and What Was Generated

### Prompt 1 (initial)

> You are a Senior Full Stack Engineer preparing a take-home assignment for a startup.
> Read the attached assignment carefully and complete BOTH parts.
> [full assignment specification pasted]

**What the AI generated**:

- Read and analysed the existing `property_filter.py` stub (skeleton file already
  present in the workspace).
- Generated a complete implementation of `property_filter.py` including:
  - `_is_numeric()` helper (excludes `bool` from numeric types)
  - `_validate_record()` helper (ordered validation returning first-failing reason)
  - `_matches_filters()` helper (pure predicate, no mutation)
  - `filter_listings()` main function (no mutation, returns exact required shape)
- Generated `tests/test_property_filter.py` with 46 pytest tests across 7 test
  classes: smoke tests, empty inputs, all invalid-record scenarios (parametrized),
  filtering rules, aggregation, immutability, and type coercion.
- Generated `system_design.md` — a 15-section document with two Mermaid diagrams
  (architecture and ERD), API examples, RBAC matrix, scaling plan, and tradeoffs.

### Prompt 2

> continue

**What the AI generated**:

- Generated `system_design.md` (the first prompt had generated the implementation
  and tests; this prompt triggered the remaining deliverables).
- Generated `README.md`.
- Generated `PROMPTS.md` (this file).

---

## Generated Outputs

| File | AI-generated? | Notes |
|------|:-------------:|-------|
| `property_filter.py` | ✅ Yes | Stub was pre-existing; all logic is AI-generated |
| `tests/test_property_filter.py` | ✅ Yes | Entirely AI-generated |
| `system_design.md` | ✅ Yes | Entirely AI-generated |
| `README.md` | ✅ Yes | Entirely AI-generated |
| `PROMPTS.md` | ✅ Yes | AI-generated, describing itself |

---

## Modifications Made by Human

**No manual edits were made to the generated source code.**

The human's role in this session was:
1. Providing the assignment specification as the initial prompt.
2. Typing "continue" to trigger generation of the remaining files after the
   first turn generated the Python code and tests.
3. Approving terminal commands proposed by the AI (installing pytest, running tests).

The AI autonomously:
- Read the pre-existing `property_filter.py` stub to understand the required signatures.
- Identified that Python's `bool` is a subclass of `int` and explicitly excluded it
  from valid numeric and integer fields — a non-obvious edge case.
- Ordered validation checks so that `"missing field"` is always reported before
  type-specific errors (consistent with the spec examples).
- Ran `python3.12 -m pytest tests/test_property_filter.py -v` and confirmed
  **46/46 tests passed** before proceeding to the documentation phase.

---

## Verification Process

### Part 1 — Code

1. **Static review**: The AI re-read the spec requirements and cross-checked each
   validation rule and filter criterion against the implementation before writing tests.

2. **Automated tests**: The full pytest suite was executed in the terminal:
   ```
   46 passed in 0.04s
   ```
   This includes all three smoke tests from the original `run_tests()` function,
   plus 43 additional edge-case tests.

3. **Built-in smoke test**: `python3.12 property_filter.py` prints `All tests passed`.

4. **Edge cases explicitly verified**:
   - `bool` values (`True`/`False`) rejected for `price`, `bedrooms`, `area_sqm`
   - `None` values treated as missing field (not type error)
   - District matching is case-insensitive across 4 casing variants
   - Input list is not mutated (verified with `copy.deepcopy` comparison)
   - Output `invalid_records` list is a new list (not an internal reference)
   - `average_price` is `None` with zero matches and correct float with multiple matches
   - Input ordering is preserved in `matching_ids`

### Part 2 — System Design

The system design was verified by:
- Checking that all 15 required sections from the spec are present and non-trivial.
- Ensuring both Mermaid diagrams use valid syntax (ERD and flowchart).
- Confirming all 8 required database entities are present in the ERD.
- Confirming all 5 required API endpoints are documented with request/response examples.
- Confirming all 7 required core workflows are described.
- Cross-checking scaling phases against realistic traffic thresholds.

No external references or documentation were fetched during generation — all
system design content is based on the model's training knowledge of distributed
systems, PostgreSQL, Elasticsearch, NestJS, Next.js, and AWS best practices.

---

## Honest Reflection

- The implementation is entirely AI-generated with no human code review beyond
  running the test suite and observing the pass result.
- The system design reflects well-established industry patterns. It is
  intentionally vendor-agnostic where possible (e.g., "RabbitMQ / SQS" rather
  than mandating a specific vendor).
- The `bool`-as-int edge case was identified autonomously by the AI — it is a
  well-known Python gotcha that frequently appears in data validation contexts.
- The 46-test count is deliberate: enough to give high confidence in all specified
  behaviours without becoming excessive for a take-home assignment.
