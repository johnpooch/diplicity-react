import React from "react";
import {
    AvatarGroup,
    Button,
    Divider,
    List,
    ListSubheader,
    Skeleton,
    Stack,
} from "@mui/material";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { IconName } from "../../components/Icon";
import { useNavigate } from "react-router";
import { Table } from "../../components/Table";
import { PlayerAvatar } from "../../components/PlayerAvatar";
import { useSelectedGameContext } from "../../context";
import { GameMap, Panel } from "../../components";

const GameInfoScreen: React.FC = () => {
    const { gameId, gameRetrieveQuery: query } = useSelectedGameContext();
    const navigate = useNavigate();

    const handlePlayerInfo = () => {
        navigate(`/game/${gameId}/player-info`);
    };

    if (query.isError) {
        return <div>Error</div>;
    }

    return (
        <GameDetailLayout
            appBar={
                <GameDetailAppBar
                    title="Game Info"
                    onNavigateBack={() => navigate(`/game/${gameId}`)}
                    variant="secondary"
                />
            }
            bottomNavigation={<div></div>}
            rightPanel={<GameMap />}
            content={
                <Panel>
                    <Panel.Content>
                        <Stack>
                            <List>
                                <ListSubheader>Game settings</ListSubheader>
                                <Table
                                    rows={[
                                        {
                                            label: "Variant",
                                            value: query.data ? (
                                                query.data.variant.name
                                            ) : (
                                                <Stack alignItems="flex-end">
                                                    <Skeleton variant="text" width={100} />
                                                </Stack>
                                            ),
                                            icon: IconName.WinCondition,
                                        },
                                        {
                                            label: "Phase deadlines",
                                            value: query.data ? (
                                                query.data.movementPhaseDuration
                                            ) : (
                                                <Stack alignItems="flex-end">
                                                    <Skeleton variant="text" width={100} />
                                                </Stack>
                                            ),
                                            icon: IconName.StartYear,
                                        },
                                    ]}
                                />
                                <Divider />
                                <ListSubheader>Player settings</ListSubheader>
                                <Table
                                    rows={[
                                        {
                                            label: "Players",
                                            value: query.data ? (
                                                <Button onClick={handlePlayerInfo}>
                                                    <AvatarGroup total={query.data?.members.length} max={7}>
                                                        {query.data?.members.map(member => (
                                                            <PlayerAvatar member={member} variant={query.data?.variant.id ?? ""}
                                                                key={member.username}
                                                                size="small"
                                                            />
                                                        ))}
                                                    </AvatarGroup>
                                                </Button>
                                            ) : (
                                                <Skeleton variant="rectangular" width={100} height={40} />
                                            ),
                                            icon: IconName.Players,
                                        },
                                    ]}
                                />
                                <Divider />
                                <ListSubheader>Variant details</ListSubheader>
                                <Table
                                    rows={[
                                        {
                                            label: "Number of nations",
                                            value: query.data ? (
                                                query.data.variant.nations.length.toString()
                                            ) : (
                                                <Skeleton variant="text" width={10} />
                                            ),
                                            icon: IconName.Players,
                                        },
                                        {
                                            label: "Start year",
                                            value: query.data ? (
                                                query.data.variant.templatePhase.year?.toString()
                                            ) : (
                                                <Skeleton variant="text" width={50} />
                                            ),
                                            icon: IconName.StartYear,
                                        },
                                        {
                                            label: "Original author",
                                            value: query.data ? (
                                                query.data.variant.author
                                            ) : (
                                                <Skeleton variant="text" width={100} />
                                            ),
                                            icon: IconName.Author,
                                        },
                                    ]}
                                />
                            </List>
                        </Stack>
                    </Panel.Content>
                </Panel >
            }
        />
    );
};

export { GameInfoScreen };
