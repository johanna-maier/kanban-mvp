import { moveCard, createId, type Column } from "@/lib/kanban";

describe("moveCard", () => {
  const baseColumns: Column[] = [
    { id: "col-a", title: "A", cardIds: ["card-1", "card-2"] },
    { id: "col-b", title: "B", cardIds: ["card-3"] },
  ];

  it("reorders cards in the same column", () => {
    const result = moveCard(baseColumns, "card-2", "card-1");
    expect(result[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("moves cards to another column", () => {
    const result = moveCard(baseColumns, "card-2", "card-3");
    expect(result[0].cardIds).toEqual(["card-1"]);
    expect(result[1].cardIds).toEqual(["card-2", "card-3"]);
  });

  it("drops cards to the end of a column", () => {
    const result = moveCard(baseColumns, "card-1", "col-b");
    expect(result[0].cardIds).toEqual(["card-2"]);
    expect(result[1].cardIds).toEqual(["card-3", "card-1"]);
  });

  it("returns unchanged columns when activeId is not found", () => {
    const result = moveCard(baseColumns, "nonexistent", "card-1");
    expect(result).toEqual(baseColumns);
  });

  it("returns unchanged columns when overId is not found", () => {
    const result = moveCard(baseColumns, "card-1", "nonexistent");
    expect(result).toEqual(baseColumns);
  });

  it("moves card to end of its own column when dropped on column id", () => {
    const result = moveCard(baseColumns, "card-1", "col-a");
    expect(result[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("returns unchanged when same-column reorder indices are equal", () => {
    const result = moveCard(baseColumns, "card-1", "card-1");
    expect(result).toEqual(baseColumns);
  });

  it("moves card between columns when numeric IDs collide with column IDs", () => {
    // Regression: with prefixed IDs (col-X, card-X) there's no collision
    const numericColumns: Column[] = [
      { id: "col-1", title: "Backlog", cardIds: ["card-1", "card-2"] },
      { id: "col-2", title: "Done", cardIds: ["card-3"] },
    ];
    // Drag card "card-1" over column "col-2" (drop on column)
    const result = moveCard(numericColumns, "card-1", "col-2");
    expect(result[0].cardIds).toEqual(["card-2"]);
    expect(result[1].cardIds).toEqual(["card-3", "card-1"]);
  });
});

describe("createId", () => {
  it("returns a string with the given prefix", () => {
    const id = createId("card");
    expect(id.startsWith("card-")).toBe(true);
  });

  it("generates unique ids", () => {
    const a = createId("x");
    const b = createId("x");
    expect(a).not.toBe(b);
  });
});
