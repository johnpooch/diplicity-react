import {
  Stack,
  List,
  ListItem,
  Checkbox,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  ListItemText,
  TextField,
  IconButton,
} from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import React from "react";
import { useNavigate } from "react-router";
import { service, mergeQueries, useGetVariantQuery } from "../../common";
import { useGameDetailContext } from "../../context";
import { QueryContainer } from "../query-container";

type CreateChannelContextType = {
  selectedMembers: string[];
  setSelectedMembers: React.Dispatch<React.SetStateAction<string[]>>;
};

const CreateChannelContext = React.createContext<
  CreateChannelContextType | undefined
>(undefined);

const CreateChannelContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const [selectedMembers, setSelectedMembers] = React.useState<string[]>([]);

  return (
    <CreateChannelContext.Provider
      value={{ selectedMembers, setSelectedMembers }}
    >
      {children}
    </CreateChannelContext.Provider>
  );
};

const useCreateChannel = () => {
  const { gameId } = useGameDetailContext();
  const { selectedMembers, setSelectedMembers } = React.useContext(
    CreateChannelContext
  ) as CreateChannelContextType;
  const [message, setMessage] = React.useState("");
  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const getGameQuery = service.endpoints.getGame.useQuery(gameId);
  const getVariantQuery = useGetVariantQuery(gameId);
  const [createMessage, createMessageMutation] =
    service.endpoints.createMessage.useMutation();

  const query = mergeQueries(
    [getVariantQuery, getRootQuery, getGameQuery],
    (variant, user, game) => {
      return {
        userNation: game.Members.find((member) => member.User.Id === user.Id)
          ?.Nation,
        members: game.Members.filter(
          (member) => member.User.Id !== user.Id
        ).map((member) => {
          return {
            ...member,
            flag: variant.Flags[member.Nation],
          };
        }),
      };
    }
  );

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
  const { query, selectedMembers, handleToggle, isSubmitting } =
    useCreateChannel();

  return (
    <QueryContainer query={query}>
      {(data) => (
        <Stack
          sx={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
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
                      <Avatar src={member.flag}>{member.Nation[0]}</Avatar>
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
        </Stack>
      )}
    </QueryContainer>
  );
};

const CreateChannelTetxField: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();

  const { message, setMessage, handleSubmit, isSubmitting, selectedMembers } =
    useCreateChannel();

  const handleSubmitAndRedirect = async () => {
    const response = await handleSubmit();
    if (response.data) {
      const channelName = response.data.ChannelMembers.join(",");
      navigate(`/game/${gameId}/chat/channel/${channelName}`);
    }
  };

  return (
    <Stack sx={{ gap: 1, width: "100%" }} direction="row">
      <TextField
        label="Type a message"
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
  );
};

export { CreateChannel, CreateChannelTetxField, CreateChannelContextProvider };
