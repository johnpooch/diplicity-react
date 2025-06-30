import React from "react";
import { Stack } from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { createUseStyles } from "../utils/styles";
import { service } from "../../store";
import { NotificationBanner } from "../notification-banner";
import { GameCard } from "../game-card";
import { GameCardSkeleton } from "../composites/GameCardSkeleton";
import { QueryContainer } from "../elements/QueryContainer";
import { HomeAppBar } from "../composites/HomeAppBar";
import { Notice } from "../elements/Notice";
import { IconName } from "../elements/Icon";

const useStyles = createUseStyles(() => ({
    header: {
        alignItems: "center",
    },
    image: {
        height: 48,
        width: 48,
    },
    tabs: {
        width: "100%",
    },
}));

const FindGames: React.FC = () => {
    const query = service.endpoints.gamesList.useQuery({ canJoin: true });

    return (
        <HomeLayout
            appBar={<HomeAppBar title="Find Games" />}
            content={
                <Stack>
                    <NotificationBanner />
                    <QueryContainer
                        query={query}
                        pending={() =>
                            Array.from({ length: 10 }, (_, index) => (
                                <GameCardSkeleton key={index} />
                            ))
                        }
                        error={() => <div>Error</div>}
                        fulfilled={(games) => {
                            if (games.length === 0) {
                                return (
                                    <Notice
                                        title="No games found"
                                        message="There are no games available to join. Go to Create Game to start a new game."
                                        icon={IconName.NoResults}
                                    />
                                );
                            }
                            return (
                                <div>
                                    {games.map((game) => (
                                        <GameCard key={game.id} {...game} />
                                    ))}
                                </div>
                            );
                        }}
                    />
                </Stack>
            }
        />
    );
};

export { FindGames };
