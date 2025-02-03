import React from "react";
import { useGameDetailContext } from "../../context";
import { mergeQueries, service } from "../../common";
import {
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Checkbox,
  ListItemButton,
  TextField,
  Stack,
  IconButton,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { QueryContainer } from "../../components/query-container";
import { ScreenTopBar } from "../home/screen-top-bar";
import { useNavigate } from "react-router";

const useCreateChannel = () => {
  const { gameId } = useGameDetailContext();
  const [selectedMembers, setSelectedMembers] = React.useState<string[]>([]);
  const [message, setMessage] = React.useState("");
  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const [createMessage, createMessageMutation] =
    service.endpoints.createMessage.useMutation();

  const query = mergeQueries([getRootQuery, getGameQuery], (user, game) => {
    return {
      userNation: game.Members.find((member) => member.User.Id === user.Id)
        ?.Nation,
      members: game.Members.filter((member) => member.User.Id !== user.Id),
    };
  });

  const handleSubmit = async () => {
    if (!query.data) throw new Error("Data is not available yet");
    if (!query.data.userNation) throw new Error("User nation is not available");
    return createMessage({
      gameId: gameId,
      ChannelMembers: [...selectedMembers, query.data.userNation],
      Body: message,
    });
  };

  const handleToggle = (memberId: string) => {
    setSelectedMembers((prevSelected) =>
      prevSelected.includes(memberId)
        ? prevSelected.filter((id) => id !== memberId)
        : [...prevSelected, memberId]
    );
  };

  const isSubmitting = createMessageMutation.isLoading;

  return {
    query,
    handleSubmit,
    message,
    setMessage,
    selectedMembers,
    handleToggle,
    isSubmitting,
  };
};

const CreateChannel: React.FC = () => {
  const {
    query,
    selectedMembers,
    handleToggle,
    message,
    setMessage,
    isSubmitting,
    handleSubmit,
  } = useCreateChannel();

  const navigate = useNavigate();

  const handleSubmitAndRedirect = async () => {
    const response = await handleSubmit();
    if (response.data) {
      const channelName = response.data.ChannelMembers.join(",");
      navigate(`../channel/${channelName}`);
    }
  };

  return (
    <>
      <ScreenTopBar title="Create Channel" />
      <QueryContainer query={query}>
        {(data) => (
          <Stack
            sx={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              minHeight: "calc(100vh - 113px)",
              paddingBottom: 1,
            }}
          >
            <Stack sx={{ flexGrow: 1 }}>
              <List>
                {data.members.map((member) => (
                  <ListItem
                    key={member.Nation}
                    secondaryAction={
                      <Checkbox
                        edge="end"
                        onChange={() => handleToggle(member.Nation)}
                        checked={selectedMembers.includes(member.Nation)}
                        disableRipple
                        disabled={isSubmitting}
                      />
                    }
                  >
                    <ListItemButton
                      disableRipple
                      onClick={() => handleToggle(member.Nation)}
                    >
                      <ListItemAvatar>
                        <Avatar src={""} />
                      </ListItemAvatar>
                      <ListItemText
                        primary={member.Nation}
                        secondary={member.User.Name}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Stack>

            <Stack sx={{ p: 1, gap: 1 }} direction="row">
              <TextField
                label="Write a message to start the conversation"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                fullWidth
                disabled={isSubmitting}
              />
              <IconButton
                sx={{ width: 56 }}
                disabled={
                  selectedMembers.length === 0 || message === "" || isSubmitting
                }
                onClick={handleSubmitAndRedirect}
              >
                <SendIcon />
              </IconButton>
            </Stack>
          </Stack>
        )}
      </QueryContainer>
    </>
  );
};

export { CreateChannel };
