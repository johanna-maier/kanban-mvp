# Code Review

Reviewed: 2026-05-22. Full codebase review covering backend, frontend, tests, and infrastructure.

Findings are grouped by priority. Each has a location, description, and a concrete action.

---

## High priority

### 1. Password hashing uses raw SHA-256

**File:** `backend/app/database.py:40`

```python
def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()
```

SHA-256 is a general-purpose hash — fast by design, unsalted, and precomputed rainbow tables exist for common passwords. A password hash must be slow and salted.

**Action:** Replace with `hashlib.scrypt` (stdlib, no extra dependency) or add `bcrypt`/`argon2-cffi` to requirements.

---

### 2. No authorization on board and card endpoints

**File:** `backend/app/main.py`

The `/api/board/{user_id}`, `/api/columns/{column_id}`, `/api/cards/{card_id}`, and `/api/ai/chat` endpoints accept requests without verifying the caller is who they claim to be. Any client that knows a numeric ID can read or mutate any user's data.

This is expected for MVP (no auth tokens), but it means the app is not safe to expose beyond localhost even with the Docker setup as-is.

**Action:** Document this limitation explicitly in AGENTS.md under Limitations. When auth is added, the simplest approach is a signed session cookie or a short-lived token returned at login.

---

### 3. Every keystroke fires an API call

**Files:** `frontend/src/components/KanbanCard.tsx:38,44`, `frontend/src/components/KanbanColumn.tsx:46`

Both `KanbanCard` and `KanbanColumn` call `onUpdate`/`onRename` on every `onChange` event. These propagate immediately to `api.updateCard()` and `api.renameColumn()`, sending an HTTP request per character typed.

**Action:** Debounce the API call (e.g. 500ms) while keeping the local state update immediate. A small `useDebounce` hook or `setTimeout`/`clearTimeout` pattern in `KanbanBoard.tsx` handlers is sufficient.

---

### 4. `renameColumn` and `updateCard` in api.ts silently swallow errors

**File:** `frontend/src/lib/api.ts:46-52, 64-70`

```ts
export async function renameColumn(...) {
  await fetch(`${API_BASE}/columns/${columnId}`, { ... });
  // no res.ok check
}
export async function updateCard(...) {
  await fetch(`${API_BASE}/cards/${cardId}`, { ... });
  // no res.ok check
}
```

A failed rename or card update returns to the caller with no indication of failure. The optimistic UI update has already been applied, so the UI and database silently diverge.

**Action:** Add `if (!res.ok) throw new Error(...)` to both functions, matching the pattern used in `createCard` and `getBoard`.

---

## Medium priority

### 5. `rename_column` returns 200 for non-existent column

**File:** `backend/app/main.py:131-139`

```python
@app.put("/api/columns/{column_id}")
def rename_column(column_id: int, body: ColumnRename):
    conn.execute("UPDATE columns SET title = ? WHERE id = ?", ...)
    # no check whether the row existed
    return {"id": column_id, "title": body.title}
```

If `column_id` doesn't exist, SQLite executes 0 rows and the endpoint returns 200 with the supplied title as if it succeeded.

**Action:** After the `UPDATE`, check `conn.execute(...).rowcount` (or re-query) and raise `HTTPException(404)` if no row was affected.

---

### 6. Dead code: `createId` in `kanban.ts`

**File:** `frontend/src/lib/kanban.ts:164-168`

`createId` was used when IDs were generated client-side. After the API integration (Part 7), all IDs come from the backend. The function is no longer called anywhere.

**Action:** Delete `createId`.

---

### 7. Chat message list uses array index as React key

**File:** `frontend/src/components/ChatSidebar.tsx:77`

```tsx
{messages.map((msg, i) => (
  <div key={i} ...>
```

Array index keys cause React to reuse DOM nodes incorrectly when items are inserted or removed, which can produce mismatched rendering.

**Action:** Add an `id` field to `ChatMessage` (e.g. `Date.now() + Math.random()` at push time) and use that as the key.

---

### 8. `apply_actions` connection not closed on unexpected exception

**File:** `backend/app/ai_chat.py:129-207`

The `apply_actions` function opens one connection and closes it at the end. Per-action errors are caught and recorded, so normal failures are handled. However, if an unhandled exception propagates out of the function before `conn.close()` (e.g. from `conn.commit()`), the connection leaks.

**Action:** Wrap the function body in a `try/finally` block, or use `with get_connection() as conn` if the connection is refactored to support context management.

---

### 9. No error state when board fails to load

**File:** `frontend/src/components/KanbanBoard.tsx:53-56`

`loadBoard` is called in `useEffect` but errors from the `await api.getBoard(userId)` call are uncaught. If the backend is down, the component shows "Loading board..." forever with no message.

**Action:** Wrap the `loadBoard` body in try/catch, add an `error` state, and render an error message when set.

---

### 10. Seed hardcodes `user_id = 1` by literal

**File:** `backend/app/database.py:63-65`

```python
conn.execute("INSERT INTO boards (user_id, title) VALUES (1, 'My Board')")
```

This relies on SQLite's AUTOINCREMENT producing ID 1 for the first user. It works now, but if `init_db` logic ever changes order of inserts, this silently creates a board with a dangling foreign key.

**Action:** Use `cursor.lastrowid` from the user insert to get the actual ID:
```python
cursor = conn.execute("INSERT INTO users ...")
user_id = cursor.lastrowid
conn.execute("INSERT INTO boards (user_id, title) VALUES (?, 'My Board')", (user_id,))
```

---

## Low priority / observations

### 11. `apiBoard` state in `KanbanBoard.tsx` is redundant

**File:** `frontend/src/components/KanbanBoard.tsx:50`

`apiBoard` is stored in state and updated alongside `board`, but is only used for a null-guard in `handleDragEnd`. The `board` state already serves that guard.

**Action:** Remove `apiBoard` state; check `!board` instead of `!board || !apiBoard`.

---

### 12. Tests couple to `init_db` implementation via hardcoded IDs

**Files:** `backend/tests/test_api.py`, `backend/tests/test_ai_chat.py`

Tests reference `/api/board/1`, `columns/1`, `cards` inserted with `column_id = 1` directly. This works because `init_db` seeds predictable IDs, but couples the tests to that specific seed order.

**Action:** Low urgency — consider reading the seeded board from the API within each test to resolve IDs dynamically, rather than hardcoding `1`.

---

### 13. `start-linux.sh` does not wait for the container to be ready

**File:** `scripts/start-linux.sh`

`docker run -d` returns as soon as the container starts, before the app inside is ready to serve requests. Running `DOCKER_TEST=1 npm run test:e2e` immediately after can hit a not-yet-ready server.

**Action:** Add a readiness wait after `docker run`:
```bash
echo "Waiting for container..."
until curl -sf http://127.0.0.1:8000/api/health > /dev/null; do sleep 1; done
```

---

### 14. `initialData` seed in `kanban.ts` is no longer used in production

**File:** `frontend/src/lib/kanban.ts:18-72`

`initialData` was the client-side seed before the backend existed. In production the board is loaded from the API; `initialData` is only referenced in frontend unit tests (via mocks).

This is not a bug but worth noting — if the seed data in `initialData` ever drifts far from reality, test mocks could mask real bugs.

---

## Summary table

| # | Location | Severity | Action |
|---|----------|----------|--------|
| 1 | `database.py:40` | High | Replace SHA-256 with scrypt/bcrypt |
| 2 | `main.py` (all endpoints) | High | Document auth gap; add token auth when hardening |
| 3 | `KanbanCard.tsx:38,44`, `KanbanColumn.tsx:46` | High | Debounce API calls on keystroke |
| 4 | `api.ts:46-70` | High | Add `res.ok` checks to `renameColumn`/`updateCard` |
| 5 | `main.py:131` | Medium | Return 404 when rename column target doesn't exist |
| 6 | `kanban.ts:164` | Medium | Delete unused `createId` |
| 7 | `ChatSidebar.tsx:77` | Medium | Use stable ID as React key on messages |
| 8 | `ai_chat.py:129` | Medium | Add `try/finally` to close DB connection on error |
| 9 | `KanbanBoard.tsx:53` | Medium | Add error state for failed board load |
| 10 | `database.py:63` | Medium | Use `lastrowid` instead of hardcoded user_id 1 |
| 11 | `KanbanBoard.tsx:50` | Low | Remove redundant `apiBoard` state |
| 12 | `test_api.py`, `test_ai_chat.py` | Low | Resolve IDs dynamically in tests |
| 13 | `start-linux.sh` | Low | Add health-check wait after `docker run` |
| 14 | `kanban.ts:18` | Note | `initialData` only used in tests; keep in sync |
