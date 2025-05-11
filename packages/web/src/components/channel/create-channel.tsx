import {
  Stack,
  List,
  ListItem,
  Checkbox,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  ListItemText,
  Button,
} from "@mui/material";
import React from "react";
import { QueryContainer } from "../query-container";
import { useSelectedGameContext } from "../../common";
import { service } from "../../store";
import { useNavigate } from "react-router";

const CreateChannel: React.FC = () => {
  // const query = useListOtherMembersQuery();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  // const [_, createChannelMutation] = useCreateChannelMutation();
  const { gameRetrieveQuery, gameId } = useSelectedGameContext();
  const [createChannel, createChannelMutation] =
    service.endpoints.gameChannelCreate.useMutation();
  // const { selectedMembers, setSelectedMembers } = useCreateChannelContext();
  const [selectedMembers, setSelectedMembers] = React.useState<number[]>([]);
  const navigate = useNavigate();

  const handleToggle = (memberId: number) => {
    setSelectedMembers((prevSelected) =>
      prevSelected.includes(memberId)
        ? prevSelected.filter((id) => id !== memberId)
        : [...prevSelected, memberId]
    );
  };

  const isSubmitting = createChannelMutation.isLoading;

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

  return (
    <QueryContainer query={gameRetrieveQuery}>
      {(game) => (
        <Stack sx={styles.container}>
          <Stack sx={styles.listContainer}>
            <List>
              {game.members
                .filter((m) => !m.user.currentUser)
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
                        {/* <Avatar src={member.flag}>{member.nation[0]}</Avatar> */}
                        <Avatar src={member.user.profile.picture}>
                          {member.nation[0]}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={member.nation}
                        secondary={member.user.username}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
            </List>
            <Button
              variant="contained"
              disabled={selectedMembers.length === 0 || isSubmitting}
              onClick={handleCreateChannel}
            >
              Create Channel
            </Button>
          </Stack>
        </Stack>
      )}
    </QueryContainer>
  );
};

const styles = {
  container: {
    height: "100%",
  },
  listContainer: {
    flexGrow: 1,
  },
};

export { CreateChannel };
