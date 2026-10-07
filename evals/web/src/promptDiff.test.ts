import { describe, expect, test } from "vitest";
import { hasChanges, promptDiff } from "./promptDiff";

describe("promptDiff", () => {
  test("identical prompts have no changes", () => {
    const blocks = promptDiff("one\ntwo\n", "one\ntwo\n");
    expect(blocks).toEqual([{ kind: "same", lines: ["one", "two"] }]);
    expect(hasChanges(blocks)).toBe(false);
  });

  test("a reworded paragraph is highlighted word by word, not as a whole line", () => {
    const blocks = promptDiff(
      "Role.\nHold only to defend a province under threat.\nFormat.",
      "Role.\nHold only to defend a supply centre under threat.\nFormat."
    );
    expect(blocks).toEqual([
      { kind: "same", lines: ["Role."] },
      {
        kind: "changed",
        segments: [
          { kind: "same", text: "Hold only to defend a " },
          { kind: "removed", text: "province" },
          { kind: "added", text: "supply centre" },
          { kind: "same", text: " under threat." },
        ],
      },
      { kind: "same", lines: ["Format."] },
    ]);
    expect(hasChanges(blocks)).toBe(true);
  });

  test("an added paragraph is one added block", () => {
    const blocks = promptDiff("Role.\nFormat.", "Role.\nA new principle.\nFormat.");
    expect(blocks[1]).toEqual({ kind: "changed", segments: [{ kind: "added", text: "A new principle." }] });
  });

  test("a removed paragraph is one removed block", () => {
    const blocks = promptDiff("Role.\nAn old principle.\nFormat.", "Role.\nFormat.");
    expect(blocks[1]).toEqual({ kind: "changed", segments: [{ kind: "removed", text: "An old principle." }] });
  });
});
