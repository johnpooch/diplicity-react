import React from "react";
import { Stack, Link } from "@mui/material";
import { HomeLayout } from "./Layout";
import { service } from "../../store";
import { NotificationBanner } from "../../components/NotificationBanner";
import { GameCard } from "../../components/GameCard";
import { HomeAppBar } from "./AppBar";
import { IconName } from "../../components/Icon";
import { Notice } from "../../components/Notice";
import { useNavigate } from "react-router";

const SandboxGames: React.FC = () => {
  const navigate = useNavigate();

  const query = service.endpoints.gamesList.useQuery({
    sandbox: true,
    mine: true,
  });

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <HomeAppBar
          title="Sandbox Games"
          onNavigateBack={() => navigate("/")}
        />
      }
      content={
        <Stack>
          <NotificationBanner />
          {query.isLoading
            ? Array.from({ length: 3 }, (_, index) => (
                <GameCard key={index} />
              ))
            : query.data
              ? (() => {
                  if (query.data.length === 0) {
                    return (
                      <Notice
                        title="No sandbox games found"
                        message={
                          <>
                            <Link href="/create-game?sandbox=true">
                              Create a sandbox game
                            </Link>
                          </>
                        }
                        icon={IconName.Sandbox}
                      />
                    );
                  }
                  return query.data.map(game => (
                    <GameCard key={game.id} game={game} />
                  ));
                })()
              : null}
        </Stack>
      }
    />
  );
};

export { SandboxGames };
