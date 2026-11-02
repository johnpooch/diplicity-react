import { describe, it, expect } from "vitest";
import type {
  FlatOrderOption,
  PhaseState,
  Province,
} from "../api/generated/endpoints";
import { filterOrderableOptions } from "./orderableOptions";

const province = (id: string) => ({ id }) as unknown as Province;

const phaseState = (orderable: string[]) =>
  ({ orderableProvinces: orderable.map(province) }) as unknown as PhaseState;

const option = (sourceId: string) =>
  ({
    source: { id: sourceId, label: sourceId },
    orderType: { id: "Build", label: "Build" },
  }) as FlatOrderOption;

describe("filterOrderableOptions", () => {
  it("keeps options whose source is orderable", () => {
    const options = [option("lon"), option("lvp")];
    expect(
      filterOrderableOptions(options, [phaseState(["lon", "lvp"])])
    ).toEqual(options);
  });

  it("drops options whose source is no longer orderable", () => {
    expect(
      filterOrderableOptions(
        [option("lon"), option("lvp"), option("lon")],
        [phaseState(["lon"])]
      )
    ).toEqual([option("lon"), option("lon")]);
  });

  it("unions orderable provinces across phase states", () => {
    expect(
      filterOrderableOptions(
        [option("lon"), option("par"), option("ber")],
        [phaseState(["lon"]), phaseState(["par"])]
      )
    ).toEqual([option("lon"), option("par")]);
  });

  it("returns no options without phase states", () => {
    expect(filterOrderableOptions([option("lon")], [])).toEqual([]);
  });
});
