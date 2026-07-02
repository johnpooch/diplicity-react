import { http, HttpResponse } from "msw";
import type {
  GameList,
  PaginatedGameListList,
  PhaseList,
  Version,
} from "@/api/generated/endpoints";
import {
  allVariants,
  botRoster,
  currentUserProfile,
  fixtureByGameId,
  makeBotMember,
  publicProfiles,
} from "./fixtures";
import classicalMapSvg from "./fixtures/data/classical-map.svg?raw";
import cantonMapSvg from "./fixtures/data/canton.d.svg?raw";
import hundredMapSvg from "./fixtures/data/hundred.d.svg?raw";
import vietnamMapSvg from "./fixtures/data/vietnam-war.d.svg?raw";
import youngstownMapSvg from "./fixtures/data/youngstown-redux.d.svg?raw";
import austriaFlag from "./fixtures/data/flags/austria.svg?raw";
import englandFlag from "./fixtures/data/flags/england.svg?raw";
import franceFlag from "./fixtures/data/flags/france.svg?raw";
import germanyFlag from "./fixtures/data/flags/germany.svg?raw";
import italyFlag from "./fixtures/data/flags/italy.svg?raw";
import russiaFlag from "./fixtures/data/flags/russia.svg?raw";
import turkeyFlag from "./fixtures/data/flags/turkey.svg?raw";

const flags: Record<string, string> = {
  austria: austriaFlag,
  england: englandFlag,
  france: franceFlag,
  germany: germanyFlag,
  italy: italyFlag,
  russia: russiaFlag,
  turkey: turkeyFlag,
};

const mapSvgs: Record<string, string> = {
  "canton.d.svg": cantonMapSvg,
  "hundred.d.svg": hundredMapSvg,
  "vietnam-war.d.svg": vietnamMapSvg,
  "youngstown-redux.d.svg": youngstownMapSvg,
};

const svgResponse = (body: string) =>
  new HttpResponse(body, {
    headers: { "Content-Type": "image/svg+xml" },
  });

const paginated = (games: GameList[]): PaginatedGameListList => ({
  count: games.length,
  next: null,
  previous: null,
  results: games,
});

const toPhaseList = (fixture: (typeof fixtureByGameId)[string]): PhaseList[] =>
  fixture.phases.map(p => ({
    id: p.id,
    ordinal: p.ordinal,
    season: p.season,
    year: p.year,
    name: p.name,
    type: p.type,
    status: p.status,
  }));

const gameOr404 = (gameId: string | readonly string[]) => {
  const fixture = fixtureByGameId[String(gameId)];
  if (!fixture) return null;
  return fixture;
};

const notFound = () =>
  HttpResponse.json({ detail: "Not found." }, { status: 404 });

const recoveredCivilDisorderGames = new Set<string>();

export const handlers = [
  http.get("*/version/", () =>
    HttpResponse.json({ environment: "mock", version: "mock" } satisfies Version)
  ),

  http.get("*/variants/", () => HttpResponse.json(allVariants)),

  http.get("*/variants/:variantId/", ({ params }) => {
    const variant = allVariants.find(v => v.id === params.variantId);
    return variant ? HttpResponse.json(variant) : notFound();
  }),

  http.get("*/mock-assets/classical-map.svg", () =>
    svgResponse(classicalMapSvg)
  ),

  http.get("*/mock-assets/:file", ({ params }) => {
    const svg = mapSvgs[String(params.file)];
    return svg ? svgResponse(svg) : notFound();
  }),

  http.get("*/mock-assets/flags/:nationId", ({ params }) => {
    const flag = flags[String(params.nationId).replace(/\.svg$/, "")];
    return flag ? svgResponse(flag) : notFound();
  }),

  http.get("*/user/", () => HttpResponse.json(currentUserProfile)),

  http.get("*/users/:userId/", ({ params }) => {
    const profile = publicProfiles[Number(params.userId)];
    return profile ? HttpResponse.json(profile) : notFound();
  }),

  http.get("*/games/find-similar/", () => HttpResponse.json({ game: null })),

  http.get("*/games/", ({ request }) => {
    const url = new URL(request.url);
    let games = Object.values(fixtureByGameId).map(f => ({
      ...f.game,
      totalUnreadMessageCount: f.totalUnreadMessageCount,
    }));
    const mine = url.searchParams.get("mine");
    if (mine !== null) {
      games = games.filter(
        g => g.members.some(m => m.isCurrentUser) === (mine === "true")
      );
    }
    const status = url.searchParams.get("status");
    if (status) {
      games = games.filter(g => g.status === status);
    }
    const canJoin = url.searchParams.get("can_join");
    if (canJoin !== null) {
      games = games.filter(g => g.canJoin === (canJoin === "true"));
    }
    const sandbox = url.searchParams.get("sandbox");
    if (sandbox !== null) {
      games = games.filter(g => g.sandbox === (sandbox === "true"));
    }
    const variant = url.searchParams.get("variant");
    if (variant) {
      games = games.filter(g => g.variantId === variant);
    }
    return HttpResponse.json(paginated(games));
  }),

  http.get("*/game/:gameId/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    const game = { ...fixture.game } as Record<string, unknown>;
    delete game.currentPhase;
    const members = recoveredCivilDisorderGames.has(String(params.gameId))
      ? fixture.game.members.map(m =>
          m.isCurrentUser ? { ...m, civilDisorder: false } : m
        )
      : fixture.game.members;
    return HttpResponse.json({
      ...game,
      members,
      totalUnreadMessageCount: fixture.totalUnreadMessageCount,
    });
  }),

  http.get("*/game/:gameId/phases/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    return fixture ? HttpResponse.json(toPhaseList(fixture)) : notFound();
  }),

  http.get("*/game/:gameId/phase/:phaseId/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    const phase = fixture?.phases.find(p => p.id === Number(params.phaseId));
    return phase ? HttpResponse.json(phase) : notFound();
  }),

  http.get("*/game/:gameId/orders/:phaseId", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    return HttpResponse.json(
      fixture.ordersByPhase[Number(params.phaseId)] ?? []
    );
  }),

  http.get("*/game/:gameId/phase-states/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    return fixture ? HttpResponse.json(fixture.phaseStates) : notFound();
  }),

  http.get("*/game/:gameId/options/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    return fixture ? HttpResponse.json(fixture.options) : notFound();
  }),

  http.get("*/games/:gameId/channels/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    return fixture ? HttpResponse.json(fixture.channels) : notFound();
  }),

  http.get("*/games/:gameId/draw-proposals/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    return fixture ? HttpResponse.json(fixture.drawProposals) : notFound();
  }),

  http.get("*/devices/", () => HttpResponse.json([])),
  http.post("*/devices/", () => HttpResponse.json({}, { status: 201 })),

  http.post("*/api/token/refresh/", () =>
    HttpResponse.json({ access: "mock-access-token" })
  ),

  http.post("*/game/", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { id: "pending-some-players", ...body },
      { status: 201 }
    );
  }),

  http.post("*/sandbox-game/", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { id: "active-movement", ...body },
      { status: 201 }
    );
  }),

  http.post("*/game/:gameId/join/", () =>
    HttpResponse.json({}, { status: 201 })
  ),
  http.get("*/game/:gameId/available-bots/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    const memberUserIds = new Set(fixture.game.members.map(m => m.userId));
    return HttpResponse.json(
      botRoster.filter(bot => !memberUserIds.has(bot.userId))
    );
  }),
  http.post("*/game/:gameId/add-bot/", async ({ params, request }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    const body = (await request.json()) as { userId: number };
    const bot = botRoster.find(b => b.userId === body.userId);
    if (!bot) {
      return HttpResponse.json(
        { userId: ["This bot is not available to add to this game."] },
        { status: 400 }
      );
    }
    const member = makeBotMember(bot);
    fixture.game = { ...fixture.game, members: [...fixture.game.members, member] };
    return HttpResponse.json(member, { status: 201 });
  }),
  http.delete("*/game/:gameId/kick/:memberId/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    fixture.game = {
      ...fixture.game,
      members: fixture.game.members.filter(
        m => m.id !== Number(params.memberId)
      ),
    };
    return new HttpResponse(null, { status: 204 });
  }),
  http.delete("*/game/:gameId/leave/", () => new HttpResponse(null, { status: 204 })),
  http.delete("*/game/:gameId/delete/", () => new HttpResponse(null, { status: 204 })),
  http.patch("*/game/:gameId/confirm-phase/", () => HttpResponse.json({})),
  http.post("*/game/:gameId/resolve-phase/", () => HttpResponse.json({})),
  http.put("*/game/:gameId/pause/", () => HttpResponse.json({})),
  http.patch("*/game/:gameId/unpause/", () => HttpResponse.json({})),
  http.put("*/game/:gameId/extend-deadline/", () => HttpResponse.json({})),
  http.patch("*/game/:gameId/extend-deadline/", () => HttpResponse.json({})),
  http.post("*/game/:gameId/clone-to-sandbox/", () =>
    HttpResponse.json({ id: "active-movement" }, { status: 201 })
  ),

  http.post("*/game/:gameId/recover-from-civil-disorder/", ({ params }) => {
    const fixture = gameOr404(params.gameId as string);
    if (!fixture) return notFound();
    const member = fixture.game.members.find(m => m.isCurrentUser);
    if (!member) return notFound();
    recoveredCivilDisorderGames.add(String(params.gameId));
    return HttpResponse.json({ ...member, civilDisorder: false });
  }),

  http.post("*/game/:gameId/orders/", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(body, { status: 201 });
  }),
  http.delete("*/game/:gameId/orders/delete/:sourceId", () =>
    new HttpResponse(null, { status: 204 })
  ),

  http.post("*/games/:gameId/channels/create/", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { id: 999, name: "New Channel", private: true, messages: [], unreadMessageCount: 0, ...body },
      { status: 201 }
    );
  }),
  http.post(
    "*/games/:gameId/channels/:channelId/messages/create/",
    async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(body, { status: 201 });
    }
  ),
  http.post("*/games/:gameId/channels/:channelId/mark-read/", () =>
    HttpResponse.json({})
  ),

  http.post("*/games/:gameId/draw-proposals/create/", () =>
    HttpResponse.json({}, { status: 201 })
  ),
  http.patch("*/games/:gameId/draw-proposals/:proposalId/vote/", () =>
    HttpResponse.json({})
  ),
  http.delete("*/games/:gameId/draw-proposals/:proposalId/cancel/", () =>
    new HttpResponse(null, { status: 204 })
  ),

  http.patch("*/user/update/", () => HttpResponse.json(currentUserProfile)),
  http.put("*/user/update/", () => HttpResponse.json(currentUserProfile)),
  http.delete("*/user/delete/", () => new HttpResponse(null, { status: 204 })),
];
