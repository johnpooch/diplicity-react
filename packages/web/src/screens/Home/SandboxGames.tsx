import React, { Suspense } from "react";
import { useNavigate } from "react-router";

import { ScreenHeader } from "@/components/ui/screen-header";
import { ScreenContainer } from "@/components/ui/screen-container";
import { QueryErrorBoundary } from "@/components/QueryErrorBoundary";
import { GameCard } from "@/components/GameCard";
import { Notice } from "@/components/Notice";
import { Blocks } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useGamesListSuspense,
  useVariantsListSuspense,
} from "@/api/generated/endpoints";

const SandboxGames: React.FC = () => {
  const navigate = useNavigate();

  const { data: games } = useGamesListSuspense({ sandbox: true, mine: true });
  const { data: variants } = useVariantsListSuspense();

  const variantMap = new Map(variants.map(v => [v.id, v]));
  const knownGames = games.filter(game => variantMap.has(game.variantId));

  const handleClickCreateSandbox = () => {
    navigate("/create-game?sandbox=true");
  };

  return (
    <div className="space-y-4">
      {knownGames.length > 0 ? (
        knownGames.map(game => (
          <GameCard
            key={game.id}
            game={game}
            variant={variantMap.get(game.variantId)!}
            phaseId={game.phases[0]}
            map={<div />}
          />
        ))
      ) : (
        <Notice
          title="No sandbox games found"
          message="Practice by controlling all nations. No time limits—resolve when ready."
          icon={Blocks}
          actions={
            <Button onClick={handleClickCreateSandbox}>
              Create a sandbox game
            </Button>
          }
        />
      )}
    </div>
  );
};

const SandboxGamesSuspense: React.FC = () => {
  return (
    <ScreenContainer>
      <ScreenHeader title="Sandbox Games" showUserAvatar />
      <QueryErrorBoundary>
        <Suspense fallback={<div></div>}>
          <SandboxGames />
        </Suspense>
      </QueryErrorBoundary>
    </ScreenContainer>
  );
};

export { SandboxGamesSuspense as SandboxGames };
