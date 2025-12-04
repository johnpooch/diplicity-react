import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HomeLayout } from "@/components/HomeLayout";
import { Navigation } from "@/components/Navigation";
import { InfoPanel } from "@/components/InfoPanel.new";
import { GameCard } from "@/components/GameCard.new";
import { Notice } from "@/components/Notice";
import { IconName } from "@/components/Icon";
import { navigationItems } from "@/navigation/navigationItems";
import { service } from "@/store";

const statuses = [
  { value: "pending", label: "Staging" },
  { value: "active", label: "Started" },
  { value: "completed", label: "Finished" },
] as const;

type Status = (typeof statuses)[number]["value"];

const statusPriority: readonly Status[] = ["active", "pending", "completed"];

const getStatusMessage = (status: Status) => {
  switch (status) {
    case "pending":
      return "You are not a member of any staging games. Go to Find Games to join a game.";
    case "active":
      return "You are not a member of any started games. When you join a game, it will be in a pending state until the required number of players have joined.";
    case "completed":
      return "You have not finished any games. When a game is finished, it will appear here.";
  }
};

interface MyGamesProps {
  selectedStatus: Status;
  onStatusChange: (status: Status) => void;
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
}

const MyGames: React.FC<MyGamesProps> = ({
  selectedStatus,
  onStatusChange,
  isLoading,
  games,
  onClickGame,
  onClickGameInfo,
  onClickPlayerInfo,
  onClickJoinGame,
}) => {
  const filteredGames = games?.filter(game => game.status === selectedStatus);

  return (
    <div className="w-full space-y-4">
      <h1 className="text-2xl font-bold">My Games</h1>
      <div className="flex flex-col items-center gap-4">
        <Tabs
          value={selectedStatus}
          onValueChange={value => onStatusChange(value as Status)}
          className="w-full"
        >
          <TabsList className="w-full">
            {statuses.map(status => (
              <TabsTrigger
                key={status.value}
                value={status.value}
                className="flex-1"
              >
                {status.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {statuses.map(status => (
            <TabsContent key={status.value} value={status.value}>
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
                ) : filteredGames && filteredGames.length > 0 ? (
                  filteredGames.map(game => (
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
                    title={`No ${status.label.toLowerCase()} games`}
                    message={getStatusMessage(status.value)}
                    icon={IconName.Empty}
                  />
                )}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
};

const MyGamesContainer: React.FC = () => {
  const navigate = useNavigate();
  const [selectedStatus, setSelectedStatus] = useState<Status>("active");

  const query = service.endpoints.gamesList.useQuery({ mine: true });

  useEffect(() => {
    if (query.data) {
      const firstStatusWithGames = statusPriority.find(status =>
        query.data!.some(game => game.status === status)
      );
      if (firstStatusWithGames) {
        setSelectedStatus(firstStatusWithGames);
      }
    }
  }, [query.data]);

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

  const navItems = navigationItems.map(item => ({
    ...item,
    isActive: item.path === "/",
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
        <MyGames
          selectedStatus={selectedStatus}
          onStatusChange={setSelectedStatus}
          isLoading={query.isLoading}
          games={query.data}
          onClickGame={handleClickGame}
          onClickGameInfo={handleClickGameInfo}
          onClickPlayerInfo={handleClickPlayerInfo}
          onClickJoinGame={handleClickJoinGame}
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

export { MyGames, MyGamesContainer };
export type { MyGamesProps };
