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
    // Generated Order type marks target/aux/namedCoast non-nullable, but Hold
    // orders have no target/aux and no named coast.
    target: target as Order["target"],
    aux: aux as Order["aux"],
    targetCoast: null,
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
    earlyResolveWindowEnd: null,
    provinceNations: "",
  };
}

export function buildLessons(variant: Variant, panHint: string): Lesson[] {
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
  const englandYorToLon = () =>
    order(variant, { nationId: "england", unitType: "Army", orderType: "Move", source: "yor", target: "lon" });
  const englandConvoyFleet = () =>
    order(variant, { nationId: "england", unitType: "Fleet", orderType: "Convoy", source: "nth", aux: "lon", target: "hol" });
  const englandConvoyArmy = () =>
    order(variant, { nationId: "england", unitType: "Army", orderType: "MoveViaConvoy", source: "lon", target: "hol" });
  const franceSupportsHolland = () =>
    order(variant, { nationId: "france", unitType: "Army", orderType: "Support", source: "bel", aux: "lon", target: "hol" });
  const germanyHoldsHolland = (failed = false) =>
    order(variant, { nationId: "germany", unitType: "Army", orderType: "Hold", source: "hol", failed });
  const germanyRetreatsToRuhr = () =>
    order(variant, { nationId: "germany", unitType: "Army", orderType: "Move", source: "hol", target: "ruh" });

  // --- board states ---
  const startBoard = (): Board => ({ phase: phase(startCast(), baseCenters()), orders: [] });

  const movedTurn1: Board = { phase: phase(turn1Cast(), germanHolland()), orders: [] };

  const fromTurn2Board = (): Board => ({ phase: phase(turn2Cast(), germanHolland()), orders: [] });

  // Turn 2 result: France and Germany bounce at Belgium; England's army still in Yorkshire, moving to London.
  const bouncedAtBelgium: Board = {
    phase: phase(turn1Cast(), germanHolland()),
    orders: [
      order(variant, { nationId: "france", unitType: "Army", orderType: "Move", source: "pic", target: "bel", failed: true, failedBy: "bel" }),
      germanyHolToBel(true),
      englandYorToLon(),
    ],
  };

  // France takes Belgium with support; Belgium stays neutral (still Spring).
  const belgiumOccupied: Board = {
    phase: phase(belgiumCast(), germanHolland()),
    orders: [francePicToBel(), englandSupportsBelgium(), germanyHolToBel(true)],
  };

  // Units in convoy position, no orders shown (used for steps that explain without arrows).
  const convoyUnits: Board = {
    phase: phase(belgiumCast(), germanHolland()),
    orders: [],
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
            "Diplomacy is a game about talking to other players, making plans together and figuring out who you can trust.\n\nIn this tutorial, you'll learn the basic moves, playing as France.\n" +
            `_${panHint}_`,
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
            "There are two unit types: armies (can move on land and coasts) and fleets (can move on sea and coasts). Only one unit can ever be in a province at one time.\n\nWe've highlighted your army in Burgundy.",
          title: "Your units",
          goal: { kind: "continue" },
          highlight: ["bur"],
          primaryLabel: "Next",
        },
        {
          coach:
            "Each turn you give your units orders — Move, Hold, Support or Convoy.\n\nWe'll start with a move — tap your army in Burgundy, then tap Picardy to move into the coastal province.",
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
            "All orders resolve at the same time: Germany moved into Holland, and England brought its fleets into the Channel and the North Sea.",
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
            "Some provinces, like Belgium here, have supply centers (SCs) — these matter. They decide how many units you can have; more centers, more units.\n\nIf you have 18 SCs, you win the game (depending on variant).",
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
            "Germany may be eyeing that center too. If they move in as well, we've got a fight on our hands.\n\nConfirm your orders to continue.",
          title: "Contested provinces",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your orders",
        },
        {
          coach:
            "Germany wanted Belgium too. Because each unit has a base strength of one, these armies are evenly matched.\n\nIn this case, no one moves. We call this a **bounce** — all units stay where they are.",
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
            "Because all units are equal strength, you cannot win on your own. You need allies. England has a fleet right beside Belgium — they can help us.\n\nThis is what Diplomacy is really about: negotiating with other players. Send England a message — open the Chat and propose a deal.",
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
            "In a real game, persuading people is rarely this easy! You'll only know whether England can be trusted **after** orders are revealed.\n\nOrder your army from Picardy into Belgium again, and hope they keep their word.",
          title: "Trust the deal",
          goal: { kind: "order", source: "pic", target: "bel" },
          order: francePicToBel(),
        },
        {
          coach:
            "Nothing in Diplomacy is binding — England could still change their mind. Knowing who to trust — and when to betray — is the heart of the game.\n\nConfirm your order and see whether England keeps their word.",
          title: "Confirm your order",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your order",
          resolvedBoard: belgiumOccupied,
        },
        {
          coach:
            "England kept their word! Their fleet supported you. Each supporting unit adds one strength, but supporting units don't move.\n\nTwo against one — your army marches into Belgium, and Germany's stays put in Holland.\n**Important: if a supporting unit is itself attacked, its support is cut (cancelled).**",
          title: "England followed through",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
        {
          coach:
            "Notice Belgium is not yours yet. An SC only changes owner during the adjustment phase, after every two movement turns.\n\nWe need to keep our army there. Supporting units don't move — so ours can stay in Belgium and still support England.",
          title: "Adjustment phases",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: { phase: phase(belgiumCast(), germanHolland()), orders: [] },
        },
      ],
    },
    {
      id: "convoy",
      title: "Cross the water",
      initialBoard: convoyUnits,
      focus: convoyFocus,
      steps: [
        {
          coach:
            "Your plan is coming together — England's army reached London and its fleet is waiting in the North Sea, just where you need them.\n\nOpen the Chat to make good on your promise and plan the next move.",
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
            "A fleet — or a chain of fleets — can carry an army across water. England will order its North Sea fleet to convoy the London army into Holland. A convoy doesn't add strength; it only carries the army across.",
          title: "Convoying across water",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: convoyUnits,
        },
        {
          coach:
            "Germany might **hold** its unit to defend Holland. A unit can also support a convoyed move.\nTap your army in Belgium, then England's army in London, then Holland. Your army adds its strength to the attack.",
          title: "Convoys don't add strength",
          goal: { kind: "order", source: "bel", aux: "lon", target: "hol" },
          order: franceSupportsHolland(),
        },
        {
          coach:
            "The army will land with a strength of two. Even if Germany holds, that's only one. **Hold orders can be supported just like move orders, to defend** — but Germany is alone. Confirm your order.",
          title: "Confirm your order",
          goal: { kind: "confirm" },
          primaryLabel: "Confirm your order",
          resolvedBoard: convoyResolved,
        },
        {
          coach:
            "Your support helped England's army into Holland. Germany failed to hold. Since only one unit can occupy a province, Germany's is **dislodged**. Its owner now gets a brief retreat phase.",
          title: "The landing",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: {
            phase: convoyResolved.phase,
            orders: [englandConvoyFleet(), germanyHoldsHolland(true)],
          },
        },
        {
          coach:
            "A dislodged unit isn't destroyed — it must retreat to an empty neighboring province where there was no bounce. Germany falls back to Ruhr.\n**A hold can be supported to defend it — but Germany's wasn't, so it fell.**",
          title: "Retreats",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: {
            phase: convoyResolved.phase,
            orders: [germanyRetreatsToRuhr()],
          },
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
            "During adjustment, SCs are counted. Belgium is finally yours now (shown in blue). You control more centers than you have units, so you may build one.",
          title: "Counting centers",
          goal: { kind: "continue" },
          primaryLabel: "Next",
        },
        {
          coach:
            "You can only build on an **empty home center** (depending on variant). On a coastal center you can choose a fleet or an army. Tap Paris to build an army there.",
          title: "Build a unit",
          goal: { kind: "select", province: "par" },
          highlight: ["par"],
          tappable: ["par"],
        },
        {
          coach:
            "Done — you've built an army in Paris. Germany, however, lost a center. With fewer centers than units, it must **disband** one — the owner chooses which.",
          title: "France builds",
          goal: { kind: "continue" },
          primaryLabel: "Next",
          enterBoard: afterBuild,
        },
        {
          coach:
            "Germany removes its army in Ruhr. You're stronger now — but a long way from the 18 SCs you need to win.\nMaybe it's time to betray England's trust…",
          title: "Germany disbands",
          goal: { kind: "continue" },
          primaryLabel: "Finish",
          enterBoard: afterDisband,
        },
      ],
    },
  ];
}
