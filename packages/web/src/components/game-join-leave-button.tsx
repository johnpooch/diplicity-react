import React from "react";
import { ListItem, ListItemIcon, ListItemText, MenuItem } from "@mui/material";
import {
  Add as JoinGameIcon,
  Remove as LeaveGameIcon,
} from "@mui/icons-material";
import { QueryContainer } from "./query-container";

const useJoinLeaveButton = (gameId: string) => {
  const query = service.endpoints.getGame.useQuery(gameId);
  const [joinGame, joinGameMutation] = useJoinGameMutation(gameId);
  const [leaveGame, leaveGameMutation] = useLeaveGameMutation(gameId);

  const isSubmitting =
    joinGameMutation.isLoading || leaveGameMutation.isLoading;

  return { joinGame, leaveGame, isSubmitting, query };
};

type JoinLeaveButtonProps = {
  gameId: string;
  onJoinLeave: () => void;
};

const JoinLeaveButton: React.FC<JoinLeaveButtonProps> = (props) => {
  const { joinGame, leaveGame, isSubmitting, query } = useJoinLeaveButton(
    props.gameId
  );

  return (
    <QueryContainer
      query={query}
      onRenderLoading={() => (
        <MenuItem disabled>
          <ListItem disablePadding>
            <ListItemIcon>
              <JoinGameIcon />
            </ListItemIcon>
            <ListItemText primary="Join game" />
          </ListItem>
        </MenuItem>
      )}
    >
      {(data) => (
        <>
          {data.canJoin ? (
            <MenuItem
              onClick={async () => {
                await joinGame();
                props.onJoinLeave();
              }}
              disabled={isSubmitting}
            >
              <ListItem disablePadding>
                <ListItemIcon>
                  <JoinGameIcon />
                </ListItemIcon>
                <ListItemText primary="Join game" />
              </ListItem>
            </MenuItem>
          ) : data.canLeave ? (
            <MenuItem
              onClick={async () => {
                await leaveGame();
                props.onJoinLeave();
              }}
              disabled={isSubmitting}
            >
              <ListItem disablePadding>
                <ListItemIcon>
                  <LeaveGameIcon />
                </ListItemIcon>
                <ListItemText primary="Leave game" />
              </ListItem>
            </MenuItem>
          ) : (
            <MenuItem disabled>
              <ListItem disablePadding>
                <ListItemIcon>
                  <JoinGameIcon />
                </ListItemIcon>
                <ListItemText primary="Join game" />
              </ListItem>
            </MenuItem>
          )}
        </>
      )}
    </QueryContainer>
  );
};

export { JoinLeaveButton };
