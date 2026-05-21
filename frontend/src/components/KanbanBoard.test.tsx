import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  getBoard: vi.fn(),
  renameColumn: vi.fn(),
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  moveCard: vi.fn(),
  updateCard: vi.fn(),
}));

const mockGetBoard = vi.mocked(api.getBoard);
const mockCreateCard = vi.mocked(api.createCard);
const mockDeleteCard = vi.mocked(api.deleteCard);
const mockRenameColumn = vi.mocked(api.renameColumn);

const fakeBoard: api.ApiBoard = {
  id: 1,
  title: "My Board",
  columns: [
    { id: 10, title: "Backlog", position: 0, cards: [{ id: 100, title: "Task A", details: "Details A", position: 0 }] },
    { id: 20, title: "Discovery", position: 1, cards: [] },
    { id: 30, title: "In Progress", position: 2, cards: [] },
    { id: 40, title: "Review", position: 3, cards: [{ id: 200, title: "Task B", details: "Details B", position: 0 }] },
    { id: 50, title: "Done", position: 4, cards: [] },
  ],
};

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

async function renderBoard() {
  render(<KanbanBoard userId={1} />);
  await waitFor(() => {
    expect(screen.getByText("Kanban Studio")).toBeInTheDocument();
  });
}

describe("KanbanBoard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetBoard.mockResolvedValue(fakeBoard);
    mockCreateCard.mockResolvedValue({ id: 999, title: "", details: "", position: 0 });
    mockDeleteCard.mockResolvedValue(undefined);
    mockRenameColumn.mockResolvedValue(undefined);
  });

  it("renders five columns", async () => {
    await renderBoard();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    await renderBoard();
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    await renderBoard();
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(within(column).getByText("New card")).toBeInTheDocument();
    });

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("adds a card with no details and gets default text", async () => {
    await renderBoard();
    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "No details card");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(within(column).getByText("No details yet.")).toBeInTheDocument();
    });
  });

  it("cancels adding a card", async () => {
    await renderBoard();
    const column = getFirstColumn();
    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );

    expect(within(column).getByPlaceholderText(/card title/i)).toBeInTheDocument();

    await userEvent.click(within(column).getByRole("button", { name: /cancel/i }));

    expect(within(column).queryByPlaceholderText(/card title/i)).not.toBeInTheDocument();
  });

  it("does not add a card with empty title", async () => {
    await renderBoard();
    const column = getFirstColumn();

    await userEvent.click(
      within(column).getByRole("button", { name: /add a card/i })
    );
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    // Form should still be open (not submitted)
    expect(within(column).getByPlaceholderText(/card title/i)).toBeInTheDocument();
  });

  it("shows empty column placeholder when all cards removed", async () => {
    await renderBoard();
    // The "Review" column (id=40) has only 1 card
    const reviewColumn = screen.getByTestId("column-col-40");
    const deleteButton = within(reviewColumn).getByRole("button", {
      name: /delete/i,
    });
    await userEvent.click(deleteButton);

    expect(within(reviewColumn).getByText(/drop a card here/i)).toBeInTheDocument();
  });
});
