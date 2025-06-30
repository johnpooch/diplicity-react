import React, { useEffect } from "react";
import { Stack } from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { createUseStyles } from "../utils/styles";
import { useState } from "react";
import { Tabs } from "../elements/Tabs";
import { DiplicityLogo } from "../elements/DiplicityLogo";
import { service } from "../../store";
import { NotificationBanner } from "../notification-banner";
import { GameCard } from "../game-card";
import { GameCardSkeleton } from "../composites/GameCardSkeleton";
import { QueryContainer } from "../elements/QueryContainer";
import { Notice } from "../elements/Notice";
import { IconName } from "../elements/Icon";

const useStyles = createUseStyles(() => ({
    header: {
        paddingTop: 1,
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

const statuses = [
    { value: "pending", label: "Staging" },
    { value: "active", label: "Started" },
    { value: "completed", label: "Finished" },
];

const getStatusMessage = (status: Status) => {
    switch (status) {
        case "pending":
            return "You are not a member of any staging games. Go to Find Games to join a game.";
        case "active":
            return "You are not a member of any started games. When you join a game, it will be in a pending state until the required number of players have joined.";
        case "completed":
            return "You have not finished any games. When a game is finished, it will appear here.";
    }
}

// Priority order for which status to select if there are games in that status
const statusPriority = ["active", "pending", "completed"] as const;

type Status = (typeof statuses)[number]["value"];

const MyGames: React.FC = (props) => {
    const styles = useStyles(props);
    const [selectedStatus, setSelectedStatus] = useState<Status>("active");

    const query = service.endpoints.gamesList.useQuery({ mine: true });

    useEffect(() => {
        if (query.data) {
            const firstStatusWithGames = statusPriority.find((status) =>
                query.data!.some((game) => game.status === status)
            );
            if (firstStatusWithGames) {
                setSelectedStatus(firstStatusWithGames);
            }
        }
    }, [query.data]);

    return (
        <HomeLayout
            appBar={
                <Stack sx={styles.header}>
                    <DiplicityLogo />
                    <Tabs
                        value={selectedStatus}
                        onChange={(_, value) => setSelectedStatus(value)}
                        options={statuses}
                    />
                </Stack>
            }
            content={
                <Stack>
                    <NotificationBanner />
                    <QueryContainer
                        query={query}
                        pending={() => Array.from({ length: 10 }, (_, index) => <GameCardSkeleton key={index} />)}
                        error={() => <div>Error</div>}
                        fulfilled={(games) => {
                            const filteredGames = games.filter((game) => game.status === selectedStatus);
                            if (filteredGames.length === 0) {
                                return <Notice title={`No ${selectedStatus.toLowerCase()} games`} message={getStatusMessage(selectedStatus)} icon={IconName.Empty} />;
                            }
                            return filteredGames.map((game) => (
                                <GameCard key={game.id} {...game} />
                            ));
                        }}
                    />
                </Stack>
            }
        />
    );
};

export { MyGames };
