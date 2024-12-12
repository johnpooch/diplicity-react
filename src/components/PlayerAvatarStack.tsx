import React from "react";
import { Stack, Typography } from "@mui/material";
import PlayerAvatar from "./PlayerAvatar";

interface PlayerAvatarStackProps {
  users: Omit<React.ComponentProps<typeof PlayerAvatar>, "onClick">[];
  maxAvatars?: number;
  onClick: () => void;
}

const PlayerAvatarStack: React.FC<PlayerAvatarStackProps> = ({
  users,
  maxAvatars = 7,
  onClick,
}) => {
  const displayedUsers = users.slice(0, maxAvatars);
  const remainingUsersCount = users.length - displayedUsers.length;

  return (
    <Stack
      direction="row"
      spacing={-1}
      alignItems="center"
      onClick={onClick}
      sx={{ cursor: "pointer" }}
    >
      {displayedUsers.map((user, index) => (
        <PlayerAvatar key={index} username={user.username} />
      ))}
      {remainingUsersCount > 0 && (
        <Typography
          variant="body2"
          sx={{ paddingLeft: 1, alignSelf: "center" }}
        >
          +{remainingUsersCount}
        </Typography>
      )}
    </Stack>
  );
};

export default PlayerAvatarStack;
