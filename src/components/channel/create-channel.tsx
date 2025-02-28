import {
  Stack,
  List,
  ListItem,
  Checkbox,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  ListItemText,
} from "@mui/material";
import React from "react";
import { QueryContainer } from "../query-container";
import { useListOtherMembersQuery } from "../../common/hooks/use-list-other-members-query";
import { useCreateChannelMutation } from "../../common/hooks/use-create-channel-mutation";
import { useCreateChannelContext } from "../../common/context/create-channel-context";

const CreateChannel: React.FC = () => {
  const query = useListOtherMembersQuery();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_, createChannelMutation] = useCreateChannelMutation();
  const { selectedMembers, setSelectedMembers } = useCreateChannelContext();

  const handleToggle = (memberId: string) => {
    setSelectedMembers((prevSelected) =>
      prevSelected.includes(memberId)
        ? prevSelected.filter((id) => id !== memberId)
        : [...prevSelected, memberId]
    );
  };

  const isSubmitting = createChannelMutation.isLoading;

  return (
    <QueryContainer query={query}>
      {(data) => (
        <Stack sx={styles.container}>
          <Stack sx={styles.listContainer}>
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

const styles = {
  container: {
    height: "100%",
  },
  listContainer: {
    flexGrow: 1,
  },
};

export { CreateChannel };
