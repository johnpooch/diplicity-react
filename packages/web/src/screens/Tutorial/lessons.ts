import type {
  Nation,
  Order,
  OrderTypeEnum,
  PhaseRetrieve,
  Province,
  SupplyCenter,
  Unit,
  UnitTypeEnum,
  Variant,
} from "@/api/generated/endpoints";
import type { Board, Lesson } from "./types";

// Self-contained province table for the north-west corner used by the tutorial.
// The map renders units/orders by province id (geometry comes from the variant
// SVG), so only id + descriptive fields are needed here.
const PROVINCES: Record<string, Province> = {
  edi: prov("edi", "Edinburgh", "coastal", true),
  lvp: prov("lvp", "Liverpool", "coastal", true),
  yor: prov("yor", "Yorkshire", "coastal", false),
  lon: prov("lon", "London", "coastal", true),
  nth: prov("nth", "North Sea", "sea", false),
  eng: prov("eng", "English Channel", "sea", false),
  pic: prov("pic", "Picardy", "coastal", false),
  bel: prov("bel", "Belgium", "coastal", true),
  hol: prov("hol", "Holland", "coastal", true),
  bur: prov("bur", "Burgundy", "land", false),
  ruh: prov("ruh", "Ruhr", "land", false),
  par: prov("par", "Paris", "land", true),
  bre: prov("bre", "Brest", "coastal", true),
  mar: prov("mar", "Marseilles", "coastal", true),
  kie: prov("kie", "Kiel", "coastal", true),
};

function prov(
  id: string,
  name: string,
  type: string,
  supplyCenter: boolean
): Province {
  return { id, name, type, supplyCenter, parentId: null, namedCoastIds: [] };
}

function p(id: string): Province {
  const found = PROVINCES[id];
  if (!found) throw new Error(`Unknown tutorial province: ${id}`);
  return found;
}

export function provinceName(id: string): string {
  return PROVINCES[id]?.name ?? id;
}

function nationOf(variant: Variant, nationId: string): Nation {
  const found = variant.nations.find(n => n.nationId === nationId);
  if (!found) throw new Error(`Unknown tutorial nation: ${nationId}`);
  return found;
}

function unit(
  variant: Variant,
  type: UnitTypeEnum,
  nationId: string,
  provinceId: string,
  dislodged = false
): Unit {
  return {
    type,
    nation: nationOf(variant, nationId),
    province: p(provinceId),
    dislodged,
    dislodgedBy: null,
  };
}

function supplyCenter(
  variant: Variant,
  nationId: string,
  provinceId: string
): SupplyCenter {
  return { nation: nationOf(variant, nationId), province: p(provinceId) };
}

interface OrderSpec {
  nationId: string;
  unitType: UnitTypeEnum;
  orderType: OrderTypeEnum;
  source: string;
  target?: string;
  aux?: string;
  failed?: boolean;
  failedBy?: string;
}

function orderTitle(spec: OrderSpec): string {
  const u = spec.unitType === "Army" ? "A" : "F";
  switch (spec.orderType) {
    case "Move":
    case "MoveViaConvoy":
      return `${u} ${p(spec.source).name} - ${p(spec.target!).name}`;
    case "Support":
      return `${u} ${p(spec.source).name} S ${p(spec.aux!).name} - ${p(spec.target!).name}`;
    case "Convoy":
      return `${u} ${p(spec.source).name} C ${p(spec.aux!).name} - ${p(spec.target!).name}`;
    case "Hold":
    default:
      return `${u} ${p(spec.source).name} Hold`;
  }
}

function order(variant: Variant, spec: OrderSpec): Order {
  const target = spec.target ? p(spec.target) : null;
  const aux = spec.aux ? p(spec.aux) : null;
  const title = orderTitle(spec);
  return {
    source: p(spec.source),
    sourceCoast: null,
    // The generated Order type marks target/aux/namedCoast non-nullable, but the
    // real API returns null where they do not apply.
    target: target as Order["target"],
    aux: aux as Order["aux"],
    namedCoast: null as unknown as Order["namedCoast"],
    resolution: spec.failed
      ? { status: "Failed", by: spec.failedBy ? p(spec.failedBy) : null }
      : { status: "Succeeded", by: null },
    options: [],
    orderType: spec.orderType,
    unitType: spec.unitType,
    nation: nationOf(variant, spec.nationId),
    complete: true,
    step: "completed",
    title,
    summary: title,
  };
}

let phaseId = 100;

function phase(
  units: Unit[],
  supplyCenters: SupplyCenter[],
  overrides: Partial<Pick<PhaseRetrieve, "season" | "year" | "type">> = {}
): PhaseRetrieve {
  const season = overrides.season ?? "Spring";
  const year = overrides.year ?? 1901;
  const type = overrides.type ?? "Movement";
  return {
    id: phaseId++,
    ordinal: 1,
    season,
    year,
    name: `${season} ${year}, ${type}`,
    type,
    remainingTime: 0,
    scheduledResolution: "2026-01-01T00:00:00Z",
    status: "active",
    units,
    supplyCenters,
    previousPhaseId: null,
    nextPhaseId: null,
    provinceNations: "",
  };
}

export function buildLessons(variant: Variant): Lesson[] {
  // --- supply-center ownership ---
  // Movement turns: France's home centres, plus England/Germany for context.
  // Belgium and Holland stay neutral until the year-end adjustment.
  const baseCenters = (): SupplyCenter[] => [
    supplyCenter(variant, "france", "bre"),
    supplyCenter(variant, "france", "par"),
    supplyCenter(variant, "france", "mar"),
    supplyCenter(variant, "england", "lon"),
    supplyCenter(variant, "england", "edi"),
    supplyCenter(variant, "england", "lvp"),
    supplyCenter(variant, "germany", "kie"),
  ];

  // After the adjustment: France has held Belgium so it counts now; England has
  // taken Holland; Germany's gamble has cost it its centres.
  const adjustmentCenters = (): SupplyCenter[] => [
    supplyCenter(variant, "france", "bre"),
    supplyCenter(variant, "france", "par"),
    supplyCenter(variant, "france", "mar"),
    supplyCenter(variant, "france", "bel"),
    supplyCenter(variant, "england", "lon"),
    supplyCenter(variant, "england", "edi"),
    supplyCenter(variant, "england", "lvp"),
    supplyCenter(variant, "england", "hol"),
  ];

  // Holland tinted by whoever currently occupies it (it is a neutral centre, so
  // this shows control rather than formal ownership).
  const germanHolland = (): SupplyCenter[] => [
    ...baseCenters(),
    supplyCenter(variant, "germany", "hol"),
  ];
  const englishHolland = (): SupplyCenter[] => [
    ...baseCenters(),
    supplyCenter(variant, "england", "hol"),
  ];

  // --- camera framing ---
  const setupFocus = ["edi", "lon", "eng", "bur", "bel", "kie"];
  const midFocus = ["lon", "eng", "pic", "bel", "hol", "ruh"];
  const convoyFocus = ["lon", "nth", "hol", "bel", "ruh"];
  const adjustmentFocus = ["bre", "par", "bel", "hol", "ruh"];

  // --- casts at each stage ---
  // Spring start: England holds Edinburgh, London and Liverpool.
  const startCast = (): Unit[] => [
    unit(variant, "Army", "france", "bre"),
    unit(variant, "Army", "france", "bur"),
    unit(variant, "Army", "germany", "kie"),
    unit(variant, "Fleet", "england", "edi"),
    unit(variant, "Fleet", "england", "lon"),
    unit(variant, "Army", "england", "lvp"),
  ];

  // After turn 1: France → Picardy, Germany → Holland; England's fleets reach the
  // Channel and North Sea, its army reaches Yorkshire.
  const turn1Cast = (): Unit[] => [
    unit(variant, "Army", "france", "bre"),
    unit(variant, "Army", "france", "pic"),
    unit(variant, "Army", "germany", "hol"),
    unit(variant, "Fleet", "england", "nth"),
    unit(variant, "Fleet", "england", "eng"),
    unit(variant, "Army", "england", "yor"),
  ];

  // After turn 2: England's army has marched from Yorkshire into London.
  const turn2Cast = (): Unit[] => [
    unit(variant, "Army", "france", "bre"),
    unit(variant, "Army", "france", "pic"),
    unit(variant, "Army", "germany", "hol"),
    unit(variant, "Fleet", "england", "nth"),
    unit(variant, "Fleet", "england", "eng"),
    unit(variant, "Army", "england", "lon"),
  ];

  // France took Belgium with support (still neutral); England's army waits in London.
  const belgiumCast = (): Unit[] => [
    unit(variant, "Army", "france", "bre"),
    unit(variant, "Army", "france", "bel"),
    unit(variant, "Army", "germany", "hol"),
    unit(variant, "Fleet", "england", "nth"),
    unit(variant, "Fleet", "england", "eng"),
    unit(variant, "Army", "england", "lon"),
  ];

  // --- reusable orders ---
  const franceBurToPic = () =>
    order(variant, { nationId: "france", unitType: "Army", orderType: "Move", source: "bur", target: "pic" });
  const germanyKieToHol = () =>
    order(variant, { nationId: "germany", unitType: "Army", orderType: "Move", source: "kie", target: "hol" });
  const englandLonToEng = () =>
    order(variant, { nationId: "england", unitType: "Fleet", orderType: "Move", source: "lon", target: "eng" });
  const englandEdiToNth = () =>
    order(variant, { nationId: "england", unitType: "Fleet", orderType: "Move", source: "edi", target: "nth" });
  const englandLplToYor = () =>
    order(variant, { nationId: "england", unitType: "Army", orderType: "Move", source: "lvp", target: "yor" });
  const francePicToBel = () =>
    order(variant, { nationId: "france", unitType: "Army", orderType: "Move", source: "pic", target: "bel" });
  const germanyHolToBel = (failed = false) =>
    order(variant, { nationId: "germany", unitType: "Army", orderType: "Move", source: "hol", target: "bel", failed, failedBy: failed ? "bel" : undefined });
  const englandSupportsBelgium = () =>
    order(variant, { nationId: "england", unitType: "Fleet", orderType: "Support", source: "eng", aux: "pic", target: "bel" });
  const englandConvoyFleet = () =>
    order(variant, { nationId: "england", unitType: "Fleet", orderType: "Convoy", source: "nth", aux: "lon", target: "hol" });
  const englandConvoyArmy = () =>
    order(variant, { nationId: "england", unitType: "Army", orderType: "MoveViaConvoy", source: "lon", target: "hol" });
  const franceSupportsHolland = () =>
    order(variant, { nationId: "france", unitType: "Army", orderType: "Support", source: "bel", aux: "lon", target: "hol" });
  const germanyHoldsHolland = (failed = false) =>
    order(variant, { nationId: "germany", unitType: "Army", orderType: "Hold", source: "hol", failed });

  // --- board states ---
  const startBoard = (): Board => ({ phase: phase(startCast(), baseCenters()), orders: [] });

  const movedTurn1: Board = { phase: phase(turn1Cast(), germanHolland()), orders: [] };

  const fromTurn2Board = (): Board => ({ phase: phase(turn2Cast(), germanHolland()), orders: [] });

  // Turn 2 result: France and Germany bounce at Belgium; England's army reaches London.
  const bouncedAtBelgium: Board = {
    phase: phase(turn2Cast(), germanHolland()),
    orders: [
      order(variant, { nationId: "france", unitType: "Army", orderType: "Move", source: "pic", target: "bel", failed: true, failedBy: "bel" }),
      germanyHolToBel(true),
    ],
  };

  // France takes Belgium with support; Belgium stays neutral (still Spring).
  const belgiumOccupied: Board = {
    phase: phase(belgiumCast(), germanHolland()),
    orders: [francePicToBel(), englandSupportsBelgium(), germanyHolToBel(true)],
  };

  // Convoy planned, shown before the player adds support.
  const convoyPlanned: Board = {
    phase: phase(belgiumCast(), germanHolland()),
    orders: [englandConvoyFleet(), englandConvoyArmy(), germanyHoldsHolland()],
  };

  // Convoy resolves: England lands in Holland; Germany is dislodged (retreating).
  const convoyResolved: Board = {
    phase: phase(
      [
        unit(variant, "Army", "france", "bre"),
        unit(variant, "Army", "france", "bel"),
        unit(variant, "Army", "germany", "hol", true),
        unit(variant, "Army", "england", "hol"),
        unit(variant, "Fleet", "england", "nth"),
        unit(variant, "Fleet", "england", "eng"),
      ],
      englishHolland()
    ),
    orders: [englandConvoyFleet(), englandConvoyArmy(), franceSupportsHolland(), germanyHoldsHolland(true)],
  };

  // Germany retreats to Ruhr.
  const germanyRetreated: Board = {
    phase: phase(
      [
        unit(variant, "Army", "france", "bre"),
        unit(variant, "Army", "france", "bel"),
        unit(variant, "Army", "germany", "ruh"),
        unit(variant, "Army", "england", "hol"),
        unit(variant, "Fleet", "england", "nth"),
        unit(variant, "Fleet", "england", "eng"),
      ],
      englishHolland()
    ),
    orders: [],
  };

  // Adjustment: Belgium now counts for France; Germany controls nothing.
  const adjustmentBoard: Board = {
    phase: phase(
      [
        unit(variant, "Army", "france", "bre"),
        unit(variant, "Army", "france", "bel"),
        unit(variant, "Army", "germany", "ruh"),
        unit(variant, "Army", "england", "hol"),
        unit(variant, "Fleet", "england", "nth"),
        unit(variant, "Fleet", "england", "eng"),
      ],
      adjustmentCenters()
    ),
    orders: [],
  };

  // France builds an army in its empty home centre, Paris.
  const afterBuild: Board = {
    phase: phase(
      [
        unit(variant, "Army", "france", "bre"),
        unit(variant, "Army", "france", "bel"),
        unit(variant, "Army", "france", "par"),
        unit(variant, "Army", "germany", "ruh"),
        unit(variant, "Army", "england", "hol"),
        unit(variant, "Fleet", "england", "nth"),
        unit(variant, "Fleet", "england", "eng"),
      ],
      adjustmentCenters()
    ),
    orders: [],
  };

  // Germany disbands its army.
  const afterDisband: Board = {
    phase: phase(
      [
        unit(variant, "Army", "france", "bre"),
        unit(variant, "Army", "france", "bel"),
        unit(variant, "Army", "france", "par"),
        unit(variant, "Army", "england", "hol"),
        unit(variant, "Fleet", "england", "nth"),
        unit(variant, "Fleet", "england", "eng"),
      ],
      adjustmentCenters()
    ),
    orders: [],
  };

  return [
    {
      id: "welcome",
      title: "Welcome",
      initialBoard: startBoard(),
      focus: setupFocus,
      steps: [
        {
          coach:
            "Diplomacy is a game about talking to other players, making plans together and figuring out who you can trust.\n\nIn this tutorial, you'll learn the basic moves, playing as France.",
          title: "A game about people",
          goal: { kind: "continue" },
          primaryLabel: "Start tutorial",
        },
      ],
    },
    {
      id: "first-move",
      title: "Your first move",
      initialBoard: startBoard(),
      focus: setupFocus,
      steps: [
        {
          coach:
            "There are two unit types: armies (can move on land and coasts) and fleets (can move on sea and coasts). Only one unit can ever be in a province at one time.\n\nHere we highlighted your army in Burgundy.",
          title: "Your units",
          goal: { kind: "continue" },
          highlight: ["bur"],
          primaryLabel: "Next",
        },
        {
          coach:
            "Each turn you give your units orders - Move, Hold, Support or Convoy.\n\nWe'll start with a move; Tap your army in Burgundy, then tap Picardy to move into the coast province.",
          title: "Give an order",
          goal: { kind: "order", source: "bur", target: "pic" },
          order: franceBurToPic(),
        },
        {
          coach:
            "Everyone submits orders privately, which are all resolved at the same time at the end of the turn. Only then do you find out who you could trust.\n\nTurns usually run 24 hours — time to talk — but end early once everyone confirms. Confirm yours now.",
          title: "Orders are secret",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your order",
          // Confirming reveals everyone's orders (units still in place); the units
          // relocate when the supply-centers lesson loads (initialBoard: movedTurn1).
          resolvedBoard: {
            phase: phase(startCast(), baseCenters()),
            orders: [
              franceBurToPic(),
              germanyKieToHol(),
              englandLonToEng(),
              englandEdiToNth(),
              englandLplToYor(),
            ],
          },
        },
        {
          coach:
            "All orders resolved at the same time; Germany moved into Holland, England brought its fleets in the Channel and North Sea.",
          title: "On the move",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
      ],
    },
    {
      id: "supply-centers",
      title: "Supply centers",
      initialBoard: movedTurn1,
      focus: midFocus,
      steps: [
        {
          coach:
            "Some provinces, like Belgium here, have supply centers - these matter. They decide how many units you can have; more centers, more units.\n\nIf you have 18 SCs, you win the game.",
          title: "Supply centers",
          goal: { kind: "continue" },
          highlight: ["bel"],
          primaryLabel: "Next",
        },
        {
          coach:
            "Let's try to capture the SC in Belgium. Order your army to move into it.",
          title: "Your goal",
          goal: { kind: "order", source: "pic", target: "bel" },
          order: francePicToBel(),
        },
      ],
    },
    {
      id: "the-bounce",
      title: "The bounce",
      initialBoard: { phase: phase(turn1Cast(), germanHolland()), orders: [francePicToBel()] },
      focus: midFocus,
      steps: [
        {
          coach:
            "Note that Germany is eyeing the province too. We might have a fight on our hands.\n\nConfirm your orders to continue.",
          title: "Contested provinces",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your orders",
        },
        {
          coach:
            "Germany wanted Belgium too. Because each unit has a base strength of one, these armies are evenly matched.\n\nIn this case, no one moves. We call this a bounce - all units stay where they are.",
          title: "A contested move",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: bouncedAtBelgium,
        },
      ],
    },
    {
      id: "win-support",
      title: "Win an ally",
      initialBoard: fromTurn2Board(),
      focus: midFocus,
      steps: [
        {
          coach:
            "Because all units are equal strength, you cannot win on your own. You need allies. England has a fleet right besides Belgium - they can help us.\n\nThis is what Diplomacy is about - negotiating with players. We need to send England a message - open the Chat and propose a deal.",
          title: "You need allies",
          goal: { kind: "chat" },
          ally: "england",
          chat: [
            {
              from: "you",
              body: "England! Shall we work together against Germany? If you support my army from Picardy into Belgium, I'll support you into Holland later.",
            },
            {
              from: "ally",
              body: "Gladly. My fleet in the English Channel will support your move.",
            },
          ],
          primaryLabel: "Back to the map",
        },
        {
          coach:
            "Normally influencing people will likely not be so easy! We can only know if England could be trusted **after** the orders are revealed.\n\nOrder your army from Picardy into Belgium again, and hope they follow through on their promise.",
          title: "Trust the deal",
          goal: { kind: "order", source: "pic", target: "bel" },
          order: francePicToBel(),
        },
        {
          coach:
            "Nothing in Diplomacy is binding — England could still change their mind. Knowing when and who to trust - and betray - is the key of the game.\n\nConfirm your order to see if England was trustworthy.",
          title: "Confirm your order",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your order",
          resolvedBoard: belgiumOccupied,
        },
        {
          coach:
            "England kept their word — their fleet supported you, and each supporting unit adds one strength. Two against Germany's one, so your army marched into Belgium. Armies move across land and coasts; fleets across water and coasts — which is why England's Channel fleet could back a move into coastal Belgium.",
          title: "England followed through",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
        {
          coach:
            "But notice Belgium is still grey — not yours yet. A supply center only becomes yours if you still hold it at the year's end, the adjustment. Keep your army there.",
          title: "Hold to claim it",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
      ],
    },
    {
      id: "convoy",
      title: "Cross the water",
      initialBoard: { phase: phase(belgiumCast(), germanHolland()), orders: [] },
      focus: convoyFocus,
      steps: [
        {
          coach:
            "Your plan is coming together — England's army reached London and its fleet is waiting in the North Sea, just where you need them. Open the Chat to make good on your promise and plan the next move.",
          title: "Keep the alliance",
          goal: { kind: "chat" },
          ally: "england",
          chat: [
            {
              from: "you",
              body: "Germany dug into Holland. Convoy your London army across — I'll support the landing, as promised.",
            },
            {
              from: "ally",
              body: "Perfect. My North Sea fleet will carry the army over.",
            },
          ],
          primaryLabel: "Back to the map",
        },
        {
          coach:
            "A fleet can carry an army across water — that's a convoy. England's North Sea fleet will ferry their London army into Holland (the blue line). But Germany is dug in there, holding the province.",
          title: "What a convoy is",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: convoyPlanned,
        },
        {
          coach:
            "Lend your strength. Your Belgium army can't cross the sea, but it can support the landing. Tap your army in Belgium, then England's army in London, then Holland — your army stays put and adds one strength.",
          title: "Support the landing",
          goal: { kind: "order", source: "bel", aux: "lon", target: "hol" },
          order: franceSupportsHolland(),
        },
        {
          coach:
            "The landing strikes with two strength; Germany's lone hold has only one. Hold orders can be supported too, to defend — but Germany's wasn't. Confirm your order.",
          title: "Confirm your order",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your order",
          resolvedBoard: convoyResolved,
        },
        {
          coach:
            "Your support landed England's army in Holland — and dislodged Germany. The little flag marks a unit in retreat. The landing struck with two strength against Germany's lone hold of one.",
          title: "The landing",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
        {
          coach:
            "A dislodged unit isn't destroyed — it must retreat to an empty neighbouring province. Germany falls back to Ruhr. Hold orders can be supported too, to defend — but Germany's wasn't.",
          title: "Retreats",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: germanyRetreated,
        },
      ],
    },
    {
      id: "adjustment",
      title: "The adjustment",
      initialBoard: adjustmentBoard,
      focus: adjustmentFocus,
      steps: [
        {
          coach:
            "The year ends, and now supply centers are counted. You held Belgium through to the adjustment, so it's finally yours — it's turned blue. You control four centers but have only two armies.",
          title: "Counting centers",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
        {
          coach:
            "More centers than armies means you build. New units appear in your empty home centers. Tap Paris to build an army there.",
          title: "Build a unit",
          goal: { kind: "select", province: "par" },
          highlight: ["par"],
          tappable: ["par"],
        },
        {
          coach:
            "A fresh army for France in Paris — that's a build. Germany, though, was driven out of Holland and lost the race for centers. With fewer centers than armies, it must disband one.",
          title: "France builds",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: afterBuild,
        },
        {
          coach:
            "Germany removes an army from the board — a disband. Overreaching cost it everything. You ended the year stronger; Germany ended it weaker.",
          title: "Germany disbands",
          goal: { kind: "continue" },
          primaryLabel: "Finish",
          enterBoard: afterDisband,
        },
      ],
    },
  ];
}
