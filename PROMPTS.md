# PROMPTS.md — AI Assistance Transparency Log

This file records AI-assisted work done for this repository.

---

## AI Tool Used

- **Primary coding assistant**: conversational AI agent with read/write access to the project filesystem and terminal commands.
- **Interaction style**: multi-turn prompt/response, iterative generation, then verification.

---

## Prompt History

> Note: The exact wording of older prompts may vary slightly. The sequences below reflect the actual work products present in the repository.

### A) Part 1 (Python filtering task)

#### Prompt 1

> Read the assignment and complete Part 1 implementation + tests.

**AI output generated**
- `property_filter.py` implementation
- `tests/test_property_filter.py`

#### Prompt 2

> Continue and finish remaining deliverables.

**AI output generated**
- `README.md`
- initial `PROMPTS.md`

---

### B) Part 2 — MVP (`part_2_mvp`) 

Requested sequence (as specified):
1. **MVP first**
2. **Generate image system overview**
3. **Generate ERD**
4. **Define caching strategy on backend and frontend**
5. **Verify**

#### Prompt M1 — MVP design first

> Create the MVP system design document only (scope, architecture, APIs, workflows, tradeoffs).

**AI output generated**
- `part_2_mvp/mvp_design.md`

#### Prompt M2 — System overview image

> Generate/export a visual system overview diagram for MVP architecture.

**AI output generated**
- `part_2_mvp/mvp_architecture.png`

#### Prompt M3 — ERD image

> Generate/export an MVP ERD diagram image.

**AI output generated**
- `part_2_mvp/mvp_erd.png`

#### Prompt M4 — Cache strategy (BE + FE)

> Provide backend and frontend caching strategy for MVP.

**AI output generated**
- `part_2_mvp/redis_caching_strategy.md` (backend/Redis strategy)
- `part_2_mvp/cache-key-design-tanstack-query.md` (frontend/TanStack Query key design)

#### Prompt M5 — Verify

> Verify consistency between MVP design, diagrams, and cache strategy.

**AI action/output**
- Cross-check of architecture/data-flow alignment across the MVP files.

---

### C) Part 2 — Scale (`part_2_scale`)

Requested sequence (same flow applied to scale):
1. **Scale design first**
2. **Generate image system overview**
3. **Generate ERD**
4. **Define caching strategy on backend and frontend**
5. **Verify**

#### Prompt S1 — Scale design first

> Create the scale/production system design for 10x growth.

**AI output generated**
- `part_2_scale/system_design.md`

#### Prompt S2 — System overview image

> Generate/export a scalable architecture diagram image.

**AI output generated**
- `part_2_scale/architecture_diagram.png`

#### Prompt S3 — ERD image

> Generate/export a scale-phase ERD diagram image.

**AI output generated**
- `part_2_scale/erd_diagram.png`

#### Prompt S4 — Cache strategy (BE + FE)

> Define backend and frontend caching strategy for scale phase.

**AI output generated**
- Caching approach documented inside `part_2_scale/system_design.md` (Redis/service caching and client caching behavior).

#### Prompt S5 — Verify

> Verify architecture, ERD, and caching strategy coherence for scale phase.

**AI action/output**
- Cross-check of consistency among scale design artifacts.

---

### D) Interview Demo App (`demo`)

#### Prompt D1 — React MVP cache demo

> Read `part_2_mvp` and make a quick demo in `demo` about the main parts to demo with an interviewer. Use React like the MVP design and focus on infinite loading, Redis cache, query cache, etc.

**AI output generated**
- `demo/package.json` — React + Vite + TanStack Query demo dependencies/scripts
- `demo/index.html` — Vite app entry point
- `demo/src/main.jsx` — interactive demo simulating infinite search, Redis cache, PostgreSQL fallback, listing detail cache, and invalidation
- `demo/src/styles.css` — polished demo UI styling
- `demo/README.md` — run instructions and interviewer talking track
- `demo/assets/mvp_architecture.png` and `demo/assets/mvp_erd.png` copied from MVP artifacts for reference

**Verification**
- Ran `npm install` in `demo`.
- Ran `npm run build` successfully with Vite 5.4.21.

#### Prompt D2 — Fix demo runtime error

> Fix `Uncaught ReferenceError: id is not defined` in the React demo and use the attached shadcn/find-skills guidance.

**AI output generated**
- Fixed JSX text in `demo/src/main.jsx` so `listing:detail:{id}` is rendered as literal explanatory text instead of being parsed as a JavaScript expression.
- Checked shadcn project status with `npx shadcn@latest info --json`; the demo is not currently initialized as a shadcn/Tailwind project (`config: null`, no installed components).

**Verification**
- Ran `npm run build` successfully after the fix.

#### Prompt D3 — Expand demo data and Redis explanation

> Add more data to the demo and explain how Redis is demonstrated in this repo.

**AI output generated**
- Added more seeded listings in `demo/src/main.jsx` so infinite loading has multiple realistic pages.
- Added more districts to the filter UI.
- Added an in-app Redis explainer panel describing search cache, detail cache, miss/hit behavior, TTLs, and invalidation.
- Expanded `demo/README.md` with a detailed explanation of how the mock Redis layer maps to the real MVP Redis strategy.

**Verification**
- Ran `npm run build` successfully after the updates.

#### Prompt D4 — Clarify detail-page cache chain

> Make sure the page detail is cached too. The flow should be: FE cache miss → Redis miss → DB.

**AI output generated**
- Added frontend cache event logging for search and listing-detail requests in `demo/src/main.jsx`.
- Added explicit listing-detail click handling that logs FE query cache hits/misses before the API/Redis layer.
- Updated the frontend cache clear action so the same listing can be re-clicked to demonstrate Redis detail-cache hits.
- Updated `demo/README.md` to explain the detail-page chain: TanStack Query cache → Redis `listing:detail:{id}` → PostgreSQL fallback.

**Verification**
- Ran `npm run build` successfully after the updates.

#### Prompt D5 — Add MVP design benchmark for demo

> Make the benchmark for the `demo` design using the MVP assumptions: 50,000 active listings, 500,000 monthly visitors, and 5,000 agents/owners.

**AI output generated**
- Added `demo/benchmark/cache-flow-benchmark.mjs`, a Node benchmark for the demo cache architecture.
- Added `npm run benchmark` in `demo/package.json`.
- Generated `demo/benchmark/cache-flow-report.md` with MVP assumption mapping and p95 results for 50k, 100k, and 250k synthetic listings.
- Updated `demo/README.md` with benchmark instructions and the 50k-listing result summary.

**Verification**
- Ran `npm run benchmark` successfully in `demo`.
- Ran `npm run build` successfully after adding the benchmark.
- Latest 50k-listing results: search cold p95 `5.863 ms`, Redis search p95 `0.068 ms`, FE search p95 `0.034 ms`, Redis detail p95 `0.01 ms`.

---

## AI-Generated Outputs (Current Repository)

| File | AI-generated? | Notes |
|------|:-------------:|-------|
| `property_filter.py` | ✅ Yes | Implemented from assignment stub/spec |
| `tests/test_property_filter.py` | ✅ Yes | Automated test coverage for Part 1 |
| `README.md` | ✅ Yes | Project-level guidance |
| `PROMPTS.md` | ✅ Yes | This transparency record |
| `part_2_mvp/mvp_design.md` | ✅ Yes | MVP-only design document |
| `part_2_mvp/mvp_architecture.png` | ✅ Yes | MVP architecture visual |
| `part_2_mvp/mvp_erd.png` | ✅ Yes | MVP ERD visual |
| `part_2_mvp/redis_caching_strategy.md` | ✅ Yes | Backend caching strategy |
| `part_2_mvp/cache-key-design-tanstack-query.md` | ✅ Yes | Frontend cache key strategy |
| `part_2_scale/system_design.md` | ✅ Yes | Scale-phase design document |
| `part_2_scale/architecture_diagram.png` | ✅ Yes | Scale architecture visual |
| `part_2_scale/erd_diagram.png` | ✅ Yes | Scale ERD visual |
| `demo/package.json` | ✅ Yes | React/Vite demo project config |
| `demo/index.html` | ✅ Yes | Demo HTML entry point |
| `demo/src/main.jsx` | ✅ Yes | Interactive MVP cache demo |
| `demo/src/styles.css` | ✅ Yes | Demo visual design |
| `demo/README.md` | ✅ Yes | Run instructions and interviewer talking track |
| `demo/assets/mvp_architecture.png` | ✅ Yes | Copied from MVP artifact for demo reference |
| `demo/assets/mvp_erd.png` | ✅ Yes | Copied from MVP artifact for demo reference |

---

## Verification Summary

### Part 1
- Python tests were run and passed during generation session.
- Validation logic and edge-case handling were reviewed against the assignment behavior.

### Part 2 (MVP + Scale)
- Artifacts were checked for document/diagram consistency.
- Architecture and ERD outputs match their corresponding markdown design documents.
- Caching strategy is present for MVP explicitly (dedicated docs) and for Scale within system design guidance.

### Demo App
- `npm install` completed in `demo`.
- `npm run build` completed successfully using Vite 5.4.21 on Node 20.17.0.

---

## Human Involvement

- Provided assignment requirements and iterative prompts.
- Directed generation order (MVP first, then diagram/ERD/cache/verify; same for scale).
- Requested updates to this transparency log for accuracy and completeness.
