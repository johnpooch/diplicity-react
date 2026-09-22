import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChannelAvatar } from "./ChannelAvatar";

describe("ChannelAvatar", () => {
  it("uses a 3px nation-colour ring for a single-country chat", () => {
    const { container } = render(
      <ChannelAvatar
        nations={[{ flagUrl: "/france.svg", color: "#123456" }]}
      />
    );

    expect(container.firstChild).toHaveStyle({
      boxShadow: "0 0 0 3px #123456",
    });
  });
});
