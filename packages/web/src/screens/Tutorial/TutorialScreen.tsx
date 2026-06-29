import React, { Suspense, useMemo } from "react";
import { useNavigate } from "react-router";
import { PartyPopper } from "lucide-react";
import {
  useVariantsListSuspense,
  type Variant,
} from "@/api/generated/endpoints";
import { useIsDesktopWeb } from "@/hooks/use-platform";
import { Button } from "@/components/ui/button";
import { Notice } from "@/components/Notice";
import { Navigation } from "@/components/Navigation";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { buildLessons } from "./lessons";
import { useTutorialEngine } from "./useTutorialEngine";
import { MapView } from "@/components/MapView";
import { CoachCard } from "./components/CoachCard";
import { ScriptedChat } from "./components/ScriptedChat";

interface TutorialProps {
  variant: Variant;
}

const Tutorial: React.FC<TutorialProps> = ({ variant }) => {
  const navigate = useNavigate();
  const isDesktopWeb = useIsDesktopWeb();
  const panHint = isDesktopWeb
    ? "Mousewheel (or pinch) to zoom and drag to move the map"
    : "Pinch to zoom and drag to move the map";
  const lessons = useMemo(
    () => buildLessons(variant, panHint),
    [variant, panHint]
  );
  const engine = useTutorialEngine(lessons);

  const { step, primaryAction } = engine;
  const you = variant.nations.find(n => n.nationId === "france");
  const ally = variant.nations.find(n => n.nationId === step.ally);
  const showChatScreen =
    step.goal.kind === "chat" &&
    step.chat &&
    engine.view === "chat" &&
    you &&
    ally &&
    primaryAction;

  const onNavClick = (path: string) =>
    engine.setView(path === "chat" ? "chat" : "map");
  const showNav = engine.showNav && !engine.finished;

  return (
    <div className="flex h-[100dvh] w-full overflow-hidden bg-background">
      {/* Desktop sidebar — mirrors the real game's icon rail */}
      {showNav && (
        <aside className="hidden md:flex w-14 flex-col border-r bg-sidebar">
          <Navigation
            items={engine.navItems}
            variant="compact"
            onItemClick={onNavClick}
          />
        </aside>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="relative min-h-0 flex-1">
          <MapView
            mode="interactive"
            variant={variant}
            phase={engine.board.phase}
            orders={engine.board.orders}
            selected={engine.selected}
            highlighted={engine.highlighted}
            renderableProvinces={engine.tappable}
            focus={engine.focus}
            onClickProvince={province => engine.onProvinceClick(province)}
          />

          {engine.bannerText !== null && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-black/70 text-white px-4 py-2 rounded-full text-sm font-medium pointer-events-none whitespace-nowrap">
              {engine.bannerText}
            </div>
          )}

          {engine.finished ? (
            <div className="absolute inset-0 z-30 flex items-center justify-center bg-background/80 p-6">
              <div className="w-full max-w-sm space-y-4 rounded-2xl border bg-card p-6 text-center shadow-lg">
                <PartyPopper className="mx-auto size-10 text-primary" />
                <h2 className="text-xl font-semibold">You know the basics.</h2>
                <p className="text-sm text-muted-foreground">
                  You can now join a game with real people. However, we{" "}
                  <strong>strongly recommend</strong> reading the full 'How to
                  Play' after joining your game.
                  <br />
                  There are some edge cases, and there's nothing worse than
                  watching a plan you spent three days on fall apart because you
                  misread a rule.
                  <br />
                  <br />
                  And games are slow, so you'll have plenty of time to read up
                  while discussing your first moves.
                </p>
                <div className="flex flex-col gap-2">
                  <Button onClick={() => navigate("/find-games")}>
                    Find a game
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => navigate("/learn-to-play")}
                  >
                    Read the detailed rules
                  </Button>
                  <Button variant="ghost" onClick={engine.restart}>
                    Replay the tutorial
                  </Button>
                </div>
              </div>
            </div>
          ) : showChatScreen ? (
            <ScriptedChat
              script={step.chat!}
              you={you!}
              ally={ally!}
              continueLabel={primaryAction!.label}
              onContinue={primaryAction!.run}
            />
          ) : (
            <CoachCard engine={engine} />
          )}
        </div>

        {/* Mobile bottom navigation */}
        {showNav && (
          <div className="border-t bg-background md:hidden">
            <Navigation
              items={engine.navItems}
              variant="bottom"
              onItemClick={onNavClick}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const TutorialScreen: React.FC = () => {
  const { data: variants } = useVariantsListSuspense();
  const variant = variants.find(v => v.id === "classical");

  if (!variant) {
    return (
      <div className="flex h-[100dvh] items-center justify-center p-6">
        <Notice
          title="Tutorial unavailable"
          message="The classical map could not be loaded."
        />
      </div>
    );
  }

  return <Tutorial variant={variant} />;
};

const TutorialScreenSuspense: React.FC = () => (
  <QueryErrorBoundary>
    <Suspense fallback={<div className="h-[100dvh]" />}>
      <TutorialScreen />
    </Suspense>
  </QueryErrorBoundary>
);

export { TutorialScreenSuspense as TutorialScreen };
