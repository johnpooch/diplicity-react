import React, { useState } from "react";
import {
    Avatar,
    Button,
    Checkbox,
    Divider,
    List,
    ListItem,
    ListItemAvatar,
    ListItemButton,
    ListItemText,
    Stack,
} from "@mui/material";
import { service } from "../../store";
import { GameDetailAppBar } from "./AppBar";
import { GameDetailLayout } from "./Layout";
import { useNavigate } from "react-router";
import { Icon, IconName } from "../../components/Icon";
import { createUseStyles } from "../../components/utils/styles";
import { Panel } from "../../components/Panel";
import { GameMap } from "../../components/GameMap";
import { useSelectedGameContext } from "../../context";


const useStyles = createUseStyles(() => ({
    container: {
        height: "100%",
    },
    listContainer: {
        flexGrow: 1,
    },
}));

const ChannelCreateScreen: React.FC = props => {
    const { gameId, gameRetrieveQuery } = useSelectedGameContext();

    const styles = useStyles(props);
    const navigate = useNavigate();

    const [selectedMembers, setSelectedMembers] = useState<number[]>([]);

    const [createChannel, createChannelMutation] = service.endpoints.gameChannelCreate.useMutation();

    const handleToggle = (memberId: number) => {
        setSelectedMembers((prevSelected) =>
            prevSelected.includes(memberId)
                ? prevSelected.filter((id) => id !== memberId)
                : [...prevSelected, memberId]
        );
    };

    const handleCreateChannel = async () => {
        const response = await createChannel({
            gameId: gameId,
            channelCreateRequest: {
                members: selectedMembers,
            },
        });
        if (response.data) {
            navigate(`/game/${gameId}/chat/channel/${response.data.id}`);
        }
    };

    const handleBack = () => {
        navigate(`/game/${gameId}/chat`);
    }

    if (gameRetrieveQuery.isError || !gameRetrieveQuery.data) {
        return null;
    }

    const game = gameRetrieveQuery.data;
    const isSubmitting = createChannelMutation.isLoading;

    return (
        <GameDetailLayout
            appBar={<GameDetailAppBar
                title={"Create Channel"}
                variant="secondary"
                onNavigateBack={handleBack}
            />}
            rightPanel={<GameMap />}
            content={
                <Panel>
                    <Panel.Content>
                        <Stack sx={styles.container}>
                            <Stack sx={styles.listContainer}>
                                <List>
                                    {game.members
                                        .filter((m) => !m.isCurrentUser)
                                        .map((member) => (
                                            <ListItem
                                                key={member.nation}
                                                secondaryAction={
                                                    <Checkbox
                                                        edge="end"
                                                        onChange={() => handleToggle(member.id)}
                                                        checked={selectedMembers.includes(member.id)}
                                                        disableRipple
                                                        disabled={isSubmitting}
                                                    />
                                                }
                                            >
                                                <ListItemButton
                                                    disableRipple
                                                    onClick={() => handleToggle(member.id)}
                                                >
                                                    <ListItemAvatar>
                                                        <Avatar src={member.picture}>
                                                            {member.nation[0]}
                                                        </Avatar>
                                                    </ListItemAvatar>
                                                    <ListItemText
                                                        primary={member.nation}
                                                        secondary={member.username}
                                                    />
                                                </ListItemButton>
                                            </ListItem>
                                        ))}
                                </List>
                            </Stack>
                        </Stack>
                    </Panel.Content>
                    <Divider />
                    <Panel.Footer>
                        <Button
                            variant="contained"
                            disabled={selectedMembers.length === 0 || isSubmitting}
                            onClick={handleCreateChannel}
                            startIcon={<Icon name={IconName.GroupAdd} />}
                        >
                            Select Members
                        </Button>
                    </Panel.Footer>
                </Panel>
            }
        />
    );
};

export { ChannelCreateScreen };
