import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import {
  NationSeatFlag,
  NationSeatPill,
  getNationSeatLabel,
  getNationSeatState,
} from "./NationSeat";

const nations = ["Austria", "England", "France"].map(name => ({
  nationId: name.toLowerCase(),
  name,
  color: "#cccccc",
  nonPlayable: false,
  flagUrl: `/flags/${name.toLowerCase()}.png`,
}));

describe("getNationSeatState", () => {
  it("is unset with no nation and no preferences", () => {
    expect(getNationSeatState(null, [])).toBe("unset");
  });

  it("is ranked with preferences and no nation", () => {
    expect(getNationSeatState(null, ["france"])).toBe("ranked");
  });

  it("is assigned when a nation is pinned, even with preferences", () => {
    expect(getNationSeatState("France", ["england"])).toBe("assigned");
  });
});

describe("getNationSeatLabel", () => {
  it("names the assigned nation", () => {
    expect(getNationSeatLabel("France", [])).toBe("France");
  });

  it("reports that preferences were provided", () => {
    expect(getNationSeatLabel(null, ["france", "england"])).toBe(
      "Nation preferences provided"
    );
    expect(getNationSeatLabel(null, ["france"])).toBe("Nation preferences provided");
  });

  it("asks for preferences when none are set", () => {
    expect(getNationSeatLabel(null, [])).toBe("Choose nation preferences");
  });
});

describe("missing preference data", () => {
  it("falls back to unset rather than throwing", () => {
    expect(getNationSeatState(null, undefined)).toBe("unset");
    expect(getNationSeatLabel(null, undefined)).toBe("Choose nation preferences");
  });

  it("still names an assigned nation", () => {
    expect(getNationSeatLabel("France", undefined)).toBe("France");
  });

  it("renders the pill without preference data", () => {
    render(<NationSeatPill nations={nations} nation={null} preferenceIds={undefined} />);

    expect(screen.getByText("Choose nation")).toBeInTheDocument();
  });
});

describe("NationSeatFlag", () => {
  it("shows no flag when nothing is chosen", () => {
    render(<NationSeatFlag nations={nations} nation={null} preferenceIds={[]} />);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("shows the top ranked nation when preferences are set", () => {
    render(
      <NationSeatFlag nations={nations} nation={null} preferenceIds={["england", "france"]} />
    );

    expect(screen.getByRole("img", { name: "England" })).toBeInTheDocument();
  });

  it("shows the assigned nation over the preferences", () => {
    render(
      <NationSeatFlag nations={nations} nation="France" preferenceIds={["england"]} />
    );

    expect(screen.getByRole("img", { name: "France" })).toBeInTheDocument();
    expect(screen.queryByRole("img", { name: "England" })).not.toBeInTheDocument();
  });
});

describe("NationSeatPill", () => {
  it("invites the player to set preferences when nothing is chosen", async () => {
    const onClick = vi.fn();
    render(
      <NationSeatPill
        nations={nations}
        nation={null}
        preferenceIds={[]}
        onClick={onClick}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: /Choose nation/ }));

    expect(onClick).toHaveBeenCalled();
  });

  it("names the top choice and counts the rest", () => {
    render(
      <NationSeatPill
        nations={nations}
        nation={null}
        preferenceIds={["england", "france"]}
        onClick={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: /England \+1/ })).toBeInTheDocument();
  });

  it("names a lone top choice without a count", () => {
    render(
      <NationSeatPill
        nations={nations}
        nation={null}
        preferenceIds={["england"]}
        onClick={vi.fn()}
      />
    );

    expect(screen.getByRole("button", { name: "England England" })).toBeInTheDocument();
  });

  it("keeps the positioning it is given when interactive", () => {
    render(
      <NationSeatPill
        nations={nations}
        nation={null}
        preferenceIds={[]}
        className="absolute bottom-2 left-2"
        onClick={vi.fn()}
      />
    );

    const pill = screen.getByRole("button", { name: /Choose nation/ });
    expect(pill).toHaveClass("absolute", "bg-background/70", "cursor-pointer");
    expect(pill).not.toHaveClass("relative");
  });

  it("names the assigned nation and is not interactive", () => {
    render(<NationSeatPill nations={nations} nation="France" preferenceIds={[]} />);

    expect(screen.getByText("France")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
