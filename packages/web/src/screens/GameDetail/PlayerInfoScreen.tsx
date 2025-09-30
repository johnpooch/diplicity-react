import React from "react";
import {
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    Skeleton,
    Stack,
} from "@mui/material";
import { GameDetailLayout } from "./Layout";
import { GameDetailAppBar } from "./AppBar";
import { useNavigate } from "react-router";
import { MemberAvatar } from "../../components/MemberAvatar";
import { useSelectedGameContext } from "../../context";
import { GameMap, Panel } from "../../components";

const PlayerInfoScreen: React.FC = () => {
    const { gameId, gameRetrieveQuery: query } = useSelectedGameContext();
    const navigate = useNavigate();

    if (query.isError) {
        return <div>Error</div>;
    }

    return (
        <GameDetailLayout
            appBar={
                <GameDetailAppBar
                    title="Player Info"
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
                                {query.data
                                    ? query.data.members.map(member => (
                                        <ListItem key={member.username}>
                                            <ListItemAvatar>
                                                <MemberAvatar member={member} variant={query.data?.variant.id ?? ""} size="medium" />
                                            </ListItemAvatar>
                                            <ListItemText primary={member.username} />
                                        </ListItem>
                                    ))
                                    : Array.from({ length: 3 }, (_, index) => (
                                        <ListItem key={index}>
                                            <ListItemAvatar>
                                                <Skeleton variant="circular" width={40} height={40} />
                                            </ListItemAvatar>
                                            <ListItemText
                                                primary={<Skeleton variant="text" width={150} />}
                                            />
                                        </ListItem>
                                    ))}
                            </List>
                        </Stack>
                    </Panel.Content>
                </Panel >
            }
        />
    );
};

export { PlayerInfoScreen };
