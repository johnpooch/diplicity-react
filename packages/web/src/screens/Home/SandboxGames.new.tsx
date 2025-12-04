import React from "react";
import { useNavigate } from "react-router";

import { HomeLayout } from "@/components/HomeLayout";
import { Navigation } from "@/components/Navigation";
import { InfoPanel } from "@/components/InfoPanel.new";
import { GameCard } from "@/components/GameCard.new";
import { Notice } from "@/components/Notice.new";
import { IconName } from "@/components/Icon";
import { navigationItems } from "@/navigation/navigationItems";
import { service } from "@/store";
import { Button } from "@/components/ui/button";

interface SandboxGamesProps {
  isLoading: boolean;
  games:
    | Array<{
        id: string;
        name: string;
        private: boolean;
        members: Array<{
          id: number;
          name: string;
          picture: string | null;
          nation: string;
          isCurrentUser: boolean;
        }>;
        canJoin: boolean;
        movementPhaseDuration?: string;
        status: string;
        variant: {
          name: string;
          id: string;
        };
        phase: {
          season: string;
          year: number;
          type: string;
          scheduledResolution: string;
        };
      }>
    | undefined;
  onClickGame: (id: string) => void;
  onClickGameInfo: (id: string) => void;
  onClickPlayerInfo: (id: string) => void;
  onClickJoinGame: (id: string) => void;
  onClickCreateSandbox: () => void;
}

const SandboxGames: React.FC<SandboxGamesProps> = ({
  isLoading,
  games,
  onClickGame,
  onClickGameInfo,
  onClickPlayerInfo,
  onClickJoinGame,
  onClickCreateSandbox,
}) => {
  return (
    <div className="w-full space-y-4">
      <h1 className="text-2xl font-bold">Sandbox Games</h1>
      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }, (_, index) => (
            <GameCard
              key={index}
              game={{
                id: `loading-${index}`,
                name: "",
                private: false,
                members: [],
                canJoin: false,
                movementPhaseDuration: undefined,
              }}
              variant={{ name: "", id: "" }}
              phase={{
                season: "",
                year: 0,
                type: "",
                scheduledResolution: "",
              }}
              map={<div />}
              onClickGame={onClickGame}
              onClickGameInfo={onClickGameInfo}
              onClickPlayerInfo={onClickPlayerInfo}
              onClickJoinGame={onClickJoinGame}
            />
          ))
        ) : games && games.length > 0 ? (
          games.map(game => (
            <GameCard
              key={game.id}
              game={{
                id: game.id,
                name: game.name,
                private: game.private,
                members: game.members,
                canJoin: game.canJoin,
                movementPhaseDuration: game.movementPhaseDuration,
              }}
              variant={game.variant}
              phase={game.phase}
              map={<div />}
              onClickGame={onClickGame}
              onClickGameInfo={onClickGameInfo}
              onClickPlayerInfo={onClickPlayerInfo}
              onClickJoinGame={onClickJoinGame}
            />
          ))
        ) : (
          <Notice
            title="No sandbox games found"
            icon={IconName.Sandbox}
            actions={
              <Button onClick={onClickCreateSandbox}>
                Create a sandbox game
              </Button>
            }
          />
        )}
      </div>
    </div>
  );
};

const SandboxGamesContainer: React.FC = () => {
  const navigate = useNavigate();
  const query = service.endpoints.gamesList.useQuery({
    sandbox: true,
    mine: true,
  });

  const handleClickGame = (id: string) => {
    navigate(`/game/${id}`);
  };

  const handleClickGameInfo = (id: string) => {
    console.log("Game info clicked", id);
  };

  const handleClickPlayerInfo = (id: string) => {
    console.log("Player info clicked", id);
  };

  const handleClickJoinGame = (id: string) => {
    console.log("Join game clicked", id);
  };

  const handleClickCreateSandbox = () => {
    navigate("/create-game?sandbox=true");
  };

  const navItems = navigationItems.map(item => ({
    ...item,
    isActive: item.path === "/sandbox",
  }));

  return (
    <HomeLayout
      left={
        <Navigation
          items={navItems}
          variant="sidebar"
          onItemClick={path => navigate(path)}
        />
      }
      center={
        <SandboxGames
          isLoading={query.isLoading}
          games={query.data}
          onClickGame={handleClickGame}
          onClickGameInfo={handleClickGameInfo}
          onClickPlayerInfo={handleClickPlayerInfo}
          onClickJoinGame={handleClickJoinGame}
          onClickCreateSandbox={handleClickCreateSandbox}
        />
      }
      right={<InfoPanel />}
      bottom={
        <Navigation
          items={navItems}
          variant="bottom"
          onItemClick={path => navigate(path)}
        />
      }
    />
  );
};

export { SandboxGames, SandboxGamesContainer };
export type { SandboxGamesProps };
