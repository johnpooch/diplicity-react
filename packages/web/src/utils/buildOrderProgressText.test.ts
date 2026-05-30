import { describe, it, expect } from "vitest";
import { buildOrderProgressText, unitAbbrev } from "./buildOrderProgressText";
import type { PhaseRetrieve } from "../api/generated/endpoints";

const makePhase = (units: PhaseRetrieve["units"] = []): PhaseRetrieve => ({
  id: 1,
  ordinal: 1,
  season: "Spring",
  year: 1901,
  name: "Spring 1901",
  type: "Diplomacy",
  remainingTime: 0,
  scheduledResolution: "",
  status: "pending" as PhaseRetrieve["status"],
  units,
  supplyCenters: [],
  provinceNations: {},
  previousPhaseId: null,
  nextPhaseId: null,
});

const nation = { nationId: "england", name: "England", color: "#fff", flagUrl: null };

const province = (id: string, name: string) => ({
  id,
  name,
  type: "land",
  supplyCenter: false,
  parentId: null,
  namedCoastIds: [] as string[],
});

const army = (provinceId: string, provinceName: string) => ({
  type: "Army",
  nation,
  province: province(provinceId, provinceName),
  dislodged: false,
  dislodgedBy: null,
});

const fleet = (provinceId: string, provinceName: string) => ({
  type: "Fleet",
  nation,
  province: province(provinceId, provinceName),
  dislodged: false,
  dislodgedBy: null,
});

describe("unitAbbrev", () => {
  it("returns A for Army", () => expect(unitAbbrev("Army")).toBe("A"));
  it("returns F for Fleet", () => expect(unitAbbrev("Fleet")).toBe("F"));
  it("returns empty string for unknown", () => expect(unitAbbrev("unknown")).toBe(""));
  it("returns empty string for undefined", () => expect(unitAbbrev(undefined)).toBe(""));
});

describe("buildOrderProgressText", () => {
  const phase = makePhase([army("par", "Paris"), fleet("bre", "Brest")]);

  describe("no source", () => {
    it("returns null", () => {
      expect(buildOrderProgressText({}, {}, phase, false)).toBeNull();
    });
  });

  describe("source only (no orderType)", () => {
    it("shows unit abbreviation and label when unit is in province", () => {
      expect(
        buildOrderProgressText({ source: "par" }, { source: "Paris" }, phase, false)
      ).toBe("A Paris");
    });

    it("shows just the province label when no unit is there", () => {
      expect(
        buildOrderProgressText({ source: "lon" }, { source: "London" }, phase, false)
      ).toBe("London");
    });

    it("falls back to the province id when no label", () => {
      expect(
        buildOrderProgressText({ source: "par" }, {}, phase, false)
      ).toBe("A par");
    });
  });

  describe("Build", () => {
    const emptyPhase = makePhase();

    it("shows ellipsis when unitType not yet selected", () => {
      expect(
        buildOrderProgressText(
          { source: "lon", orderType: "Build" },
          { source: "London" },
          emptyPhase,
          false
        )
      ).toBe("Build in London ...");
    });

    it("shows full build text when unitType selected", () => {
      expect(
        buildOrderProgressText(
          { source: "lon", orderType: "Build", unitType: "Army" },
          { source: "London", unitType: "Army" },
          emptyPhase,
          false
        )
      ).toBe("Build Army in London");
    });

    it("falls back to unitType id when no label", () => {
      expect(
        buildOrderProgressText(
          { source: "lon", orderType: "Build", unitType: "Army" },
          { source: "London" },
          emptyPhase,
          false
        )
      ).toBe("Build Army in London");
    });
  });

  describe("Hold", () => {
    it("shows unit + Hold", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Hold" },
          { source: "Paris" },
          phase,
          true
        )
      ).toBe("A Paris Hold");
    });
  });

  describe("Disband", () => {
    it("shows unit + Disband", () => {
      expect(
        buildOrderProgressText(
          { source: "bre", orderType: "Disband" },
          { source: "Brest" },
          phase,
          true
        )
      ).toBe("F Brest Disband");
    });
  });

  describe("Move", () => {
    it("shows ellipsis when target not selected", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Move" },
          { source: "Paris" },
          phase,
          false
        )
      ).toBe("A Paris Move to ...");
    });

    it("shows full move text when target selected", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Move", target: "bur" },
          { source: "Paris", target: "Burgundy" },
          phase,
          true
        )
      ).toBe("A Paris Move to Burgundy");
    });

    it("falls back to target id when no label", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Move", target: "bur" },
          { source: "Paris" },
          phase,
          true
        )
      ).toBe("A Paris Move to bur");
    });
  });

  describe("MoveViaConvoy", () => {
    it("shows ellipsis with via Convoy suffix when target not selected", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "MoveViaConvoy" },
          { source: "Paris" },
          phase,
          false
        )
      ).toBe("A Paris Move via Convoy to ...");
    });

    it("shows full move via convoy text", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "MoveViaConvoy", target: "lon" },
          { source: "Paris", target: "London" },
          phase,
          true
        )
      ).toBe("A Paris Move via Convoy to London");
    });
  });

  describe("Support", () => {
    it("shows ellipsis when aux not selected", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Support" },
          { source: "Paris" },
          phase,
          false
        )
      ).toBe("A Paris Supports ...");
    });

    it("shows aux with ellipsis when target not selected and not complete (hold support in progress)", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Support", aux: "bre" },
          { source: "Paris", aux: "Brest" },
          phase,
          false
        )
      ).toBe("A Paris Supports F Brest ...");
    });

    it("shows aux without ellipsis when isComplete (hold support)", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Support", aux: "bre" },
          { source: "Paris", aux: "Brest" },
          phase,
          true
        )
      ).toBe("A Paris Supports F Brest");
    });

    it("shows full support move text with target", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Support", aux: "bre", target: "pic" },
          { source: "Paris", aux: "Brest", target: "Picardy" },
          phase,
          true
        )
      ).toBe("A Paris Supports F Brest to Picardy");
    });

    it("shows aux province name when no unit in aux province", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Support", aux: "lon" },
          { source: "Paris", aux: "London" },
          phase,
          true
        )
      ).toBe("A Paris Supports London");
    });
  });

  describe("Convoy", () => {
    it("shows ellipsis when aux not selected", () => {
      expect(
        buildOrderProgressText(
          { source: "bre", orderType: "Convoy" },
          { source: "Brest" },
          phase,
          false
        )
      ).toBe("F Brest Convoys ...");
    });

    it("shows aux with ellipsis when target not selected", () => {
      expect(
        buildOrderProgressText(
          { source: "bre", orderType: "Convoy", aux: "par" },
          { source: "Brest", aux: "Paris" },
          phase,
          false
        )
      ).toBe("F Brest Convoys A Paris to ...");
    });

    it("shows full convoy text with target", () => {
      expect(
        buildOrderProgressText(
          { source: "bre", orderType: "Convoy", aux: "par", target: "lon" },
          { source: "Brest", aux: "Paris", target: "London" },
          phase,
          true
        )
      ).toBe("F Brest Convoys A Paris to London");
    });

    it("shows aux province name when no unit in aux province", () => {
      expect(
        buildOrderProgressText(
          { source: "bre", orderType: "Convoy", aux: "lon", target: "edi" },
          { source: "Brest", aux: "London", target: "Edinburgh" },
          phase,
          true
        )
      ).toBe("F Brest Convoys London to Edinburgh");
    });
  });

  describe("unknown orderType", () => {
    it("returns sourceLabel as fallback", () => {
      expect(
        buildOrderProgressText(
          { source: "par", orderType: "Unknown" },
          { source: "Paris" },
          phase,
          false
        )
      ).toBe("A Paris");
    });
  });
});
