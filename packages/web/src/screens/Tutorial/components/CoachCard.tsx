import { Hand, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { TutorialEngine } from "../useTutorialEngine";

interface CoachCardProps {
  engine: TutorialEngine;
}

// Render coach copy with inline **bold** and _italic_ emphasis, preserving newlines.
function renderCoach(text: string): React.ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|_[^_]+_)/).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("_") && part.endsWith("_")) {
      return (
        <em key={i} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}

const CoachCard: React.FC<CoachCardProps> = ({ engine }) => {
  const { step, primaryAction, isFirstStep, skip, progress, setView } = engine;
  // A chat step (shown here only in map view) directs the player to the Chat tab.
  const isChatNav = step.goal.kind === "chat";

  return (
    <div
      className={cn(
        "absolute z-20 bg-card text-card-foreground border shadow-lg",
        "inset-x-0 bottom-0 rounded-t-2xl",
        "md:inset-x-auto md:bottom-auto md:top-4 md:right-4 md:w-[360px] md:rounded-2xl"
      )}
    >
      <div className="p-5 space-y-3 short:p-3 short:space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {progress.lessonTitle}
          </span>
          <div className="flex-1" />
          <div className="flex gap-1">
            {Array.from({ length: progress.stepCount }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  i <= progress.stepIndex ? "bg-primary" : "bg-muted"
                )}
              />
            ))}
          </div>
        </div>

        {step.title && (
          <h2 className="text-lg font-semibold leading-tight short:text-base">{step.title}</h2>
        )}

        <p className="whitespace-pre-line text-[15px] leading-relaxed text-muted-foreground short:text-[13px] short:leading-snug">
          {renderCoach(step.coach)}
        </p>

        {isChatNav ? (
          <button
            type="button"
            onClick={() => setView("chat")}
            className="flex w-full items-center gap-2 rounded-lg bg-muted/60 px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-muted short:py-1.5 short:text-xs"
          >
            <MessageCircle className="size-4 shrink-0" />
            <span>Tap Chat in the menu to continue.</span>
          </button>
        ) : primaryAction === null ? (
          <div className="flex items-center gap-2 rounded-lg bg-muted/60 px-3 py-2 text-sm text-muted-foreground short:py-1.5 short:text-xs">
            <Hand className="size-4 shrink-0" />
            <span>Tap the highlighted area on the map to continue.</span>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Button
              onClick={primaryAction.run}
              className="flex-1 short:h-8 short:px-3"
            >
              {primaryAction.label}
            </Button>
            {isFirstStep && (
              <Button
                variant="ghost"
                onClick={skip}
                className="short:h-8 short:px-3"
              >
                I already know how
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export { CoachCard };
