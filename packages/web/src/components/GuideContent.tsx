import React from "react";

interface ShotProps {
  label: string;
  caption?: string;
}

const Shot: React.FC<ShotProps> = ({ label, caption }) => (
  <div>
    <div
      className="aspect-square flex items-center justify-center"
      style={{
        background:
          "repeating-linear-gradient(135deg, oklch(0.97 0 0) 0px, oklch(0.97 0 0) 8px, oklch(0.94 0 0) 8px, oklch(0.94 0 0) 9px)",
      }}
    >
      <span className="font-mono text-[11px] tracking-[0.14em] uppercase text-muted-foreground bg-background px-2.5 py-1.5 border border-border rounded-sm">
        {label}
      </span>
    </div>
    {caption && (
      <span className="block text-sm text-muted-foreground mt-2.5">{caption}</span>
    )}
  </div>
);

const CardShot: React.FC<{ label: string }> = ({ label }) => (
  <div
    className="aspect-square flex items-center justify-center border-b border-border"
    style={{
      background:
        "repeating-linear-gradient(135deg, oklch(0.97 0 0) 0px, oklch(0.97 0 0) 8px, oklch(0.94 0 0) 8px, oklch(0.94 0 0) 9px)",
    }}
  >
    <span className="font-mono text-[11px] tracking-[0.14em] uppercase text-muted-foreground bg-background px-2.5 py-1.5 border border-border rounded-sm">
      {label}
    </span>
  </div>
);

const Divider: React.FC = () => (
  <hr className="max-w-[720px] mx-auto border-0 border-t border-border" />
);

const SectionNum: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-3 font-medium">
    {children}
  </div>
);

const SectionHeading: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <h2 className="text-[clamp(28px,3.5vw,40px)] font-semibold tracking-[-0.01em] leading-[1.15] text-foreground">
    {children}
  </h2>
);

const Body: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className }) => (
  <p
    className={`text-[17px] leading-[1.65] text-[oklch(0.3_0_0)] ${className ?? ""}`}
  >
    {children}
  </p>
);

const GuideContent: React.FC = () => (
  <article className="px-6 pb-24">
    {/* I */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>I · The premise</SectionNum>
      <SectionHeading>
        You are a diplomat first, a commander second.
      </SectionHeading>
      <Body className="mt-[18px]">
        Yes, you move armies and fleets. But you cannot succeed on your own. The
        game is built around <em>talking</em> to other players, making plans
        together, and deciding who you trust.
      </Body>
      <Body>
        You will negotiate, cooperate, and sometimes betray. There is no
        randomness, no dice, no luck — everything that happens comes from player
        decisions.
      </Body>
    </section>

    <Divider />

    {/* II */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>II · The goal</SectionNum>
          <SectionHeading>Control eighteen supply centers.</SectionHeading>
          <Body className="mt-[18px]">
            Supply centers are the key locations on the map. The more you
            control, the more units you get. The more units you have, the more
            influence you have.
          </Body>
          <Body>Eighteen out of thirty-four wins the game outright.</Body>
        </div>
        <Shot
          label="Map · Supply centers"
          caption="Fig. 01 — Highlighted supply centers across the standard map"
        />
      </div>
    </section>

    <Divider />

    {/* III */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>III · How a turn works</SectionNum>
      <SectionHeading>Each turn has a simple rhythm.</SectionHeading>
      <Body className="mt-[18px]">
        <strong>First</strong>, you talk to other players. You make plans, agree
        on moves, or try to avoid being attacked.
      </Body>
      <Body>
        <strong>Then</strong>, everyone writes down their orders in secret.
      </Body>
      <Body>
        <strong>After that</strong>, all orders are revealed and resolved at the
        same time. There is no turn order — everything happens simultaneously.
      </Body>
      <Body>
        At the end of each year, your number of supply centers determines
        whether you gain or lose units.
      </Body>
    </section>

    <Divider />

    {/* IV */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>IV · Your units</SectionNum>
      <SectionHeading>Two types. That's all.</SectionHeading>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-7">
        <div className="border border-border rounded-lg p-5 flex items-start gap-4 bg-card">
          <div className="size-11 border-[1.5px] border-foreground flex items-center justify-center font-semibold rounded-sm shrink-0 text-foreground">
            A
          </div>
          <div>
            <h3 className="text-[17px] font-semibold mb-0.5 text-foreground">
              Army
            </h3>
            <p className="text-sm text-muted-foreground m-0">
              Moves on land. Cannot enter sea spaces, but can be ferried by
              friendly fleets.
            </p>
          </div>
        </div>
        <div className="border border-border rounded-lg p-5 flex items-start gap-4 bg-card">
          <div className="size-11 border-[1.5px] border-foreground flex items-center justify-center font-semibold rounded-full shrink-0 text-foreground">
            F
          </div>
          <div>
            <h3 className="text-[17px] font-semibold mb-0.5 text-foreground">
              Fleet
            </h3>
            <p className="text-sm text-muted-foreground m-0">
              Moves on water and coasts. Can carry armies across the sea.
            </p>
          </div>
        </div>
      </div>
    </section>

    <Divider />

    {/* V */}
    <section className="max-w-[1040px] mx-auto py-14">
      <SectionNum>V · What units can do</SectionNum>
      <SectionHeading>Each unit gives one order per turn.</SectionHeading>
      <p className="text-[17px] leading-[1.65] text-[oklch(0.3_0_0)] mt-[18px] max-w-[680px]">
        There are four kinds of orders. Support is the most important — units
        are weak alone, but powerful together.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mt-8">
        {[
          {
            label: "Hold",
            syntax: "A PAR H",
            desc: "The unit stays in place and defends its territory.",
          },
          {
            label: "Move",
            syntax: "A PAR – BUR",
            desc: "The unit advances into a neighboring area.",
          },
          {
            label: "Support",
            syntax: "A MAR S A PAR – BUR",
            desc: "One unit reinforces another, making it stronger in attack or defense.",
          },
          {
            label: "Convoy",
            syntax: "F ENG C A LON – BRE",
            desc: "A fleet ferries an army across water — sometimes across half the map.",
          },
        ].map(({ label, syntax, desc }) => (
          <div
            key={label}
            className="bg-card border border-border rounded-lg overflow-hidden flex flex-col"
          >
            <CardShot label={label} />
            <div className="p-[18px_20px_20px]">
              <h3 className="text-lg font-semibold mb-1 text-foreground">
                {label}
              </h3>
              <div className="font-mono text-[12.5px] text-muted-foreground mb-3">
                {syntax}
              </div>
              <p className="text-[14.5px] text-[oklch(0.35_0_0)] m-0">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>

    <Divider />

    {/* VI · Successful attack */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div className="lg:order-2">
          <SectionNum>VI · How combat works</SectionNum>
          <SectionHeading>Strongest side wins.</SectionHeading>
          <Body className="mt-[18px]">
            Every unit has a strength of one. Each support adds one more. The
            strongest side wins; the loser retreats or is destroyed.
          </Body>
          <Body>
            A single unit cannot dislodge another unit on its own — you almost
            always need support to take territory.
          </Body>
        </div>
        <div className="lg:order-1">
          <Shot
            label="2 vs 1 · Successful attack"
            caption="Fig. 06 — Two supported units overpower a lone defender"
          />
        </div>
      </div>
    </section>

    <Divider />

    {/* VII · A bounce */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>VII · A bounce</SectionNum>
          <SectionHeading>Equal strength. Neither moves.</SectionHeading>
          <Body className="mt-[18px]">
            When two sides are equally matched, neither can advance — both units
            stay in place.
          </Body>
          <div className="border border-border rounded-lg bg-secondary p-5 my-7">
            <div className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground mb-1.5">
              Rule
            </div>
            <div className="text-[17px] font-medium leading-[1.4] text-foreground">
              Equal strength = no movement. Both sides bounce in place.
            </div>
          </div>
          <Body>
            Even if your attack fails, it still forces the defending player to
            hold that unit — which can be useful in itself.
          </Body>
        </div>
        <Shot
          label="1 vs 1 · Bounce"
          caption="Fig. 07 — Equally matched units — nobody moves"
        />
      </div>
    </section>

    <Divider />

    {/* VIII · Cut support */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>VIII · One key tactic</SectionNum>
          <SectionHeading>Cutting support.</SectionHeading>
          <Body className="mt-[18px]">
            Support only works if the supporting unit is left alone.
          </Body>
          <Body>
            If you attack a unit that is giving support, its support is canceled
            — even if your attack doesn't succeed.
          </Body>
          <p className="text-[17px] leading-[1.65] italic text-muted-foreground">
            This is often the easiest way to break a strong position.
          </p>
        </div>
        <Shot
          label="Cut support"
          caption="Fig. 08 — A weak attack neutralizes a strong defense"
        />
      </div>
    </section>

    <Divider />

    {/* IX · Supply centers */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>IX · Supply centers</SectionNum>
      <SectionHeading>Centers are what matter.</SectionHeading>
      <Body className="mt-[18px]">
        At the end of the year, you compare how many centers you control with
        how many units you have. If you have more centers, you build units. If
        you have fewer, you remove them.
      </Body>
      <Body>This is how players grow — or fall behind.</Body>
    </section>

    <blockquote className="max-w-[800px] mx-auto text-center text-[clamp(28px,3.5vw,40px)] leading-[1.2] font-semibold tracking-[-0.02em] text-foreground py-16">
      The rules are simple. The people are not.
    </blockquote>

    {/* X · The real game */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>X · The real game</SectionNum>
      <SectionHeading>Diplomacy.</SectionHeading>
      <Body className="mt-[18px]">
        You need other players to succeed, especially early on. You'll form
        alliances and make plans together. But only one player can win, so those
        alliances don't last forever.
      </Body>
      <Body>There are no binding agreements. Players can promise anything.</Body>
      <Body>
        Good players aren't just tactical — they understand timing, trust, and
        when to change sides.
      </Body>
    </section>

    <Divider />

    {/* XI · Getting started */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>XI · Getting started</SectionNum>
      <SectionHeading>Don't worry about playing perfectly.</SectionHeading>
      <Body className="mt-[18px]">
        Talk to your neighbors. Make simple plans. Use support to help each
        other. Pay attention to who is working with you — and who isn't.
      </Body>
      <Body>You'll learn quickly by playing.</Body>
    </section>

    <Divider />

    {/* In short */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>In short</SectionNum>
      <p className="text-[20px] leading-[1.5] text-foreground mt-4">
        You move units on a map — but you win by working with people, until the
        moment comes not to.
      </p>
    </section>
  </article>
);

export { GuideContent };
