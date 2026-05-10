import React from "react";

interface ShotProps {
  label: string;
  caption?: string;
  src?: string;
}

const Shot: React.FC<ShotProps> = ({ label, caption, src }) => (
  <div>
    <div className="aspect-square overflow-hidden rounded-sm">
      {src ? (
        <img src={src} alt={label} className="w-full h-full object-cover" />
      ) : (
        <div
          className="w-full h-full flex items-center justify-center"
          style={{
            background:
              "repeating-linear-gradient(135deg, oklch(0.97 0 0) 0px, oklch(0.97 0 0) 8px, oklch(0.94 0 0) 8px, oklch(0.94 0 0) 9px)",
          }}
        >
          <span className="font-mono text-[11px] tracking-[0.14em] uppercase text-muted-foreground bg-background px-2.5 py-1.5 border border-border rounded-sm">
            {label}
          </span>
        </div>
      )}
    </div>
    {caption && (
      <span className="block text-sm text-muted-foreground mt-2.5">{caption}</span>
    )}
  </div>
);

const CardShot: React.FC<{ label: string; src?: string }> = ({ label, src }) => (
  <div className="aspect-square overflow-hidden border-b border-border">
    {src ? (
      <img src={src} alt={label} className="w-full h-full object-cover" />
    ) : (
      <div
        className="w-full h-full flex items-center justify-center"
        style={{
          background:
            "repeating-linear-gradient(135deg, oklch(0.97 0 0) 0px, oklch(0.97 0 0) 8px, oklch(0.94 0 0) 8px, oklch(0.94 0 0) 9px)",
        }}
      >
        <span className="font-mono text-[11px] tracking-[0.14em] uppercase text-muted-foreground bg-background px-2.5 py-1.5 border border-border rounded-sm">
          {label}
        </span>
      </div>
    )}
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
  <p className={`text-[17px] leading-[1.65] text-foreground/80 ${className ?? ""}`}>
    {children}
  </p>
);

const Italic: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p className="text-[17px] leading-[1.65] italic text-muted-foreground">
    {children}
  </p>
);

const GuideContent: React.FC = () => (
  <article className="px-6 pb-24">
    {/* I */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>I · The premise</SectionNum>
      <SectionHeading>
        Diplomacy is a game about people.
      </SectionHeading>
      <Body className="mt-[18px]">
        Yes, there are armies and fleets. But the game is really about <em>talking </em> 
        to the other players, making plans together, and figuring out who you
        can trust.
      </Body>
      <Body>
        You cannot win on your own for very long. At some point you need allies,
        even if those alliances eventually fall apart.
      </Body>
      <Body>
        There are no dice rolls or random events. Every outcome comes from the
        decisions players make. Everyone submits orders secretly, they are all
        revealed at the same time, and then you find out whose plans actually
        worked.
      </Body>
    </section>

    <Divider />

    {/* II */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>II · The goal</SectionNum>
          <SectionHeading>Control enough supply centers to win.</SectionHeading>
          <Body className="mt-[18px]">
            Supply centers are the important territories on the map. They
            determine how many units you can support.
          </Body>
          <Body>
            More centers means more units. More units means more influence over
            the board.
          </Body>
          <Body>
            If you control half the supply centers, you win the game outright.
          </Body>
        </div>
        <Shot
          src="/guidecontent/fig1.png"
          label="Map · Supply centers"
          caption="Fig. 01 — French supply centers - while Belgium remains unoccupied."
        />
      </div>
    </section>

    <Divider />

    {/* III */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>III · How a turn works</SectionNum>
      <SectionHeading>Talk first. Orders second.</SectionHeading>
<Body className="mt-[18px]">
        A turn usually starts with conversations. You message other players,
        discuss plans, coordinate attacks, or try to make sure nobody attacks
        you.
      </Body>

      <Body>
        After that, everyone submits orders privately.
      </Body>

      <Body>
        Once the deadline hits, all orders resolve simultaneously. There is no
        turn order and no reaction time — you only see the full picture after
        everything is revealed.
      </Body>

      <Body>
        At the end of the year, the number of supply centers you control
        determines whether you gain or lose units.
      </Body>

      <Italic>
        A year consists of Spring and Fall turns, followed by Winter
        adjustments. Supply centers only count after the Fall turn.
      </Italic>
    </section>

    <Divider />

    {/* IV */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>IV · Your units</SectionNum>
      <SectionHeading>There are only two unit types.</SectionHeading>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-7">
        <div className="border border-border rounded-lg p-5 flex items-start gap-4 bg-card">
          <div className="size-11 border-[1.5px] border-foreground flex items-center justify-center font-semibold rounded-full shrink-0 text-foreground">
            A
          </div>
          <div>
            <h3 className="text-[17px] font-semibold mb-0.5 text-foreground">
              Army
            </h3>
            <p className="text-sm text-muted-foreground m-0">
              Moves across land territories. Armies cannot move into sea spaces,
              but fleets can convoy them across water.
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
              Moves across water and coastal territories (lands bordering water). Fleets are also what
              make convoys possible.
            </p>
          </div>
        </div>
      </div>
    </section>

    <Divider />

    {/* V */}
    <section className="max-w-[1040px] mx-auto py-14">
      <SectionNum>V · Orders</SectionNum>
      <SectionHeading>Every unit gets one order each turn.</SectionHeading>
      <p className="text-[17px] leading-[1.65] text-foreground/80 mt-[18px] max-w-[680px]">
        There are four kinds of orders, with Support being the most important. A single unit is
        weak by itself, but coordinated units become difficult to stop.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mt-8">
        {[
          {
            label: "Hold",
            src: "/guidecontent/fig2.png",
            syntax: "Army Budapest Holds",
            desc: "The unit stays where it is and defends the territory - here preventing any potential attack from Galicia.",
          },
          {
            label: "Move",
            src: "/guidecontent/fig3.png",
            syntax: "Fleet NRG – Norway",
            desc: "The unit attempts to move into a neighboring territory - capturing the supply center in Norway (if held until the Adjustment phase).",
          },
          {
            label: "Support",
            src: "/guidecontent/fig4.png",
            syntax: "Army Rumania Supports Army Budapest – Serbia",
            desc: "Adds strength to another unit, either for attack or defense. Supporting units do not move themselves.",
          },
          {
            label: "Convoy",
            src: "/guidecontent/fig5.png",
            syntax: "Fleet NTH Convoys Army Edinburgh – Holland",
            desc: "Fleets allows an army to travel across water. A convoy succeeds even if the fleet is attacked - unless it has to retreat.",
          },
        ].map(({ label, src, syntax, desc }) => (
          <div
            key={label}
            className="bg-card border border-border rounded-lg overflow-hidden flex flex-col"
          >
            <CardShot label={label} src={src} />
            <div className="p-[18px_20px_20px]">
              <h3 className="text-lg font-semibold mb-1 text-foreground">
                {label}
              </h3>
              <div className="font-mono text-[12.5px] text-muted-foreground mb-3">
                {syntax}
              </div>
              <p className="text-[14.5px] text-muted-foreground m-0">{desc}</p>
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
          <SectionNum>VI · Combat</SectionNum>
          <SectionHeading>Support decides most battles.</SectionHeading>
          <Body className="mt-[18px]">
            Every unit has a base strength of one. Each supporting unit adds one
            more strength.
          </Body>
          <Body>
            If the attacking side is stronger, the defending unit is "dislodged" and has to
            retreat.
          </Body>
          <Italic>You cannot dislodge your own units, even with support. You cannot support an attack against yourself.</Italic>
        </div>
        <div className="lg:order-1">
          <Shot
            src="/guidecontent/fig6.png"
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
          <SectionNum>VII · Bounces</SectionNum>
          <SectionHeading>Equal strength means nobody moves.</SectionHeading>
          <Body className="mt-[18px]">
            If two opposing sides have the same strength, neither succeeds.
            Both units stay where they are.
          </Body>
          <div className="border border-border rounded-lg bg-secondary p-5 my-7">
            <div className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground mb-1.5">
              Rule
            </div>
            <div className="text-[17px] font-medium leading-[1.4] text-foreground">
            Equal strength? No one moves. It always results in a bounce.
            </div>
          </div>
          <Body>
            Even failed attacks can still matter, because they can block another player units from moving.
          </Body>
          <Italic>
            This also applies when two units try to swap places; neither succeeds.
          </Italic>
        </div>
        <Shot
          src="/guidecontent/fig7.png"
          label="1 vs 1 · Bounce"
          caption="Fig. 07 — Neither side has enough strength to enter the Black Sea."
        />
      </div>
    </section>

    <Divider />

    {/* VIII · Cut support */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>VIII · A key tactic</SectionNum>
          <SectionHeading>Cutting support.</SectionHeading>
          <Body className="mt-[18px]">
            Support only works if the supporting unit is left alone.
          </Body>
          <Body>
            If you attack a unit that is giving support, whether it succeeds or not, that support is cut.
          </Body>
          <Body>This is one of the most important tactical ideas in the game, and
            often the easiest way to break strong defenses.</Body>
        </div>
        <Shot
          src="/guidecontent/fig8.png"
          label="Cut support"
          caption="Fig. 08 — Berlin attacks Silesia and bounces, but Galicia loses Silesias support and bounces with Warsaw."
        />
      </div>
    </section>

    <Divider />

    {/* IX · Retreats */}
    <section className="max-w-[1040px] mx-auto py-14">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-7 lg:gap-14 items-center">
        <div>
          <SectionNum>IX · Retreats</SectionNum>
          <SectionHeading>Dislodged units must retreat.</SectionHeading>
          <Body className="mt-[18px]">
            A defeated unit does not disappear immediately. Instead, it must
            retreat to an adjacent <em>empty</em> territory.
          </Body>
          <Body>
            It cannot retreat to the territory the attack came from, or to any
            territory where there was a bounce that turn.
          </Body>
          <Italic>
            If there are retreats, players get an extra turn to decide where to
            send them. If there is no legal retreat, the unit is destroyed immediately.
          </Italic>
        </div>
        <Shot
          src="/guidecontent/fig9.png"
          label="Retreat"
          caption="Fig. 09 — The English Channel was supported by the Irish Sea. The French fleet needs to retreat anywhere else."
        />
      </div>
    </section>

    <Divider />

    {/* X · Supply centers */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>X · Supply centers</SectionNum>
      <SectionHeading>Centers determine your strength.</SectionHeading>
      <Body className="mt-[18px]">
        At the end of each year, you compare the number of supply centers you
        control with the number of units you have on the board.
      </Body>
      <Body>If you control more centers than units, you build new units. If you
        control fewer, you must remove some (you decide which).</Body>
      <Italic>Most variants only allow new units to be built in empty home centers.</Italic>
    </section>

    <blockquote className="max-w-[800px] mx-auto text-center text-[clamp(28px,3.5vw,40px)] leading-[1.2] font-semibold tracking-[-0.02em] text-foreground py-16">
      The rules are simple. The difficult part is playing the people.
    </blockquote>

    {/* XI · The real game */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>XI · The real game</SectionNum>
      <SectionHeading>Games are decided through negotiation.</SectionHeading>
      <Body className="mt-[18px]">
        You will spend a lot of time making deals, sharing information, and
        trying to understand what other players actually want.
      </Body>
      <Body>Alliances matter, especially early on. But because only one player can
        win, alliances eventually become unstable.</Body>
      <Body>
        Nothing is binding. Players can lie, change plans, or turn on each
        other at any time.
      </Body>
      <Body>
        Strong players are usually not the loudest or most aggressive. They are
        the ones who manage trust well and recognize the right moment to shift
        direction.
      </Body>
    </section>

    <Divider />

    {/* XII · Getting started */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>XII · Getting started</SectionNum>
      <SectionHeading>Don't worry about playing perfectly.</SectionHeading>
      <Body className="mt-[18px]">
        Talk to your neighbors. Make simple plans. Use support to help each
        other. Pay attention to who is working with you — and who isn't.
      </Body>
      <Body>You'll learn quickly by playing.</Body>     <Body className="mt-[18px]">
        Start simple. Talk to your neighbors. Make basic agreements. Learn how
        support works and pay attention to who follows through on their word.
      </Body>

      <Body>
        Most people understand the rules after a few turns. The difficult part
        is learning how different players think.
      </Body>

      <Body>
        Even if you fall behind, you still matter. A single surviving unit can
        influence negotiations, block movement, or decide who wins a larger
        conflict.
      </Body>

      <div className="border border-border rounded-lg bg-secondary p-5 my-7">
        <div className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground mb-1.5">
          About pacing
        </div>

        <div className="text-[17px] font-medium leading-[1.4] text-foreground">
          Games move at a real-life pace. Sometimes conversations are constant;
          sometimes several hours pass while people are at work, asleep, or
          thinking about their next move. That slower rhythm is part of what
          makes the diplomacy feel real.
        </div>
      </div>
    </section>

    <Divider />

    {/* In short */}
    <section className="max-w-[720px] mx-auto py-14">
      <SectionNum>In short</SectionNum>
      <p className="text-[20px] leading-[1.5] text-foreground mt-4">
        The rules are not very complicated. Understanding the people around the
        table is the hard part.
      </p>
    </section>
  </article>
);

export { GuideContent };
