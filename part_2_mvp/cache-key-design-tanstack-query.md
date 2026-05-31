# Cache Key Design in TanStack Query (React Query)

## Overview

Cache keys are the backbone of TanStack Query's caching system. They uniquely identify each query, determine when data should be refetched, and control cache invalidation. A well-designed cache key strategy leads to optimal cache hits, minimal redundant requests, and predictable state management.

---

## What is a Cache Key?

A cache key (query key) is an array — typically a tuple of `[string, ...params]` — passed as the first argument to `useQuery`, `useMutation`, `queryClient.fetchQuery`, etc. TanStack Query serializes this array to create a unique identifier for the cached data.

```typescript
// Basic string key
useQuery({ queryKey: ['todos'], queryFn: fetchTodos })

// Compound key with parameters
useQuery({ queryKey: ['todos', { status: 'completed' }], queryFn: fetchFilteredTodos })
```

---

## Design Principles

### 1. Hierarchy & Namespacing

Structure keys from **most general to most specific**. This mirrors REST API paths and enables targeted invalidation via partial matching.

```typescript
// ❌ Flat / ambiguous
['todos', 'list', 1, 'comments']

// ✅ Hierarchical
['todos', 'list']
['todos', 'detail', todoId]
['todos', 'detail', todoId, 'comments']
```

**Rule of thumb**: Design keys so that querying `queryClient.invalidateQueries({ queryKey: ['todos'] })` clears everything related to "todos".

### 2. Deterministic Serialization

TanStack Query uses `JSON.stringify` internally. The order of keys **matters**. Ensure objects passed as part of the query key have stable property ordering.

```typescript
// ❌ Non-deterministic — object key order can vary
const params = { status: 'active', page: 2 } // may serialize differently

// ✅ Deterministic
const queryKey = ['todos', 'list', { page: 2, status: 'active' }]
// But still risky — better to use a flat structure or sort keys
```

**Best practice**: Use flat, primitive-based keys whenever possible, or pass serializable primitives only:

```typescript
useQuery({
  queryKey: ['users', 'list', { page: 1, limit: 20 }],
  queryFn: () => fetchUsers({ page: 1, limit: 20 }),
})
```

### 3. Specificity Controls Refetch Behavior

The key should include **every variable that changes the result** of the query. If a parameter doesn't affect the response, don't include it.

```typescript
// ✅ status affects the result → include it
useQuery({
  queryKey: ['todos', { status: filter }],
  queryFn: () => fetchTodos({ status: filter }),
})

// ❌ sortField doesn't affect the API response (client-side sort)
// Including it causes unnecessary cache misses
useQuery({
  queryKey: ['todos', { status: filter, sortField: 'title' }],
  queryFn: () => fetchTodos({ status: filter }),
})
```

---

## Common Patterns

### Pattern 1: Query Key Factory

Define all keys in one place. Prevents typos, enables autocomplete, and serves as documentation.

```typescript
// features/todos/query-keys.ts
export const todoKeys = {
  all: ['todos'] as const,
  
  lists: () => [...todoKeys.all, 'list'] as const,
  list: (filters: TodoFilters) => [...todoKeys.lists(), filters] as const,
  
  details: () => [...todoKeys.all, 'detail'] as const,
  detail: (id: string) => [...todoKeys.details(), id] as const,
  
  comments: (todoId: string) => [...todoKeys.detail(todoId), 'comments'] as const,
}
```

**Usage:**

```typescript
// In a component
const { data } = useQuery({
  queryKey: todoKeys.list({ status: 'active' }),
  queryFn: () => fetchTodos({ status: 'active' }),
})

// In a mutation callback
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: todoKeys.lists() })
}
```

### Pattern 2: Partial Matching for Invalidation

Invalidate or refetch multiple related queries by matching a prefix.

```typescript
// Invalidate all todos — lists, details, comments
queryClient.invalidateQueries({ queryKey: ['todos'] })

// Invalidate only list queries
queryClient.invalidateQueries({ queryKey: ['todos', 'list'] })

// Invalidate a specific todo and all its children (comments)
queryClient.invalidateQueries({ queryKey: ['todos', 'detail', todoId] })
```

### Pattern 3: Query Options Factory

Combine keys with `queryFn`, `staleTime`, etc., for even more reuse.

```typescript
// features/todos/query-options.ts
import { queryOptions } from '@tanstack/react-query'
import { todoKeys } from './query-keys'

export const todoQueries = {
  list: (filters: TodoFilters) =>
    queryOptions({
      queryKey: todoKeys.list(filters),
      queryFn: () => fetchTodos(filters),
      staleTime: 5 * 60 * 1000,
    }),

  detail: (id: string) =>
    queryOptions({
      queryKey: todoKeys.detail(id),
      queryFn: () => fetchTodo(id),
      staleTime: 10 * 60 * 1000,
    }),
}
```

### Pattern 4: Pagination & Infinite Queries

```typescript
// Offset-based pagination
const postKeys = {
  all: ['posts'] as const,
  page: (page: number, limit: number) => [...postKeys.all, { page, limit }] as const,
}

// Cursor-based (useInfiniteQuery)
const feedKeys = {
  all: ['feed'] as const,
  infinite: (filters?: FeedFilters) => [...feedKeys.all, 'infinite', filters ?? {}] as const,
}
```

### Pattern 5: Dependent / Parametric Keys

When a query depends on data from another query:

```typescript
const projectKeys = {
  all: ['projects'] as const,
  detail: (id: string) => [...projectKeys.all, 'detail', id] as const,
  members: (projectId: string) => [...projectKeys.detail(projectId), 'members'] as const,
}

function useProjectMembers(projectId: string | undefined) {
  return useQuery({
    queryKey: projectKeys.members(projectId!),
    queryFn: () => fetchMembers(projectId!),
    enabled: !!projectId, // Don't run until projectId is available
  })
}
```

---

## Key Design for Mutations

Mutations don't have query keys themselves, but they interact with query caches. Design mutation callbacks to maintain cache consistency.

```typescript
const useUpdateTodo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateTodo,

    // Optimistic update
    onMutate: async (updatedTodo) => {
      await queryClient.cancelQueries({ queryKey: todoKeys.detail(updatedTodo.id) })
      const previous = queryClient.getQueryData(todoKeys.detail(updatedTodo.id))
      queryClient.setQueryData(todoKeys.detail(updatedTodo.id), updatedTodo)
      return { previous }
    },

    onError: (_err, updatedTodo, context) => {
      queryClient.setQueryData(todoKeys.detail(updatedTodo.id), context?.previous)
    },

    onSettled: (_data, _error, updatedTodo) => {
      // Invalidate the detail and any related list
      queryClient.invalidateQueries({ queryKey: todoKeys.detail(updatedTodo.id) })
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() })
    },
  })
}
```

---

## Structuring Keys for Complex Domains

### Entity-Based Pattern

```typescript
// Feature: Blog
export const blogKeys = {
  all: ['blog'] as const,
  
  posts: {
    all: ['blog', 'posts'] as const,
    list: (filters?: PostFilters) => [...blogKeys.posts.all, 'list', filters ?? {}] as const,
    detail: (slug: string) => [...blogKeys.posts.all, 'detail', slug] as const,
  },

  categories: {
    all: ['blog', 'categories'] as const,
    list: () => [...blogKeys.categories.all, 'list'] as const,
  },

  authors: {
    all: ['blog', 'authors'] as const,
    detail: (id: string) => [...blogKeys.authors.all, 'detail', id] as const,
  },
} as const
```

### Service-Based Pattern

```typescript
// Group by API service domain
export const queryKeys = {
  users: {
    root: ['users'] as const,
    me: ['users', 'me'] as const,
    detail: (id: string) => ['users', id] as const,
    list: (params?: UserListParams) => ['users', 'list', params ?? {}] as const,
  },

  orders: {
    root: ['orders'] as const,
    detail: (id: string) => ['orders', id] as const,
    list: (params?: OrderListParams) => ['orders', 'list', params ?? {}] as const,
    byUser: (userId: string) => ['orders', 'byUser', userId] as const,
  },
} as const
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| `['todos', todo]` (whole object) | Serialization breaks if object shape changes; bloated keys | `['todos', todo.id]` |
| `['todosList']` (no hierarchy) | Can't invalidate all todos at once | `['todos', 'list']` |
| `['todos', new Date()]` | Non-deterministic; new key every render | Pass a stable string/ISO representation |
| Inline string keys everywhere | Typos, no autocomplete, hard to refactor | Use a key factory |
| Including `user.id` in every key | Violates separation of concerns; user change invalidates everything | Use `queryClient.resetQueries()` on logout |

---

## When Keys Change: Full Lifecycle

```
Component mounts with key ['todos', 1]
       │
       ▼
Is key in cache? ──Yes──▶ Is data stale? ──Yes──▶ Refetch (show stale data if available)
       │                        │
       No                       No
       │                        │
       ▼                        ▼
   Fetch data             Return cached data
       │
       ▼
Key changes to ['todos', 2]
       │
       ▼
Repeat — this is a different cache entry
```

---

## Stale Time & GC Time by Key Granularity

Align `staleTime` and `gcTime` with your key design:

```typescript
// Static data — long staleTime
const configQueries = queryOptions({
  queryKey: ['config', 'features'],
  queryFn: fetchFeatureFlags,
  staleTime: 30 * 60 * 1000, // 30 minutes
  gcTime: 24 * 60 * 60 * 1000, // 24 hours
})

// Dynamic data — short staleTime
const notificationQueries = queryOptions({
  queryKey: ['notifications', 'unread'],
  queryFn: fetchUnreadNotifications,
  staleTime: 30 * 1000, // 30 seconds
})
```

---

## Real-World Example: E-Commerce Product Page

```typescript
// query-keys.ts
export const productKeys = {
  all: ['products'] as const,
  
  list: (filters: ProductListFilters) =>
    ['products', 'list', filters] as const,
  
  detail: (id: string) =>
    ['products', 'detail', id] as const,
  
  variants: (productId: string) =>
    ['products', 'detail', productId, 'variants'] as const,
  
  reviews: (productId: string, page?: number) =>
    ['products', 'detail', productId, 'reviews', { page: page ?? 1 }] as const,
  
  recommendations: (productId: string) =>
    ['products', 'detail', productId, 'recommendations'] as const,
}

// ProductDetailPage.tsx
function ProductDetailPage({ productId }: { productId: string }) {
  const { data: product } = useQuery({
    queryKey: productKeys.detail(productId),
    queryFn: () => fetchProduct(productId),
  })

  const { data: variants } = useQuery({
    queryKey: productKeys.variants(productId),
    queryFn: () => fetchVariants(productId),
  })

  const { data: reviews } = useQuery({
    queryKey: productKeys.reviews(productId),
    queryFn: () => fetchReviews(productId),
  })

  const { data: recommendations } = useQuery({
    queryKey: productKeys.recommendations(productId),
    queryFn: () => fetchRecommendations(productId),
    enabled: !!product, // Wait for product data first
  })
}

// AddReviewForm.tsx — Mutation invalidates reviews
function AddReviewForm({ productId }: { productId: string }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: submitReview,
    onSuccess: () => {
      // Only invalidate reviews for this product
      queryClient.invalidateQueries({
        queryKey: productKeys.reviews(productId),
        exact: false, // Match all review pages
      })
    },
  })
}
```

---

## Summary Checklist

- [ ] Keys follow a **hierarchical** structure: `['domain', 'entity', 'operation', ...params]`
- [ ] Keys include **only values that affect the API response**
- [ ] Keys use **primitive values**; no whole objects, no `Date` instances
- [ ] A **query key factory** centralizes all key definitions
- [ ] Invalidation uses **partial matching** to target the right scope
- [ ] `staleTime` and `gcTime` are tuned per key/entity type
- [ ] Mutations invalidate or update the **minimum necessary** set of queries
- [ ] **Dependent queries** use `enabled` with a guard on the dependency
- [ ] On user **logout**, `queryClient.clear()` or targeted `removeQueries()` is called

---

## References

- [TanStack Query — Query Keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
- [TanStack Query — Query Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation)
- [TkDodo's Blog — Effective React Query Keys](https://tkdodo.eu/blog/effective-react-query-keys)
- [TkDodo's Blog — Practical React Query](https://tkdodo.eu/blog/practical-react-query)
