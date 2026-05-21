import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import Home from "@/app/page";
import * as api from "@/lib/api";

vi.mock("@/lib/api", () => ({
  login: vi.fn(),
  getBoard: vi.fn(),
}));

const mockLogin = vi.mocked(api.login);
const mockGetBoard = vi.mocked(api.getBoard);

const fakeBoard: api.ApiBoard = {
  id: 1,
  title: "My Board",
  columns: [
    { id: 1, title: "Backlog", position: 0, cards: [] },
    { id: 2, title: "Discovery", position: 1, cards: [] },
    { id: 3, title: "In Progress", position: 2, cards: [] },
    { id: 4, title: "Review", position: 3, cards: [] },
    { id: 5, title: "Done", position: 4, cards: [] },
  ],
};

describe("Login flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetBoard.mockResolvedValue(fakeBoard);
  });

  it("shows login form initially", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByText("Kanban Studio")).not.toBeInTheDocument();
  });

  it("shows error on invalid credentials", async () => {
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));
    render(<Home />);
    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid username or password.");
    });
    expect(screen.queryByText("Kanban Studio")).not.toBeInTheDocument();
  });

  it("logs in with correct credentials and shows board", async () => {
    mockLogin.mockResolvedValue({ user_id: 1, username: "user" });
    render(<Home />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Kanban Studio")).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: /sign in/i })).not.toBeInTheDocument();
  });

  it("logs out and returns to login form", async () => {
    mockLogin.mockResolvedValue({ user_id: 1, username: "user" });
    render(<Home />);
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Kanban Studio")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /sign out/i }));

    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByText("Kanban Studio")).not.toBeInTheDocument();
  });
});
