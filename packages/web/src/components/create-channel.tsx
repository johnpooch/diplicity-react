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
  Divider,
} from "@mui/material";
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import React from "react";
import { QueryContainer } from "./query-container";
import { service } from "../store";
import { useNavigate } from "react-router";
import { useSelectedGameContext } from "../context";
import { Panel } from "./panel";

const CreateChannel: React.FC = () => {
  const { gameRetrieveQuery, gameId } = useSelectedGameContext();
  const [createChannel, createChannelMutation] =
    service.endpoints.gameChannelCreate.useMutation();
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
              startIcon={<GroupAddIcon />}
            >
              Select Members
            </Button>
          </Panel.Footer>
        </Panel>
      )
      }
    </QueryContainer >
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
