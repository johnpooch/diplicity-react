import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, LockKeyhole } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScreenContainer } from "@/components/ui/screen-container";
import { GameDetailShell } from "@/components/GameDetailShell";
import { NationFlag } from "@/components/NationFlag";
import { PlayerCard } from "@/components/PlayerCard";
import { janeDoe } from "@/data/fixtures";
import { cn } from "@/lib/utils";

const nations = [
  { name: "Austria" },
  { name: "England", holder: "Wilhelmina" },
  { name: "France" },
  { name: "Germany", holder: "Otto" },
  { name: "Italy" },
  { name: "Russia" },
  { name: "Turkey" },
];

const SingleMember: React.FC<{ state: string }> = ({ state }) => {
  const [selectedNation, setSelectedNation] = useState<string | undefined>(
    state === "assigned" ? "France" : undefined,
  );

  return (
    <GameDetailShell
      title="Assign nation"
      activeNavItem="Players"
      mode="secondary"
      backTo="/member-details/grouped-sections/manager-pending"
      footer={
        <div className="border-t bg-background p-3">
          <Button className="w-full" size="lg" asChild>
            <Link to="/member-details/grouped-sections/manager-pending">
              Save assignment
            </Link>
          </Button>
        </div>
      }
    >
      <ScreenContainer>
        <PlayerCard
          player={{ ...janeDoe, assignedNation: selectedNation }}
          presentation="identity"
          to="/player-profile/stat-grid"
        />

        <p className="text-sm text-muted-foreground">
          Choose a nation for this player. Their ranked preferences remain
          private. If left unassigned, the game will use those preferences when
          it starts.
        </p>

        <Card className="overflow-hidden py-0">
          <CardContent className="flex flex-col divide-y p-0">
            <button
              type="button"
              aria-pressed={selectedNation === undefined}
              onClick={() => setSelectedNation(undefined)}
              className="flex min-h-16 items-center gap-3 p-3 text-left transition-colors hover:bg-accent/50"
            >
              <span className="flex size-8 items-center justify-center rounded-full border border-dashed text-xs text-muted-foreground">
                None
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-semibold">Unassigned</p>
                <p className="text-sm text-muted-foreground">
                  Use the player&apos;s private preferences at game start
                </p>
              </div>
              {selectedNation === undefined && <Check className="size-5" />}
            </button>

            {nations.map((nation) => {
              const selected = selectedNation === nation.name;
              const unavailable = nation.holder !== undefined;
              return (
                <button
                  key={nation.name}
                  type="button"
                  aria-pressed={selected}
                  disabled={unavailable}
                  onClick={() => setSelectedNation(nation.name)}
                  className={cn(
                    "flex min-h-16 items-center gap-3 p-3 text-left transition-colors hover:bg-accent/50 disabled:cursor-not-allowed disabled:opacity-50",
                    selected && "bg-accent/50",
                  )}
                >
                  <NationFlag nation={nation.name} size="md" />
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold">{nation.name}</p>
                    {nation.holder && (
                      <p className="text-sm text-muted-foreground">
                        Assigned to {nation.holder}
                      </p>
                    )}
                  </div>
                  {unavailable ? (
                    <LockKeyhole className="size-4 text-muted-foreground" />
                  ) : selected ? (
                    <Check className="size-5" />
                  ) : null}
                </button>
              );
            })}
          </CardContent>
        </Card>
      </ScreenContainer>
    </GameDetailShell>
  );
};

export { SingleMember };
