import React, { Suspense } from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import {
  GameRetrieve,
  Member,
  useGamePhaseRetrieveSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";
import { Button } from "@/components/ui/button";
import { NationFlag, findNationColor, findNationFlagUrl } from "@/components/NationFlag";

type ResultType = "victory" | "draw" | "defeat";

interface ResultInfo {
  type: ResultType;
  title: string;
  blurb: string;
  backgroundImage: string;
  drawMembers: readonly Member[];
}

function computeResult(game: GameRetrieve): ResultInfo | null {
  if (game.status !== "completed" && game.status !== "abandoned") return null;

  const userMember = game.members.find(m => m.isCurrentUser);
  if (!userMember) return null;

  const { victory } = game;
  if (!victory) return null;

  const userIsInVictory = victory.members.some(m => m.id === userMember.id);
  const winnerName = victory.members[0]?.name ?? "A player";

  if (victory.type === "solo") {
    if (userIsInVictory) {
      return {
        type: "victory",
        title: "Victory",
        blurb: `You have conquered Europe, seizing enough supply centers to achieve a solo victory.`,
        backgroundImage: "url('/victory.jpg')",
        drawMembers: [],
      };
    }
    return {
      type: "defeat",
      title: "Defeat",
      blurb: `${winnerName} has achieved a solo victory. Your forces have been overcome — Europe falls under a single dominant power.`,
      backgroundImage: "url('/defeat.jpg')",
      drawMembers: [],
    };
  }

  if (victory.type === "draw") {
    if (userIsInVictory) {
      return {
        type: "draw",
        title: "Draw",
        blurb: "The great powers have agreed to a negotiated peace. No single nation dominates — Europe is divided among the surviving powers.",
        backgroundImage: "url('/draw.jpg')",
        drawMembers: victory.members,
      };
    }
    return {
      type: "defeat",
      title: "Defeat",
      blurb: "The surviving powers agreed to a negotiated peace — but your nation had already been eliminated before the armistice was reached.",
      backgroundImage: "url('/defeat.jpg')",
      drawMembers: victory.members,
    };
  }

  return null;
}

interface NationRowProps {
  member: { id: number; nation: string | null; name: string };
  scCount: number;
  flagUrl: string | null;
  color: string | null;
  dim?: boolean;
}

const NationRow: React.FC<NationRowProps> = ({ member, scCount, flagUrl, color, dim }) => (
  <div className={`flex items-center gap-3 py-2.5 ${dim ? "opacity-50" : ""}`}>
    <NationFlag flagUrl={flagUrl} alt={member.nation ?? ""} size="sm" color={color} className="shrink-0" />
    <div className="flex-1 min-w-0">
      <p className="text-white font-medium text-sm leading-tight">{member.nation ?? "—"}</p>
      <p className="text-white/50 text-xs">{member.name}</p>
    </div>
    <span className="text-white/70 text-sm font-mono tabular-nums shrink-0">{scCount} SC</span>
  </div>
);

interface GameEndDialogInnerProps {
  game: GameRetrieve;
  result: ResultInfo;
}

const GameEndDialogInner: React.FC<GameEndDialogInnerProps> = ({ game, result }) => {
  const lastPhaseId = game.phases[game.phases.length - 1];
  const { data: phase } = useGamePhaseRetrieveSuspense(game.id, lastPhaseId);
  const { data: variants } = useVariantsListSuspense();

  const variant = variants.find(v => v.id === game.variantId);

  const scCountByNation = phase.supplyCenters.reduce<Record<string, number>>((acc, sc) => {
    acc[sc.nation.name] = (acc[sc.nation.name] ?? 0) + 1;
    return acc;
  }, {});

  const drawMemberIds = new Set(result.drawMembers.map(m => m.id));

  const sortedMembers = [...game.members]
    .map(m => ({
      member: m,
      scCount: m.nation ? (scCountByNation[m.nation] ?? 0) : 0,
      isSurvivor: drawMemberIds.has(m.id),
    }))
    .sort((a, b) => b.scCount - a.scCount);

  const showSurvivorSections = result.drawMembers.length > 0;
  const survivors = showSurvivorSections ? sortedMembers.filter(m => m.isSurvivor) : [];
  const eliminated = showSurvivorSections ? sortedMembers.filter(m => !m.isSurvivor) : [];

  const getNationProps = (member: { nation: string | null }) => ({
    color: variant ? findNationColor(variant.nations, member.nation) : null,
    flagUrl: variant ? findNationFlagUrl(variant.nations, member.nation) : null,
  });

  return (
    <>
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/50 to-black/90" />

      <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col gap-4 p-6 max-h-[70vh]">
        <div className="shrink-0">
          <p className="text-white/70 text-xs uppercase tracking-widest font-semibold drop-shadow">
            Game ended
          </p>
          <h2 className="text-4xl font-bold text-white mt-0.5 drop-shadow-lg">{result.title}</h2>
          <p className="text-white/90 text-sm mt-2 leading-relaxed drop-shadow">{result.blurb}</p>
        </div>

        <div className="overflow-y-auto flex-1 min-h-0 bg-black/40 rounded-lg px-3">
          {showSurvivorSections ? (
            <>
              {survivors.length > 0 && (
                <>
                  <p className="text-white/50 text-xs uppercase tracking-wider font-medium pt-2.5 pb-1">
                    Surviving powers
                  </p>
                  <div className="divide-y divide-white/15">
                    {survivors.map(({ member, scCount }) => (
                      <NationRow key={member.id} member={member} scCount={scCount} {...getNationProps(member)} />
                    ))}
                  </div>
                </>
              )}
              {eliminated.length > 0 && (
                <>
                  <p className="text-white/50 text-xs uppercase tracking-wider font-medium pt-2.5 pb-1">
                    Eliminated
                  </p>
                  <div className="divide-y divide-white/15">
                    {eliminated.map(({ member, scCount }) => (
                      <NationRow key={member.id} member={member} scCount={scCount} {...getNationProps(member)} dim />
                    ))}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="divide-y divide-white/15">
              {sortedMembers.map(({ member, scCount }) => (
                <NationRow key={member.id} member={member} scCount={scCount} {...getNationProps(member)} />
              ))}
            </div>
          )}
        </div>

        <DialogPrimitive.Close asChild>
          <Button
            className="w-full border-white/30 bg-white/10 text-white hover:bg-white/20 shrink-0"
            variant="outline"
          >
            OK
          </Button>
        </DialogPrimitive.Close>
      </div>
    </>
  );
};

interface GameEndDialogProps {
  game: GameRetrieve;
  open: boolean;
  onClose: () => void;
}

const GameEndDialog: React.FC<GameEndDialogProps> = ({ game, open, onClose }) => {
  const result = computeResult(game);

  if (!result || game.phases.length === 0) return null;

  return (
    <DialogPrimitive.Root open={open} onOpenChange={isOpen => { if (!isOpen) onClose(); }}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-black/60
            data-[state=open]:animate-in data-[state=closed]:animate-out
            data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
        />
        <DialogPrimitive.Content
          className="fixed z-50 overflow-hidden
            inset-0
            sm:inset-auto sm:top-1/2 sm:left-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2
            sm:w-full sm:max-w-md sm:h-[85vh] sm:rounded-2xl
            data-[state=open]:animate-in data-[state=closed]:animate-out
            data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
            data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
          style={{
            backgroundImage: result.backgroundImage,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          <DialogPrimitive.Title className="sr-only">
            Game ended — {result.title}
          </DialogPrimitive.Title>
          <Suspense
            fallback={
              <div className="absolute inset-0 bg-gradient-to-t from-black/95 to-black/40" />
            }
          >
            <GameEndDialogInner game={game} result={result} />
          </Suspense>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
};

export { GameEndDialog };
