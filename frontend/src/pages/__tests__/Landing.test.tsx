import '@testing-library/jest-dom';
import { render, screen } from "@testing-library/react";
import Landing from "../Landing";

describe("Landing page", () => {
  it("renders hero copy", () => {
    render(<Landing />);
    expect(screen.getByText(/AI-FIRST MARKET COPILOT/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Finbot helps/i })).toBeInTheDocument();
  });
});
