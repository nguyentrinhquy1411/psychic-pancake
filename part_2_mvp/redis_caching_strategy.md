# Redis Caching Strategy — Real Estate Marketplace

> **Structure**: MVP caches ship on day one. "Phase 2+" caches are introduced when
> the corresponding scaling trigger in [`system_design.md §13`](./system_design.md) is hit.

---

## Guiding Principles

1. **Cache reads, not writes** — never cache data that must be immediately consistent after a write.
2. **Smallest useful TTL** — shorter TTLs reduce stale-data risk; longer TTLs reduce DB load. Find the minimum that gives meaningful relief.
3. **Invalidate on mutation** — every write path that changes cached data must also delete the relevant cache key(s).
4. **Document every key** — key naming and TTL must live here, not scattered across the codebase.
5. **Redis is not your DB** — if Redis goes down, the app must degrade gracefully (read from PostgreSQL).

---

## Key Naming Convention

```
<namespace>:<resource>:<identifier>[:<variant>]
```

| Segment | Example |
|---------|---------|
| Namespace | `listing`, `search`, `user`, `rate`, `session` |
| Resource | `detail`, `results`, `wishlist`, `count` |
| Identifier | UUID, hash of query params, user ID |
| Variant | `page:2`, `district:thao-dien` |

Examples:
```
listing:detail:550e8400-e29b-41d4-a716-446655440000
search:results:a3f2c1d8e9b4  (md5 of normalized query params)
user:wishlist:count:uuid-user
rate:inquiry:ip:203.0.113.42
session:refresh:uuid-user
```

---

## MVP Caches (Phase 1)

These are the **minimum viable cache entries** — each one pays for itself at day-one traffic.

---

### 1. Listing Detail Page

**What**: Full serialized listing response (title, price, photos, agent info, etc.)

**Why**: The most expensive read — requires joining `listings + listing_photos + users`.
Every listing detail page view hits this key.

| Property | Value |
|----------|-------|
| Key | `listing:detail:{listing_id}` |
| Structure | `STRING` (serialized JSON) |
| TTL | **5 minutes** |
| Set on | Successful `GET /listings/:id` cache miss |
| Invalidated on | `PATCH /listings/:id` · status change (approve/reject) · photo add/delete |

```typescript
// Read-through pattern
async getListingDetail(id: string): Promise<ListingDetailDto> {
  const cacheKey = `listing:detail:${id}`;
  const cached = await this.redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const listing = await this.listingsRepo.findDetailById(id);
  await this.redis.set(cacheKey, JSON.stringify(listing), 'EX', 300);
  return listing;
}

// Invalidation on update
async updateListing(id: string, dto: UpdateListingDto): Promise<void> {
  await this.listingsRepo.update(id, dto);
  await this.redis.del(`listing:detail:${id}`);
}
```

---

### 2. Search Results

**What**: Paginated search result page (list of listing summaries matching a given filter set)

**Why**: Popular searches (e.g., "2BR rent in Thao Dien under $1500") are fired repeatedly
by many users simultaneously. PostgreSQL FTS with indexes handles this fine at < 50k listings,
but caching eliminates redundant identical queries.

| Property | Value |
|----------|-------|
| Key | `search:results:{md5(normalized_params)}` |
| Structure | `STRING` (serialized JSON) |
| TTL | **60 seconds** |
| Set on | Cache miss on `GET /listings` |
| Invalidated on | **Not actively invalidated** — TTL expiry is acceptable for search results (60 s staleness is fine; a just-published listing appearing after 1 min is acceptable) |

```typescript
function buildSearchCacheKey(params: SearchParams): string {
  // Normalize: sort keys, lowercase strings, remove undefined
  const normalized = JSON.stringify(
    Object.fromEntries(
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => [k, typeof v === 'string' ? v.toLowerCase() : v]),
    ),
  );
  return `search:results:${createHash('md5').update(normalized).digest('hex')}`;
}
```

> **Caveat**: Do not cache search results that include unavailable or pending listings.
> Only cache queries where `only_available=true` and `status=active` is enforced.

---

### 3. Rate-Limit Counters

**What**: Per-IP and per-email request counters for throttled endpoints

**Why**: In-memory counters don't survive restarts and don't work across multiple API
instances. Redis gives a shared, atomic counter across all nodes from day one.

| Endpoint | Key | TTL | Limit |
|----------|-----|-----|-------|
| All public endpoints | `rate:global:ip:{ip}` | 60 s | 100 req/min |
| `POST /inquiries` | `rate:inquiry:ip:{ip}` | 60 s | 5 req/min |
| `POST /inquiries` | `rate:inquiry:email:{email_hash}` | 86400 s (1 day) | 20 req/day |
| `POST /auth/login` | `rate:auth:ip:{ip}` | 60 s | 10 req/min |

```typescript
// Using INCR + EXPIRE (atomic in Redis)
async checkRateLimit(key: string, limit: number, windowSecs: number): Promise<boolean> {
  const count = await this.redis.incr(key);
  if (count === 1) {
    await this.redis.expire(key, windowSecs); // set TTL only on first increment
  }
  return count <= limit;
}
```

---

### 4. Session / Refresh Token Denylist

**What**: A set of revoked JWT refresh tokens (logout and rotation)

**Why**: JWTs are stateless — the only way to enforce logout before token expiry is to
maintain a server-side denylist.

| Property | Value |
|----------|-------|
| Key | `session:denied:{jti}` (JWT ID claim) |
| Structure | `STRING` with value `"1"` |
| TTL | Remaining lifetime of the original refresh token (7 days max) |
| Set on | `POST /auth/logout` · token rotation (old token added to denylist) |
| Checked on | Every refresh token validation |

> **Alternative**: Use a `SET` keyed per user (`session:denied:user:{uid}`) and store
> JTIs as members — cheaper if a user logs out of all devices simultaneously.

---

### 5. Bull Job Queue (Implicit)

Bull uses Redis as its backing store for all job queues. No application-level keys to manage — Bull handles its own key namespace (`bull:{queue-name}:*`). Ensure Redis has enough memory for job payloads (photo processing jobs are the largest: ~2 KB each).

---

## Phase 2+ Caches (Growth & Scale)

Introduce these when traffic justifies the added operational complexity.

---

### 6. User Wishlist (Saved Listings)

**What**: The full list of listing IDs saved by a given user

**Why**: `GET /saved-listings` joins `saved_listings + listings + listing_photos`. At
thousands of active users constantly opening their wishlists, this becomes a hot read path.

| Property | Value |
|----------|-------|
| Key | `user:wishlist:{user_id}` |
| Structure | `SET` of listing UUIDs |
| TTL | **24 hours** (refreshed on access) |
| Set on | First wishlist load after cache miss |
| Invalidated on | Save / unsave action (add/remove member from SET, or DEL and rehydrate) |

```typescript
// O(1) membership check — "is this listing saved by this user?"
async isListingSaved(userId: string, listingId: string): Promise<boolean> {
  return this.redis.sismember(`user:wishlist:${userId}`, listingId) === 1;
}

// Add on save
await this.redis.sadd(`user:wishlist:${userId}`, listingId);

// Remove on unsave
await this.redis.srem(`user:wishlist:${userId}`, listingId);
```

---

### 7. District / Filter Facet Counts

**What**: Aggregate counts of active listings per district (used to power filter UI badges like "District 1 (42)")

**Why**: Computing `COUNT(*) GROUP BY district` on every search page load is expensive
when listing count grows beyond 100k. Facet counts can be slightly stale — 5 min is fine.

| Property | Value |
|----------|-------|
| Key | `listing:counts:district:{listing_type}` |
| Structure | `HASH` — field: district name, value: count |
| TTL | **5 minutes** |
| Set on | Cache miss |
| Invalidated on | Listing approved / rejected / expired (use TTL expiry rather than active DEL) |

```typescript
// Retrieve all district counts for rent listings
const counts = await this.redis.hgetall('listing:counts:district:rent');
// Returns: { "District 1": "42", "Thao Dien": "31", ... }
```

---

### 8. Search Autocomplete Suggestions

**What**: Ranked list of district/city strings matching a prefix (typeahead)

**Why**: Autocomplete calls fire on every keystroke. Hitting PostgreSQL `ILIKE` on each
one is wasteful and adds latency. Redis `ZSET` with lexicographic range queries gives
O(log N + M) prefix lookup.

| Property | Value |
|----------|-------|
| Key | `autocomplete:districts` |
| Structure | `ZSET` — all members scored `0`; lexicographic `ZRANGEBYLEX` for prefix match |
| TTL | **No TTL** (populated once at startup / when districts change) |
| Set on | Application startup seed; background job when new district appears |

```typescript
// Seed: store "district 1\x00uuid" with score 0
await this.redis.zadd('autocomplete:districts', 0, 'binh thanh');
await this.redis.zadd('autocomplete:districts', 0, 'district 1');

// Query: all districts starting with "bi"
const results = await this.redis.zrangebylex(
  'autocomplete:districts', '[bi', '[bi\xff',
);
// Returns: ["binh thanh"]
```

---

### 9. Listing View Counters

**What**: Real-time view count per listing (displayed on detail page)

**Why**: `UPDATE listings SET views = views + 1` on every page view causes write
amplification and table lock contention at scale. Accumulate in Redis, flush to
PostgreSQL in batches.

| Property | Value |
|----------|-------|
| Key | `listing:views:{listing_id}` |
| Structure | `STRING` (integer counter) |
| TTL | **None** (persistent until flushed) |
| Flush strategy | Background Bull job runs every 5 min; reads all `listing:views:*` keys via SCAN, writes increments to PostgreSQL, then DELs keys |

```typescript
// Increment on page view (fire-and-forget)
await this.redis.incr(`listing:views:${listingId}`);
```

---

### 10. Distributed Lock (Duplicate Listing Detection)

**What**: A short-lived lock acquired during listing creation to prevent race-condition
duplicates from the same owner

**Why**: Two rapid submissions from the same owner (e.g., double-click) could insert two
identical rows before the fingerprint uniqueness check completes.

| Property | Value |
|----------|-------|
| Key | `lock:listing:create:{owner_id}:{fingerprint}` |
| Structure | `STRING` with value `"1"` |
| TTL | **5 seconds** |
| Set on | `POST /listings` — acquired with `SET NX EX 5` before DB insert |
| Released on | After DB insert completes (or TTL auto-expires) |

```typescript
const lockKey = `lock:listing:create:${ownerId}:${fingerprint}`;
const acquired = await this.redis.set(lockKey, '1', 'EX', 5, 'NX');
if (!acquired) throw new ConflictException('Duplicate listing submission');
```

---

### 11. Popular / Featured Listings

**What**: A pre-computed ordered list of the most-viewed or recently promoted listings
(shown on the homepage "Featured" carousel)

**Why**: The homepage is the highest-traffic page. Computing a ranking query on every
home page load is wasteful; the list changes at most every few minutes.

| Property | Value |
|----------|-------|
| Key | `listing:featured:{city}` |
| Structure | `ZSET` — listing_id as member, view_count or boost_score as score |
| TTL | **10 minutes** |
| Set on | Background job recomputes every 10 min |

---

### 12. CDN Pre-Signed URL Cache

**What**: Short-lived CDN signed URLs for private/draft listing photos (photos not yet
approved should not be publicly accessible)

**Why**: Generating a signed URL on every detail page request adds latency and costs
signature computation time.

| Property | Value |
|----------|-------|
| Key | `cdn:signed:{storage_key}` |
| Structure | `STRING` (signed URL) |
| TTL | **50 minutes** (URL itself expires in 60 min — cache for 50 to avoid serving an almost-expired URL) |
| Set on | First request for a private photo URL |
| Invalidated on | Photo deleted / listing approved (photos become public, no longer need signing) |

---

## What NOT to Cache

| Data | Reason |
|------|--------|
| **User account details** (email, role, is_active) | Must be immediately consistent — a suspended user must not pass auth checks via stale cache |
| **Moderation queue** (pending listings) | Moderators need real-time data; a listing approved by one moderator must disappear immediately for others |
| **Inquiry inbox** | Agents expect new inquiries to appear immediately |
| **Payment / billing data** | Correctness > performance; never cache financial records |
| **Listings in `pending_review` status** | Not served to the public; no benefit to caching |
| **Write responses** (`POST`, `PATCH`, `DELETE`) | Never cache mutation responses |

---

## Invalidation Reference

Quick lookup: *"I just did X — what cache keys must I delete?"*

| Mutation | Keys to invalidate |
|----------|--------------------|
| Listing updated (PATCH) | `listing:detail:{id}` |
| Listing approved | `listing:detail:{id}` · `listing:counts:district:{type}` (TTL expiry ok) |
| Listing rejected / expired | `listing:detail:{id}` · `listing:counts:district:{type}` (TTL expiry ok) |
| Photo added / deleted | `listing:detail:{id}` · `cdn:signed:{old_storage_key}` |
| User saves a listing | `sadd user:wishlist:{user_id} {listing_id}` |
| User unsaves a listing | `srem user:wishlist:{user_id} {listing_id}` |
| User account suspended | **Flush all auth tokens for that user** — `del session:denied:user:{uid}` then add all active JTIs |

---

## Anti-Patterns to Avoid

| Anti-pattern | Problem | Fix |
|--------------|---------|-----|
| **Cache stampede** | TTL expires on a hot key; 1000 requests hit DB simultaneously | Use probabilistic early expiry (PER), or a single-flight mutex (`SET NX EX 1` lock while recomputing) |
| **Large JSON blobs** | Storing full listing list pages (10 MB+) bloats Redis memory | Cache individual listing detail objects; assemble the list in the API from individual cached entries |
| **No TTL on mutable data** | Stale data served indefinitely if invalidation logic has a bug | Always set a TTL as a safety net, even for actively-invalidated keys |
| **Caching errors** | A 404 or 500 response cached means users see errors for TTL duration | Never cache non-2xx responses |
| **Using Redis as primary store** | If Redis is flushed / restarted, all data is lost | Redis is a cache; PostgreSQL is the source of truth |
| **KEYS * in production** | `KEYS` scans block the Redis event loop | Always use `SCAN` with a cursor for bulk key iteration |

---

## Memory Budget (MVP)

Estimate at 50,000 active listings:

| Cache | Entry size | Max entries | Memory |
|-------|-----------|-------------|--------|
| Listing detail | ~4 KB | 10,000 hot listings | ~40 MB |
| Search results | ~8 KB | 500 cached queries | ~4 MB |
| Rate-limit counters | ~50 B | 50,000 IPs | ~2.5 MB |
| Session denylist | ~100 B | 10,000 tokens | ~1 MB |
| Bull queue jobs | ~2 KB | 1,000 in-flight | ~2 MB |
| **Total MVP estimate** | | | **~50 MB** |

An ElastiCache `cache.t3.micro` (0.555 GB) is comfortable for MVP.
Upgrade to `cache.t3.small` (1.37 GB) when Phase 2 caches are added.
