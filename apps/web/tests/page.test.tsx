import { render, screen } from "@testing-library/react";

import Home from "../app/page";

describe("foundation page", () => {
  it("identifies the application and its scaffold status", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Network Compass" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Repository foundation is running."),
    ).toBeInTheDocument();
  });
});
