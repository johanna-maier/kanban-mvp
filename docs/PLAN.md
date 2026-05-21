# Project Plan

This file is the full, executable plan. Do not start a part until the user approves the prior part.

Approval rule: complete Part 1 and obtain user approval before starting Part 2 or later work.

Sidenote for human user: Original PLAN.md can be found here https://github.com/ed-donner/pm/blob/main/docs/PLAN.md.

## Global constraints

- Keep changes minimal and focused on the MVP scope.
- Prefer simple, idiomatic implementations.
- No extra features.
- Provide tests for all new behavior.

## Testing best practices

- Test behaviors, not implementation details.
- Unit tests for pure logic and component interactions; e2e for full user flows.
- Drag-and-drop only tested in e2e (requires real browser coordinates).
- When a bug is fixed, add a regression test that would catch it if it returns.
- Exclude config files from coverage reporting (not application logic).
- Target 80%+ statement coverage for application code, but never add tests just to hit a number. Every test must validate a meaningful behavior.
- Run coverage with `npm run test:unit -- --coverage` (frontend) or `pytest --cov` (backend).
- Every new feature gets at least one unit test and one e2e scenario for critical paths.
- Use `/api/health` for container liveness checks.
- Mock API calls in unit tests (vi.mock); e2e tests hit the real backend.

## Design decisions

- **ID namespacing**: Column IDs are prefixed `col-` and card IDs `card-` in the frontend to prevent dnd-kit collisions (SQLite auto-increments both from 1). The API client strips prefixes before sending numeric IDs to the backend.
- **Dev proxy**: next.config.ts has `rewrites` routing `/api/*` to `localhost:8000` during development. This only works in `next dev` (ignored in static export, which is fine since production serves from FastAPI).
- **Optimistic UI**: Mutations (add, delete, move, rename) update local state immediately, then fire the API call. No rollback on failure for MVP simplicity.
- **API client**: `frontend/src/lib/api.ts` is a thin fetch wrapper with typed responses. No auth tokens for MVP (user_id passed directly).
- **SQLite in Docker**: The database lives at `backend/data/kanban.db` inside the container. Data is ephemeral (lost on container rebuild). A volume mount could persist it but is not configured for MVP.

## Part 1: Plan and documentation

Checklist
- [x] Expand this plan with substeps, tests, and success criteria for every part.
- [x] Create frontend/AGENTS.md that documents the existing frontend and how to reproduce the current setup.
- [x] Confirm the plan with the user and pause.

Tests
- None (documentation only).

Success criteria
- docs/PLAN.md reflects a complete, testable plan.
- frontend/AGENTS.md accurately documents the current frontend setup.
- User explicitly approves the plan.

## Part 2: Scaffolding

Checklist
- [x] Add Docker files using multi-stage build (Node stage builds frontend, Python stage runs FastAPI).
- [x] Create backend FastAPI app in backend/ using uv as the package manager.
- [x] Add a GET endpoint such as /api/hello that returns JSON.
- [x] Add a GET /api/health endpoint for container health checks (Docker HEALTHCHECK).
- [x] Serve a simple static HTML page from FastAPI for `/` to prove static serving.
- [x] Add start/stop scripts in scripts/ for macOS, Windows, and Linux.
- [x] Document how to run the container locally.

Tests
- Build the container image.
- `curl http://127.0.0.1:<port>/` returns static HTML.
- `curl http://127.0.0.1:<port>/api/hello` returns JSON.

Success criteria
- Container starts locally with one command and serves both HTML and API.
- Start/stop scripts operate on all platforms.

## Part 3: Add in Frontend

Note: The current frontend demo does not support card editing (only add/delete). Card editing will be added in Part 7 when the backend is wired up.

Checklist
- [x] Configure Next.js for static build output.
- [x] Build the existing frontend and place static files where FastAPI can serve them.
- [x] Serve the static build from FastAPI at `/`.
- [x] Ensure routing, assets, and CSS load correctly in the container.
- [x] Update or add tests where needed.

Tests
- Frontend unit tests: `npm run test:unit`.
- Frontend e2e tests: `npm run test:e2e`.
- Manual check: open `/` in the container and confirm the Kanban board renders.

Success criteria
- The existing Kanban UI is served at `/` via FastAPI.
- Tests pass in local dev and containerized runs.

## Part 4: Fake sign in

Checklist
- [x] Add login UI gating in the frontend.
- [x] Accept only `user` / `password`.
- [x] Add logout and session reset behavior.
- [x] Add tests for login and logout.

Tests
- Unit tests cover login/logout UI state.
- E2E test verifies access control and logout.

Success criteria
- Board requires dummy login, logout works, tests pass.

## Part 5: Database modeling

Checklist
- [x] Propose a SQLite schema for users, boards, columns, and cards.
- [x] Save the schema as JSON in docs/db-schema.json.
- [x] Save a readable version in docs/db-schema.md.
- [x] Document the modeling rationale and migration plan in docs/.
- [x] Obtain user approval before implementation.

Tests
- JSON schema validates (basic structure check).

Success criteria
- Database model is documented and approved.

## Part 6: Backend

Checklist
- [x] Implement CRUD endpoints for board data.
- [x] Ensure database is created if missing.
- [x] Add backend unit tests for persistence and API behavior.

Tests
- Backend unit tests pass.
- Manual curl checks for create/read/update flows.

Success criteria
- Backend reliably persists Kanban data per user.

## Part 7: Frontend + Backend

Checklist
- [x] Replace frontend local state with API-backed state.
- [x] Implement API calls for load, update, and move operations.
- [x] Ensure UI stays in sync with backend data.
- [x] Add integration coverage.
- [x] Fix dnd-kit ID collision bug (card/column IDs overlapping).

Tests
- E2E covers create/move/rename with persistence.
- Regression test for ID collision in moveCard.

Success criteria
- Board changes persist across reloads.
- Drag and drop works correctly between columns.

## Part 8: AI connectivity

Checklist
- [ ] Add OpenRouter client in backend with env config.
- [ ] Implement a simple `2+2` test endpoint.
- [ ] Add unit tests with mock client.

Tests
- Unit test mocks OpenRouter client.
- Manual test hits the `2+2` endpoint.

Success criteria
- Backend can call OpenRouter successfully.

## Part 9: Structured AI updates

Checklist
- [ ] Define structured output schema for AI response and optional board update.
- [ ] Send board JSON and conversation history to the model.
- [ ] Validate AI output and apply updates safely.
- [ ] Add tests for schema validation and update logic.

Tests
- Contract tests for schema validation.
- Unit tests for update application.

Success criteria
- Valid structured responses update the board safely.

## Part 10: AI sidebar

Checklist
- [ ] Build sidebar chat UI in the frontend.
- [ ] Wire chat UI to backend AI endpoint.
- [ ] Apply AI board updates and refresh UI.
- [ ] Add e2e coverage for chat and update flows.

Tests
- E2E chat test confirms responses and board updates.

Success criteria
- Sidebar chat works end-to-end with optional board updates.
