"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import * as api from "@/lib/api";
import type { ApiBoard, ApiCard } from "@/lib/api";
import type { Card, Column, BoardData } from "@/lib/kanban";
import { moveCard as moveCardLocal } from "@/lib/kanban";

type KanbanBoardProps = {
  userId: number;
  onLogout?: () => void;
};

function apiBoardToBoardData(apiBoard: ApiBoard): BoardData {
  const cards: Record<string, Card> = {};
  const columns: Column[] = apiBoard.columns.map((col) => {
    const cardIds = col.cards.map((c) => `card-${c.id}`);
    for (const c of col.cards) {
      cards[`card-${c.id}`] = { id: `card-${c.id}`, title: c.title, details: c.details };
    }
    return { id: `col-${col.id}`, title: col.title, cardIds };
  });
  return { columns, cards };
}

function parseColumnId(id: string): number {
  return Number(id.replace("col-", ""));
}

function parseCardId(id: string): number {
  return Number(id.replace("card-", ""));
}

export const KanbanBoard = ({ userId, onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [apiBoard, setApiBoard] = useState<ApiBoard | null>(null);

  const loadBoard = useCallback(async () => {
    const data = await api.getBoard(userId);
    setApiBoard(data);
    setBoard(apiBoardToBoardData(data));
  }, [userId]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board || !apiBoard) return;

    // Optimistic local update
    const newColumns = moveCardLocal(board.columns, active.id as string, over.id as string);
    setBoard((prev) => prev ? { ...prev, columns: newColumns } : prev);

    // Find the target column and position
    const targetColumn = newColumns.find((col) =>
      col.cardIds.includes(active.id as string)
    );
    if (!targetColumn) return;

    const position = targetColumn.cardIds.indexOf(active.id as string);
    const columnId = parseColumnId(targetColumn.id);
    const cardId = parseCardId(active.id as string);

    await api.moveCard(cardId, columnId, position);
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            columns: prev.columns.map((col) =>
              col.id === columnId ? { ...col, title } : col
            ),
          }
        : prev
    );
    await api.renameColumn(parseColumnId(columnId), title);
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    const cardDetails = details || "No details yet.";
    const result = await api.createCard(parseColumnId(columnId), title, cardDetails);
    const newId = `card-${result.id}`;
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            cards: {
              ...prev.cards,
              [newId]: { id: newId, title, details: cardDetails },
            },
            columns: prev.columns.map((col) =>
              col.id === columnId
                ? { ...col, cardIds: [...col.cardIds, newId] }
                : col
            ),
          }
        : prev
    );
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            cards: Object.fromEntries(
              Object.entries(prev.cards).filter(([id]) => id !== cardId)
            ),
            columns: prev.columns.map((col) =>
              col.id === columnId
                ? { ...col, cardIds: col.cardIds.filter((id) => id !== cardId) }
                : col
            ),
          }
        : prev
    );
    await api.deleteCard(parseCardId(cardId));
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  if (!board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">Loading board...</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex flex-col items-end gap-3">
              <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Focus
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  One board. Five columns. Zero clutter.
                </p>
              </div>
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
                >
                  Sign out
                </button>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};
