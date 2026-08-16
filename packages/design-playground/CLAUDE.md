# CLAUDE.md — Design Playground

Guidance for Claude Code when working in `packages/design-playground/`.

**These rules override the repository root `CLAUDE.md` for everything under this
directory.** Where the two disagree, this file wins. Read the overrides section
before applying any habit learned from the main app.

---

## What this is

A standalone React app for prototyping screens before we build them. It builds
and deploys independently to its own Netlify site at
`diplicity-design-playground.netlify.app`. It has no backend, no API client, no
authentication and no real data.

Nothing here ever ships to users. Prototype code exists to be argued about and
then deleted.

```bash
npm run dev     # http://localhost:5175
npm run build   # tsc -b && vite build
npm run lint    # eslint .
```

---

## The one rule that cannot be broken

**Never import anything from `packages/web`, or from any other package.**

If you need a component, a type, a fixture, a hook or a shadcn primitive that
exists in the main app, **copy it into this package**. Do not import it, do not
alias it, do not reach across with a relative path.

This is enforced by `no-restricted-imports` in `eslint.config.js`, so a
violation fails `npm run lint`. Do not weaken or disable that rule.

The playground is allowed to drift away from the main app's implementation. That
is the point: a prototype must be free to change a component in ways production
is not ready for. The cost is that the playground slowly stops matching the real
product — the fix for that is deleting stale prototypes, never a shared import.

The dependency direction is one-way and absolute: `packages/web` must **never**
import from here either.

---

## Overrides of the root CLAUDE.md

| Root rule | Here |
|---|---|
| Write tests alongside features | **No tests.** This code is disposable; tests on it are waste. There is no test runner in this package. |
| Follow existing patterns; new code indistinguishable from old | **Deliberate divergence is the point.** Match the app's look, not its abstractions. |
| Simplicity — remove anything not required | **Parallel variants of one screen are required.** Do not consolidate two variants into one parameterised component. |
| Reuse existing components | **Duplicate, never reuse across the package boundary.** |

Rules that still apply: no code comments or docstrings, TypeScript strict mode
with no `any`, never suppress lint or type errors, and lint plus build must pass
before a change is finished.

---

## Never rebuild the interactive map

Wherever a prototype shows a map, use `<StaticMap />`, which renders
`public/classical-board.svg` as a flat image.

Do not port, copy or reimplement `GameMap`, `GameMapCanvas`, `InteractiveMap`,
the `.dsvg` parser, Leaflet, or any pan/zoom/highlight logic. That is roughly
3,500 lines whose behaviour is an engineering problem, not a design question,
and maintaining a second copy of it is exactly the cost this playground exists
to avoid. If a design question genuinely turns on map interaction, prototype the
surrounding screen and argue the map behaviour in prose.

---

## Structure

```
src/
  manifest.tsx        Single source of truth: prototypes, variants, states, routes
  Router.tsx          Builds routes from the manifest
  screens/            Index and NotFound (playground's own chrome)
  prototypes/         One directory per prototype, one file per variant
  components/         Shells and shared pieces, all duplicated from the app
  components/ui/      Duplicated shadcn primitives
  data/               Hand-written types and fixtures
```

### Data

Hand-written types in `data/types.ts`, plain fixture objects in
`data/fixtures.ts`, passed to components as props.

There is **no MSW, no react-query, no generated OpenAPI types, and no network
layer**. Do not add them. Fixtures need to be plausible, not accurate — invent
states the real API cannot currently produce if the design calls for it. Only
model the fields a prototype actually renders.

### Adding a prototype or variant

1. Add the component under `prototypes/<prototype-slug>/<VariantName>.tsx`.
2. Register it in `manifest.tsx`. Routes and the index page are both generated
   from that file, so a variant missing from the manifest does not exist.
3. Give every variant a `description` that says what design position it takes,
   not what it contains.

### URLs

```
/                                          index of everything
/<prototype>/<variant>                     first state
/<prototype>/<variant>/<state>             a specific data state
```

Name variants for the idea they represent (`single-list`, `grouped-by-phase`),
never `v1`/`v2`. Numbered names imply a progression that does not exist when the
options are genuinely different directions.

Routes render the prototype **bare** — full-bleed, no playground chrome on top.
The index page is the only navigation. Do not add a floating toolbar, theme
switcher or device frame; they contaminate the thing being judged. Theme follows
the viewer's `prefers-color-scheme`.

---

## Lifecycle

1. **Add variants, do not mutate them.** Changing an existing variant destroys
   the comparison someone is mid-argument about. Add a new one instead.
2. **Prototype code is rewritten into the app, never moved.** When a direction
   wins, the real implementation is written fresh in `packages/web` against real
   data and real types. "It already works" is not a reason to promote playground
   code into production.
3. **Delete the losers once a decision lands.** After a direction is implemented
   in the main app, delete every variant of that screen that was not chosen. At
   rest there should be exactly **one** version of each screen here — or none,
   if the screen is settled and the prototype no longer earns its place.
4. **Do not keep a decision log.** Decisions are recorded in the pull request and
   the discussion that produced them; a file here would go stale.
