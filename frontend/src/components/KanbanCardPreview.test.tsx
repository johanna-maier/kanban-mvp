import { render, screen } from "@testing-library/react";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";

describe("KanbanCardPreview", () => {
  it("renders card title and details", () => {
    render(<KanbanCardPreview card={{ id: "card-1", title: "Test", details: "Some details" }} />);
    expect(screen.getByText("Test")).toBeInTheDocument();
    expect(screen.getByText("Some details")).toBeInTheDocument();
  });
});
