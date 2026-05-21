# Frontend agent guide

This document describes the current frontend codebase and how to reproduce the existing setup.

## Overview

- Framework: Next.js App Router.
- UI: Single-page Kanban board demo rendered at `/`.
- State: Local component state only (no backend calls yet).
- Drag and drop: `@dnd-kit`.
- Styling: Tailwind v4 + CSS variables, with custom fonts via `next/font`.

## Quick start

```bash
npm install
npm run dev
```

Open http://127.0.0.1:3000 to view the Kanban board.

## Tests

```bash
npm run test:unit
npm run test:e2e
npm run test:all
```

- Unit tests use Vitest + Testing Library.
- E2E tests use Playwright and start the dev server automatically.

## Key files

- src/app/page.tsx: Renders the Kanban board.
- src/app/layout.tsx: App shell, metadata, and Google fonts.
- src/app/globals.css: CSS variables and Tailwind import.
- src/components/KanbanBoard.tsx: Main board layout and DnD wiring.
- src/components/KanbanColumn.tsx: Column UI with inline title editing.
- src/components/KanbanCard.tsx: Card UI with drag handles and delete.
- src/components/KanbanCardPreview.tsx: Drag overlay card rendering.
- src/components/NewCardForm.tsx: Inline add-card form.
- src/lib/kanban.ts: Board data model, seed data, and move logic.
- src/components/KanbanBoard.test.tsx: Board unit tests.
- src/lib/kanban.test.ts: Move logic unit tests.
- tests/kanban.spec.ts: Playwright e2e tests.

## Data model

- Board data lives in src/lib/kanban.ts.
- `BoardData` contains:
  - `columns`: ordered list of columns with `cardIds`.
  - `cards`: lookup map of card data.
- `initialData` provides the seed board for the demo.
- `moveCard` handles drag-and-drop logic for same-column reorder and cross-column moves.

## UI behavior

- Columns are fixed count (five columns) but titles are editable inline.
- Cards are created via the Add card form and deleted with the Remove button.
- Drag-and-drop uses `DndContext` with `closestCorners` collision detection and a drag overlay preview.

## Styling and theming

- CSS variables in src/app/globals.css define colors and shadows.
- Tailwind v4 is imported via `@import "tailwindcss";`.
- Fonts are loaded in src/app/layout.tsx using `Space Grotesk` and `Manrope`.

## Reproducing the current setup

1. Install dependencies: `npm install`.
2. Run the dev server: `npm run dev`.
3. Visit http://127.0.0.1:3000 to view the Kanban board.
4. Run tests with `npm run test:all`.
