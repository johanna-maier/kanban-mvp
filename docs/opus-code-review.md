# Code Review

Reviewed: 2026-05-23. Full codebase review (backend, frontend, tests, infrastructure). Three independent finder angles × verifier pass. Findings ranked most-severe first.

---

## 1. Partial move writes committed when inner exception fires mid-action

**File:** `backend/app/ai_chat.py:172–205`

`apply_actions` wraps each action in an inner `try/except` that logs the error and continues, then calls `conn.commit()` once after the loop. A "move" action executes three `UPDATE` statements sequentially. If the second or third throws, the inner `except` catches it — but the first `UPDATE` (which decremented positions in the source column) has already executed and is committed by the outer `conn.commit()`. The card stays in its old column but other cards in that column now have a gap in their position values, breaking all future reorderings.

**Failure scenario:** AI issues a batch with a move action. Step 1 (decrement old column positions) succeeds; step 2 raises (e.g., a Pydantic validation error on a malformed position field). The error is swallowed, `conn.commit()` fires, and the DB is left with corrupted position counters.

**Action:** Either wrap the entire action loop in a savepoint per action (roll back each action individually on failure), or move `conn.commit()` inside each action's success path and call `conn.rollback()` in the except clause.

---

## 2. `moveCard` silently swallows HTTP errors; caller never knows the move failed

**File:** `frontend/src/lib/api.ts:74–80`

`moveCard` calls `fetch` but never checks `res.ok` and never throws. Every other function in this file (`renameColumn`, `createCard`, `updateCard`, `chatWithAI`) checks `res.ok`. The caller `handleDragEnd` in `KanbanBoard.tsx` has already applied an optimistic UI update before the API call resolves. Because `moveCard` cannot throw, the drag outcome is always treated as success regardless of the server response.

**Failure scenario:** A drag move fails on the server (e.g., the card was deleted by an AI action concurrently). `api.moveCard` resolves successfully. The UI shows the card in its new position; the DB still has it in the old column. The board silently diverges until the next full reload.

**Action:** Add `if (!res.ok) throw new Error("Failed to move card")` after the fetch, matching the pattern used by the other API functions.

---

## 3. `deleteCard` silently swallows HTTP errors

**File:** `frontend/src/lib/api.ts:82–84`

Same missing `res.ok` check as `moveCard`. The caller `handleDeleteCard` performs an optimistic removal before the API call, so a server-side failure is undetectable and the card disappears from the UI while remaining in the DB.

**Failure scenario:** Network error or 500 response on `DELETE /api/cards/:id`. `api.deleteCard` resolves without throwing. The card is gone from the UI for this session. On page reload it reappears, confusing the user.

**Action:** Add `if (!res.ok) throw new Error("Failed to delete card")`.

---

## 4. `handleDeleteCard` removes card from UI before confirming server success

**File:** `frontend/src/components/KanbanBoard.tsx:144–161`

`setBoard(...)` (which removes the card from local state) executes synchronously before `await api.deleteCard(...)`. If the API call fails, there is no rollback and no error is shown. Combined with finding #3, a server failure leaves the card gone from the UI with no way to recover without a page refresh.

**Failure scenario:** User deletes a card while the backend is momentarily unreachable. The card vanishes from the UI immediately. The API call fails silently. On next reload the card reappears.

**Action:** Either move the `setBoard` call after a successful `await`, or add a try/catch that restores the card on failure and shows an error message.

---

## 5. Debounced rename/update fires after `loadBoard`, writing stale content to DB

**File:** `frontend/src/components/KanbanBoard.tsx:105–119, 163–179`

`handleRenameColumn` and `handleUpdateCard` each set a 500 ms debounced timer whose callback closes over the current title/details. `loadBoard` is called via `onBoardUpdated` after every AI chat response. If the AI responds within 500 ms of the last keystroke, `loadBoard` replaces board state with fresh DB values — but the pending `setTimeout` still fires and calls `api.renameColumn` / `api.updateCard` with the stale in-progress text, overwriting whatever the DB held after the AI action.

**Failure scenario:** User types "Sprin" while renaming "Backlog". Sends an AI message. AI responds in ~400 ms; `loadBoard` restores the column title to "Backlog" in DB and state. 500 ms timer fires and writes "Sprin" to DB. Column is now permanently "Sprin" without the user having finished typing.

**Action:** Cancel all pending rename/update timers at the start of `loadBoard` (e.g., iterate `renameTimers.current` and `updateTimers.current` and clear each) before replacing board state.

---

## 6. `parse_ai_response` strips all lines starting with ` ``` `, not just outer fences

**File:** `backend/app/ai_chat.py:113–123`

The line filter `[l for l in lines if not l.strip().startswith("```")]` runs over every line in the document when the outer response is fence-wrapped. If the JSON `reply` field contains a line starting with ` ``` ` (e.g., the AI mentions a code block in its reply), that line is stripped before `json.loads`, producing malformed JSON and a crash.

**Failure scenario:** User asks "how do I write a Python loop?" AI wraps its response in a ` ```json ` fence and includes a Python snippet in the reply. The fence-stripping removes the interior ` ```python ` line, breaking the JSON string. `json.loads` raises `JSONDecodeError`, which propagates as a 500 (see finding #8).

**Action:** Only strip the first and last lines of the fence-wrapped block, e.g.:
```python
lines = text.split("\n")
text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
```

---

## 7. `create_card` returns a 500 FK violation instead of 404 for unknown column

**File:** `backend/app/main.py:148–164`

`PRAGMA foreign_keys = ON` is set in `get_connection()`. The `create_card` handler does not verify that `column_id` exists before attempting the `INSERT`. The `COALESCE` position query returns `0` even for a nonexistent column (aggregate over zero rows), then the `INSERT` raises `sqlite3.IntegrityError`, which FastAPI surfaces as an unhandled 500 with an internal traceback.

**Failure scenario:** AI generates a `create` action with a hallucinated `column_id`. Request returns 500 instead of a meaningful 404. Error details from the DB layer are exposed in the response.

**Action:** After computing `next_pos`, check if `conn.execute("SELECT id FROM columns WHERE id = ?", (column_id,)).fetchone()` is `None` and raise `HTTPException(404)`.

---

## 8. `JSONDecodeError` from `parse_ai_response` propagates uncaught as 500

**File:** `backend/app/ai_chat.py:224`

`chat_with_board` calls `parse_ai_response(raw_reply)` with no surrounding `try/except`. If the model returns malformed JSON (truncated output, explanatory preamble, or corrupted by finding #6), `json.loads` raises `JSONDecodeError` and the entire `/api/ai/chat` endpoint returns an unhandled 500. The frontend shows a generic error and the user has no actionable feedback.

**Action:** Wrap `parse_ai_response` in a try/except in `chat_with_board` and return a graceful fallback reply with an empty actions list.

---

## 9. `board.cards[cardId]` can produce `undefined` in the cards array

**File:** `frontend/src/components/KanbanBoard.tsx:263`

```tsx
cards={column.cardIds.map((cardId) => board.cards[cardId])}
```

TypeScript types this as `Card[]` but the runtime result is `(Card | undefined)[]` if any `cardId` is absent from `board.cards`. `KanbanCard` immediately dereferences `card.id`, `card.title`, and `card.details` without a null guard. Under normal operation the state is atomically consistent, but a race between a concurrent AI board reload and a local mutation could produce a transient inconsistency that crashes the entire board render.

**Action:** Add a filter: `column.cardIds.map((id) => board.cards[id]).filter(Boolean)` and assert the type, or add a guard in `KanbanCard`.

---

## 10. `verify_password` uses non-constant-time string comparison

**File:** `backend/app/database.py:54`

```python
return h.hex() == hash_hex
```

Python string equality short-circuits on the first differing byte. An attacker with a precise timer can distinguish "wrong at byte 0" from "wrong at byte 30" and recover the stored hash hex one character at a time without needing to invert scrypt. The correct comparison is `hmac.compare_digest(h.hex(), hash_hex)`.

Low practical risk for the current localhost-only deployment, but the comparison undermines the security guarantee that scrypt is meant to provide.

**Action:** Replace with `import hmac; return hmac.compare_digest(h.hex(), hash_hex)`.

---

## Summary

| # | File | Severity | Finding |
|---|------|----------|---------|
| 1 | `ai_chat.py:205` | High | Partial move writes committed when inner exception fires |
| 2 | `api.ts:74` | High | `moveCard` swallows HTTP errors silently |
| 3 | `api.ts:82` | High | `deleteCard` swallows HTTP errors silently |
| 4 | `KanbanBoard.tsx:144` | High | Optimistic delete before confirming server success |
| 5 | `KanbanBoard.tsx:117` | Medium | Debounced rename fires after `loadBoard`, overwrites stale data |
| 6 | `ai_chat.py:119` | Medium | Fence-strip filter removes interior ` ``` ` lines, corrupts JSON |
| 7 | `main.py:157` | Medium | `create_card` returns 500 FK error for nonexistent column |
| 8 | `ai_chat.py:224` | Medium | `JSONDecodeError` propagates uncaught as 500 |
| 9 | `KanbanBoard.tsx:263` | Low | `board.cards[cardId]` can be `undefined`, crashing render |
| 10 | `database.py:54` | Low | Non-constant-time password hash comparison |
